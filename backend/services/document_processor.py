"""Document processing service for extracting text from various file formats."""
import io
import os
from typing import Optional
import PyPDF2
from docx import Document


class DocumentProcessor:
    """Process documents and extract text."""
    
    async def process_file(self, file_contents: bytes, file_ext: str) -> str:
        """
        Process file and extract text.
        
        Args:
            file_contents: File content as bytes
            file_ext: File extension (e.g., '.pdf', '.docx')
        
        Returns:
            Extracted text
        """
        if file_ext == '.pdf':
            return self._extract_from_pdf(file_contents)
        elif file_ext in ['.docx', '.doc']:
            return self._extract_from_docx(file_contents)
        elif file_ext == '.txt':
            return file_contents.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _extract_from_pdf(self, file_contents: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = io.BytesIO(file_contents)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting PDF text: {str(e)}")
    
    def _extract_from_docx(self, file_contents: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            doc_file = io.BytesIO(file_contents)
            doc = Document(doc_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting DOCX text: {str(e)}")

