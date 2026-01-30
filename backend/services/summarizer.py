"""AI service for document summarization."""
import os
from openai import OpenAI
from typing import Optional


class DocumentSummarizer:
    """Service for summarizing documents using OpenAI."""
    
    def __init__(self):
        """Initialize summarizer."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    
    async def summarize_document(
        self,
        text: str,
        max_length: int = 500
    ) -> str:
        """
        Summarize a document using AI.
        
        Args:
            text: Document text to summarize
            max_length: Maximum length of summary
        
        Returns:
            Summary string
        """
        if not text or len(text.strip()) < 50:
            return "Tài liệu quá ngắn để tóm tắt."
        
        try:
            # Truncate text if too long (to save tokens)
            if len(text) > 8000:
                text = text[:8000] + "..."
            
            prompt = f"""Hãy tóm tắt bài báo cáo sau đây một cách ngắn gọn và súc tích (tối đa {max_length} từ):

{text}

Tóm tắt bằng tiếng Việt, tập trung vào:
1. Chủ đề/nội dung chính
2. Mục tiêu nghiên cứu
3. Phương pháp tiếp cận (nếu có)
4. Kết quả/kết luận chính (nếu có)

Tóm tắt:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý chuyên tóm tắt các bài báo cáo học thuật."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=max_length
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
        
        except Exception as e:
            print(f"Error summarizing document: {e}")
            return f"Không thể tóm tắt tài liệu: {str(e)}"

