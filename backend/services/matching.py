"""AI matching service for finding suitable professors using OpenAI embeddings."""
import os
from typing import List, Dict
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from database.professors import ProfessorDatabase

class MatchingService:
    """Service for matching student reports with professor profiles using OpenAI."""
    
    def __init__(self):
        """Initialize matching service with OpenAI embeddings."""
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment variables."
            )
        
        # Initialize OpenAI client
        # Fix for httpx compatibility issue
        import httpx
        try:
            # Try with explicit http_client to avoid proxies issue
            http_client = httpx.Client(timeout=60.0)
            self.client = OpenAI(api_key=api_key, http_client=http_client)
        except Exception:
            # Fallback to default initialization
            self.client = OpenAI(api_key=api_key)
        
        # Use text-embedding-3-small or text-embedding-ada-002
        # text-embedding-3-small is newer and better, cheaper than ada-002
        self.embedding_model = os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small"  # or "text-embedding-ada-002"
        )
        
        # Chat model for analysis generation (default: gpt-4o-mini)
        self.chat_model = os.getenv(
            "OPENAI_CHAT_MODEL",
            "gpt-4o-mini"
        )
        
        self.professor_db = ProfessorDatabase()  # Keep for backward compatibility
        self._professor_embeddings = None
        self._professor_data = None
        # Load embeddings will be done async now
        self._professor_embeddings_loaded = False
    
    async def _load_professor_embeddings_async(self):
        """Load professor profiles from MongoDB and compute embeddings."""
        try:
            from database.professor_profile_repository import ProfessorProfileRepository
            profile_repo = ProfessorProfileRepository()
            
            # Get only complete profiles
            profiles = await profile_repo.get_all_complete_profiles()
            
            if not profiles:
                print("No complete professor profiles found in MongoDB")
                # Fallback to JSON file if no MongoDB profiles
                profiles = self.professor_db.get_all_professors()
            
            if not profiles:
                self._professor_embeddings = np.array([])
                self._professor_data = []
                self._professor_embeddings_loaded = True
                return
            
            # Create combined text for each professor
            professor_texts = []
            self._professor_data = []
            
            for prof in profiles:
                # Use profile_text if available, otherwise generate
                if prof.get("profile_text"):
                    text = prof["profile_text"]
                else:
                    text_parts = [
                        prof.get("name", ""),
                        prof.get("title", ""),
                        prof.get("department", ""),
                        prof.get("bio", ""),
                        ", ".join(prof.get("research_interests", [])),
                        ", ".join(prof.get("expertise_areas", [])),
                        prof.get("education", ""),
                        prof.get("publications", ""),
                    ]
                    text = " ".join([part for part in text_parts if part])
                
                professor_texts.append(text)
                self._professor_data.append(prof)
            
            # Compute embeddings using OpenAI
            if professor_texts:
                self._professor_embeddings = self._get_embeddings(professor_texts)
                print(f"Loaded embeddings for {len(profiles)} professor profiles")
            else:
                self._professor_embeddings = np.array([])
                self._professor_data = []
            
            self._professor_embeddings_loaded = True
        except Exception as e:
            print(f"Error loading professor profiles from MongoDB: {e}")
            # Fallback to JSON file
            self._load_professor_embeddings()
            self._professor_embeddings_loaded = True
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Get embeddings from OpenAI API.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            numpy array of embeddings
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)
        except Exception as e:
            raise Exception(f"Error getting embeddings from OpenAI: {str(e)}")
    
    def _load_professor_embeddings(self):
        """Pre-compute embeddings for all professors."""
        professors = self.professor_db.get_all_professors()
        
        if not professors:
            self._professor_embeddings = np.array([])
            self._professor_data = []
            return
        
        # Create combined text for each professor (name + expertise + research)
        professor_texts = []
        self._professor_data = []
        
        for prof in professors:
            text_parts = [
                prof.get("name", ""),
                prof.get("expertise", ""),
                prof.get("research_interests", ""),
                prof.get("description", ""),
                " ".join(prof.get("keywords", []))
            ]
            combined_text = " ".join([part for part in text_parts if part])
            professor_texts.append(combined_text)
            self._professor_data.append(prof)
        
        # Compute embeddings using OpenAI
        try:
            self._professor_embeddings = self._get_embeddings(professor_texts)
            print(f"Loaded embeddings for {len(professors)} professors")
        except Exception as e:
            print(f"Error loading professor embeddings: {e}")
            self._professor_embeddings = np.array([])
            self._professor_data = []
    
    async def _generate_analysis(
        self,
        report_text: str,
        professor: Dict,
        similarity_score: float
    ) -> str:
        """
        Generate analysis explaining why professor is a good match.
        
        Args:
            report_text: Student report text
            professor: Professor profile
            similarity_score: Similarity score (0-1)
        
        Returns:
            Analysis text in Vietnamese
        """
        try:
            # Prepare professor information (support both MongoDB profile and JSON format)
            if isinstance(professor.get('research_interests'), list) or isinstance(professor.get('expertise_areas'), list):
                # MongoDB profile format
                prof_info = f"""
Tên: {professor.get('name', 'N/A')}
Chức danh: {professor.get('title', 'N/A')}
Khoa: {professor.get('department', 'N/A')}
Chuyên môn: {', '.join(professor.get('expertise_areas', []))}
Lĩnh vực nghiên cứu: {', '.join(professor.get('research_interests', []))}
Tiểu sử: {professor.get('bio', 'N/A')}
Học vấn: {professor.get('education', 'N/A')}
Công trình nghiên cứu: {professor.get('publications', 'N/A')}
"""
            else:
                # JSON file format (backward compatibility)
                prof_info = f"""
Tên: {professor.get('name', 'N/A')}
Chức danh: {professor.get('title', 'N/A')}
Khoa: {professor.get('department', 'N/A')}
Chuyên môn: {professor.get('expertise', 'N/A')}
Lĩnh vực nghiên cứu: {professor.get('research_interests', 'N/A')}
Mô tả: {professor.get('description', 'N/A')}
Từ khóa: {', '.join(professor.get('keywords', []))}
"""
            
            # Truncate report text if too long (keep first 2000 chars)
            report_preview = report_text[:2000] + "..." if len(report_text) > 2000 else report_text
            
            prompt = f"""Bạn là một trợ lý AI chuyên phân tích và đánh giá sự phù hợp giữa bài báo cáo của học sinh và profile của giảng viên.

Hãy phân tích tại sao giảng viên này phù hợp với bài báo cáo của học sinh. Phân tích cần:
1. Ngắn gọn, rõ ràng (khoảng 3-5 câu)
2. Chỉ ra các điểm tương đồng cụ thể giữa nội dung báo cáo và chuyên môn của giảng viên
3. Giải thích tại sao giảng viên này có thể hỗ trợ tốt cho học sinh
4. Viết bằng tiếng Việt, thân thiện và dễ hiểu

Thông tin giảng viên:
{prof_info}

Nội dung bài báo cáo (trích đoạn):
{report_preview}

Điểm khớp: {similarity_score:.2%}

Hãy đưa ra phân tích ngắn gọn:"""

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là một trợ lý AI chuyên phân tích và đánh giá sự phù hợp giữa bài báo cáo và profile giảng viên. Hãy đưa ra phân tích ngắn gọn, rõ ràng bằng tiếng Việt."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            analysis = response.choices[0].message.content.strip()
            return analysis
            
        except Exception as e:
            print(f"Error generating analysis: {e}")
            # Fallback analysis
            return f"Giảng viên này phù hợp với bài báo cáo của bạn với điểm khớp {similarity_score:.1%}. Chuyên môn và lĩnh vực nghiên cứu của giảng viên có nhiều điểm tương đồng với nội dung bạn đang nghiên cứu."
    
    async def find_matches(
        self,
        text: str,
        top_k: int = 5,
        include_analysis: bool = True
    ) -> List[Dict]:
        """
        Find matching professors for given text.
        
        Args:
            text: Student report text
            top_k: Number of top matches to return
            include_analysis: Whether to include AI-generated analysis
        
        Returns:
            List of matching professors with similarity scores and analysis
        """
        if not text or len(text.strip()) < 10:
            return []
        
        # Check if professor embeddings are loaded
        if self._professor_embeddings is None or not self._professor_embeddings_loaded:
            print("Warning: Professor embeddings not loaded. Loading now...")
            await self._load_professor_embeddings_async()
        
        if self._professor_embeddings is None:
            print("Warning: Failed to load professor embeddings")
            return []
        
        # Check if embeddings array is empty
        if hasattr(self._professor_embeddings, 'size') and self._professor_embeddings.size == 0:
            print("Warning: No professor embeddings available (empty array)")
            return []
        
        if len(self._professor_data) == 0:
            print("Warning: No professor data available")
            return []
        
        # Compute embedding for input text using OpenAI
        try:
            query_embedding = self._get_embeddings([text])
        except Exception as e:
            print(f"Error getting query embedding: {e}")
            return []
        
        # Calculate cosine similarity
        similarities = cosine_similarity(
            query_embedding,
            self._professor_embeddings
        )[0]
        
        # Get top k matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        matches = []
        for idx in top_indices:
            professor = self._professor_data[idx].copy()
            similarity = float(similarities[idx])
            professor["similarity_score"] = similarity
            professor["match_percentage"] = round(similarity * 100, 2)
            
            # Generate analysis if requested
            if include_analysis:
                try:
                    analysis = await self._generate_analysis(
                        report_text=text,
                        professor=professor,
                        similarity_score=similarity
                    )
                    professor["analysis"] = analysis
                except Exception as e:
                    print(f"Error generating analysis for {professor.get('name')}: {e}")
                    professor["analysis"] = None
            else:
                professor["analysis"] = None
            
            matches.append(professor)
        
        return matches
    
    def reload_professors(self):
        """Reload professor data and recompute embeddings."""
        self._load_professor_embeddings()

