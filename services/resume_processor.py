import PyPDF2
from docx import Document
import io
import os
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ResumeProcessor:
    def __init__(self):
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.hf_api_url = "https://api-inference.huggingface.co/models"
        self.extraction_model = os.getenv(
            "HF_EXTRACTION_MODEL", 
            "microsoft/DialoGPT-medium"
        )
    
    def extract_text(self, file_content: bytes, file_ext: str) -> str:
        try:
            if file_ext == 'pdf':
                return self._extract_from_pdf(file_content)
            elif file_ext == 'docx':
                return self._extract_from_docx(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise Exception(f"Failed to extract text from file: {str(e)}")
    
    def _extract_from_pdf(self, file_content: bytes) -> str:
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
    
    def _extract_from_docx(self, file_content: bytes) -> str:
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise
    
    def process_resume(self, resume_text: str) -> Dict[str, Any]:
        try:
            if self.hf_api_key:
                try:
                    extracted_data = self._extract_with_hf_api(resume_text)
                    if extracted_data:
                        return extracted_data
                except Exception as e:
                    logger.warning(f"HF API extraction failed, using rule-based: {e}")
            
            return self._extract_with_rules(resume_text)
            
        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            return {
                "education": {},
                "experience": {},
                "skills": [],
                "hobbies": [],
                "certifications": [],
                "projects": [],
                "introduction": resume_text[:500] if resume_text else ""
            }
    
    def _extract_with_hf_api(self, resume_text: str) -> Dict[str, Any]:
        try:
            return None
        except Exception as e:
            logger.error(f"HF API extraction error: {e}")
            return None
    
    def _extract_with_rules(self, resume_text: str) -> Dict[str, Any]:
        text_lower = resume_text.lower()
        lines = resume_text.split('\n')
        
        education = self._extract_education(text_lower, lines)
        experience = self._extract_experience(text_lower, lines)
        skills = self._extract_skills(text_lower, resume_text)
        certifications = self._extract_certifications(text_lower, lines)
        projects = self._extract_projects(text_lower, lines)
        hobbies = self._extract_hobbies(text_lower, lines)
        introduction = self._extract_introduction(resume_text, text_lower)
        
        return {
            "education": education,
            "experience": experience,
            "skills": skills,
            "hobbies": hobbies,
            "certifications": certifications,
            "projects": projects,
            "introduction": introduction
        }
    
    def _extract_education(self, text_lower: str, lines: List[str]) -> Dict:
        education = {}
        education_keywords = ['education', 'degree', 'university', 'college', 'bachelor', 'master', 'phd', 'graduation']
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords):
                education['degree'] = line.strip()
                for year in range(2000, 2030):
                    if str(year) in line:
                        education['year'] = year
                        break
                break
        
        return education
    
    def _extract_experience(self, text_lower: str, lines: List[str]) -> Dict:
        experience = {}
        experience_keywords = ['experience', 'work', 'employment', 'job', 'position', 'role']
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in experience_keywords):
                if i + 1 < len(lines):
                    experience['title'] = lines[i+1].strip() if lines[i+1].strip() else ""
                break
        
        return experience
    
    def _extract_skills(self, text_lower: str, resume_text: str) -> List[str]:
        skills = []
        common_skills = [
            'python', 'java', 'javascript', 'sql', 'mongodb', 'postgresql',
            'fastapi', 'flask', 'django', 'react', 'node.js', 'aws', 'docker',
            'git', 'linux', 'data analysis', 'machine learning', 'deep learning',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'
        ]
        
        skills_keywords = ['skills', 'technical skills', 'competencies']
        skills_text = ""
        
        for keyword in skills_keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                skills_text = resume_text[idx:idx+500].lower()
                break
        
        for skill in common_skills:
            if skill in text_lower or skill in skills_text:
                skills.append(skill.title())
        
        return list(set(skills))
    
    def _extract_certifications(self, text_lower: str, lines: List[str]) -> List[str]:
        certifications = []
        cert_keywords = ['certification', 'certificate', 'certified', 'aws', 'google', 'microsoft']
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in cert_keywords):
                cert = line.strip()
                if len(cert) > 5:
                    certifications.append(cert)
        
        return certifications[:5]
    
    def _extract_projects(self, text_lower: str, lines: List[str]) -> List[str]:
        projects = []
        project_keywords = ['project', 'projects', 'portfolio']
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in project_keywords):
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip() and len(lines[j].strip()) > 10:
                        projects.append(lines[j].strip())
                    if len(projects) >= 5:
                        break
                break
        
        return projects[:5]
    
    def _extract_hobbies(self, text_lower: str, lines: List[str]) -> List[str]:
        hobbies = []
        hobby_keywords = ['hobbies', 'interests', 'hobby', 'interest']
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in hobby_keywords):
                parts = line.split(':')
                if len(parts) > 1:
                    hobby_list = [h.strip() for h in parts[1].split(',')]
                    hobbies.extend(hobby_list[:5])
                break
        
        return hobbies
    
    def _extract_introduction(self, resume_text: str, text_lower: str) -> str:
        intro_keywords = ['summary', 'introduction', 'about', 'profile', 'objective']
        
        for keyword in intro_keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                intro = resume_text[idx:idx+300].strip()
                for kw in intro_keywords:
                    intro = intro.replace(kw, "", 1)
                intro = intro.strip()
                if intro.startswith(':'):
                    intro = intro[1:].strip()
                return intro[:500]
        
        first_paragraph = resume_text.split('\n\n')[0] if '\n\n' in resume_text else resume_text[:300]
        return first_paragraph.strip()[:500]
