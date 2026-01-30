"""Database for professor profiles."""
import json
import os
from typing import List, Dict
from pathlib import Path


class ProfessorDatabase:
    """Database interface for professor profiles."""
    
    def __init__(self, data_file: str = None):
        """Initialize professor database."""
        # Check if running in serverless environment (Vercel/Lambda)
        is_serverless = os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT")
        
        if data_file is None:
            if is_serverless:
                # In serverless, don't try to use file path
                data_file = None
            else:
                # Default to data/professors.json for local development
                base_dir = Path(__file__).parent.parent.parent
                data_file = os.path.join(base_dir, "data", "professors.json")
        
        self.data_file = data_file
        self._professors = []
        self._load_professors()
    
    def _load_professors(self):
        """Load professors from JSON file."""
        # Check if running in serverless environment
        is_serverless = os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT")
        
        # In serverless, always use default professors
        if is_serverless or self.data_file is None:
            self._professors = self._get_default_professors()
            print("Using default professors (serverless environment)")
            return
        
        # Try to load from file for local development
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self._professors = json.load(f)
            else:
                # File not found, use defaults
                self._professors = self._get_default_professors()
                print(f"Using default professors (file not found: {self.data_file})")
        except (OSError, IOError, PermissionError) as e:
            # Read-only filesystem or permission error - use defaults
            print(f"Error loading professors (read-only filesystem?): {e}")
            self._professors = self._get_default_professors()
        except Exception as e:
            print(f"Error loading professors: {e}")
            self._professors = self._get_default_professors()
    
    def _save_professors(self):
        """Save professors to JSON file."""
        try:
            # Skip saving in serverless environment (read-only filesystem)
            if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
                print("Skipping save professors (serverless environment)")
                return
            
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._professors, f, ensure_ascii=False, indent=2)
        except (OSError, IOError, PermissionError):
            # Ignore write errors in read-only environments
            print("Cannot save professors (read-only filesystem)")
    
    def get_all_professors(self) -> List[Dict]:
        """Get all professors."""
        return self._professors
    
    def get_professor_by_id(self, professor_id: str) -> Dict:
        """Get professor by ID."""
        for prof in self._professors:
            if prof.get("id") == professor_id:
                return prof
        return None
    
    def add_professor(self, professor: Dict):
        """Add a new professor."""
        if "id" not in professor:
            professor["id"] = f"prof_{len(self._professors) + 1}"
        self._professors.append(professor)
        self._save_professors()
    
    def _get_default_professors(self) -> List[Dict]:
        """Get default professor data for testing."""
        return [
            {
                "id": "prof_1",
                "name": "TS. Nguyễn Văn A",
                "title": "Phó Giáo sư",
                "department": "Khoa Công nghệ Thông tin",
                "expertise": "Trí tuệ nhân tạo, Machine Learning, Deep Learning",
                "research_interests": "Xử lý ngôn ngữ tự nhiên, Computer Vision, Hệ thống khuyến nghị",
                "description": "Chuyên gia về AI và Machine Learning với hơn 15 năm kinh nghiệm. Nghiên cứu về NLP và Computer Vision.",
                "keywords": ["AI", "Machine Learning", "NLP", "Computer Vision", "Deep Learning"],
                "email": "nguyenvana@university.edu.vn",
                "publications": 45
            },
            {
                "id": "prof_2",
                "name": "TS. Trần Thị B",
                "title": "Giảng viên chính",
                "department": "Khoa Kinh tế",
                "expertise": "Kinh tế học ứng dụng, Phân tích dữ liệu kinh tế",
                "research_interests": "Kinh tế lượng, Phân tích chính sách, Kinh tế phát triển",
                "description": "Chuyên gia về kinh tế học ứng dụng và phân tích dữ liệu. Nghiên cứu về chính sách kinh tế và phát triển.",
                "keywords": ["Kinh tế", "Phân tích dữ liệu", "Kinh tế lượng", "Chính sách"],
                "email": "tranthib@university.edu.vn",
                "publications": 32
            },
            {
                "id": "prof_3",
                "name": "TS. Lê Văn C",
                "title": "Phó Giáo sư",
                "department": "Khoa Sinh học",
                "expertise": "Sinh học phân tử, Di truyền học, Công nghệ sinh học",
                "research_interests": "Genomics, Proteomics, Sinh học tính toán",
                "description": "Chuyên gia về sinh học phân tử và di truyền học. Nghiên cứu về genomics và công nghệ sinh học.",
                "keywords": ["Sinh học", "Di truyền", "Genomics", "Công nghệ sinh học"],
                "email": "levanc@university.edu.vn",
                "publications": 38
            },
            {
                "id": "prof_4",
                "name": "TS. Phạm Thị D",
                "title": "Giảng viên",
                "department": "Khoa Văn học",
                "expertise": "Văn học Việt Nam, Văn học so sánh, Phê bình văn học",
                "research_interests": "Văn học đương đại, Văn học dân gian, Văn học và văn hóa",
                "description": "Chuyên gia về văn học Việt Nam và văn học so sánh. Nghiên cứu về văn học đương đại và văn hóa.",
                "keywords": ["Văn học", "Văn học Việt Nam", "Phê bình", "Văn hóa"],
                "email": "phamthid@university.edu.vn",
                "publications": 28
            },
            {
                "id": "prof_5",
                "name": "TS. Hoàng Văn E",
                "title": "Phó Giáo sư",
                "department": "Khoa Toán học",
                "expertise": "Toán ứng dụng, Thống kê, Phân tích số liệu",
                "research_interests": "Toán tối ưu, Thống kê Bayes, Phân tích dữ liệu lớn",
                "description": "Chuyên gia về toán ứng dụng và thống kê. Nghiên cứu về toán tối ưu và phân tích dữ liệu.",
                "keywords": ["Toán học", "Thống kê", "Tối ưu", "Phân tích dữ liệu"],
                "email": "hoangvane@university.edu.vn",
                "publications": 42
            },
            {
                "id": "prof_6",
                "name": "TS. Võ Thị F",
                "title": "Giảng viên chính",
                "department": "Khoa Hóa học",
                "expertise": "Hóa học hữu cơ, Hóa học vật liệu, Hóa học tính toán",
                "research_interests": "Vật liệu nano, Hóa học xanh, Phát triển thuốc",
                "description": "Chuyên gia về hóa học hữu cơ và vật liệu. Nghiên cứu về vật liệu nano và hóa học xanh.",
                "keywords": ["Hóa học", "Vật liệu", "Nano", "Hóa học xanh"],
                "email": "vothif@university.edu.vn",
                "publications": 35
            }
        ]

