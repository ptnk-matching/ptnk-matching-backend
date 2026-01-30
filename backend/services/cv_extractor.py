"""CV extraction service using AI."""
import os
from openai import OpenAI
from services.document_processor import DocumentProcessor
from typing import Dict, Optional


class CVExtractor:
    """Service for extracting structured information from CV using AI."""
    
    def __init__(self):
        """Initialize CV extractor."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.doc_processor = DocumentProcessor()
    
    async def extract_from_cv(
        self,
        cv_text: str,
        existing_profile: Optional[Dict] = None
    ) -> Dict:
        """
        Extract structured information from CV text using AI.
        
        Args:
            cv_text: Extracted text from CV PDF
            existing_profile: Existing profile data to merge with
        
        Returns:
            Dictionary with extracted fields
        """
        if not cv_text or len(cv_text.strip()) < 50:
            return {}
        
        try:
            # Truncate if too long
            if len(cv_text) > 8000:
                cv_text = cv_text[:8000] + "..."
            
            existing_info = ""
            if existing_profile:
                existing_info = f"""
Thông tin hiện tại:
- Tên: {existing_profile.get('name', '')}
- Chức danh: {existing_profile.get('title', '')}
- Khoa: {existing_profile.get('department', '')}
- Lĩnh vực nghiên cứu: {', '.join(existing_profile.get('research_interests', []))}
- Chuyên môn: {', '.join(existing_profile.get('expertise_areas', []))}
"""
            
            prompt = f"""Bạn là một trợ lý AI chuyên trích xuất thông tin từ CV của giảng viên.

Hãy phân tích CV sau đây và trích xuất các thông tin sau (nếu có):
1. Tên đầy đủ
2. Chức danh (Giáo sư, Phó Giáo sư, Tiến sĩ, Thạc sĩ, v.v.)
3. Khoa/Bộ môn
4. Lĩnh vực nghiên cứu (danh sách, mỗi lĩnh vực một dòng)
5. Chuyên môn (danh sách, mỗi chuyên môn một dòng)
6. Học vấn (bằng cấp, trường, năm)
7. Công trình nghiên cứu/Publications (danh sách các công trình quan trọng)
8. Tiểu sử ngắn (2-3 câu tóm tắt)

{existing_info}

CV:
{cv_text}

Hãy trả về kết quả dưới dạng JSON với các key sau:
{{
  "name": "Tên đầy đủ",
  "title": "Chức danh",
  "department": "Khoa/Bộ môn",
  "research_interests": ["Lĩnh vực 1", "Lĩnh vực 2"],
  "expertise_areas": ["Chuyên môn 1", "Chuyên môn 2"],
  "education": "Học vấn",
  "publications": "Công trình nghiên cứu",
  "bio": "Tiểu sử ngắn"
}}

Chỉ trả về JSON, không thêm text khác."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là một trợ lý AI chuyên trích xuất thông tin từ CV. Trả về kết quả dưới dạng JSON chính xác."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                extracted = json.loads(result_text)
                
                # Clean and format the data
                cleaned = {}
                if extracted.get("name"):
                    cleaned["name"] = extracted["name"].strip()
                if extracted.get("title"):
                    cleaned["title"] = extracted["title"].strip()
                if extracted.get("department"):
                    cleaned["department"] = extracted["department"].strip()
                if extracted.get("research_interests"):
                    if isinstance(extracted["research_interests"], list):
                        cleaned["research_interests"] = [r.strip() for r in extracted["research_interests"] if r.strip()]
                    elif isinstance(extracted["research_interests"], str):
                        # Try to split by comma or newline
                        cleaned["research_interests"] = [r.strip() for r in extracted["research_interests"].replace('\n', ',').split(',') if r.strip()]
                if extracted.get("expertise_areas"):
                    if isinstance(extracted["expertise_areas"], list):
                        cleaned["expertise_areas"] = [e.strip() for e in extracted["expertise_areas"] if e.strip()]
                    elif isinstance(extracted["expertise_areas"], str):
                        cleaned["expertise_areas"] = [e.strip() for e in extracted["expertise_areas"].replace('\n', ',').split(',') if e.strip()]
                if extracted.get("education"):
                    cleaned["education"] = extracted["education"].strip()
                if extracted.get("publications"):
                    cleaned["publications"] = extracted["publications"].strip()
                if extracted.get("bio"):
                    cleaned["bio"] = extracted["bio"].strip()
                
                return cleaned
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON from AI response: {result_text}")
                return {}
        
        except Exception as e:
            print(f"Error extracting CV information: {e}")
            return {}

