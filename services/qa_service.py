import requests
import os
import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class QAService:
    def __init__(self):
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.hf_api_url = "https://api-inference.huggingface.co/models"
        self.qa_model = os.getenv(
            "HF_QA_MODEL",
            "mistralai/Mistral-7B-Instruct-v0.2"
        )
        
        if not self.hf_api_key:
            raise ValueError("HUGGINGFACE_API_KEY must be set in environment variables")
    
    async def answer_question(self, question: str, candidate_data: Dict[str, Any]) -> str:
        try:
            context = self._prepare_context(candidate_data)
            prompt = self._create_prompt(question, context)
            answer = await self._call_hf_api(prompt)
            return answer
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    def _prepare_context(self, candidate_data: Dict[str, Any]) -> str:
        context_parts = []
        
        if candidate_data.get("introduction"):
            context_parts.append(f"Introduction: {candidate_data['introduction']}")
        
        education = candidate_data.get("education", {})
        if education:
            edu_str = "Education: " + json.dumps(education)
            context_parts.append(edu_str)
        
        experience = candidate_data.get("experience", {})
        if experience:
            exp_str = "Experience: " + json.dumps(experience)
            context_parts.append(exp_str)
        
        skills = candidate_data.get("skills", [])
        if skills:
            context_parts.append(f"Skills: {', '.join(skills)}")
        
        certifications = candidate_data.get("certifications", [])
        if certifications:
            context_parts.append(f"Certifications: {', '.join(certifications)}")
        
        projects = candidate_data.get("projects", [])
        if projects:
            context_parts.append(f"Projects: {', '.join(projects)}")
        
        hobbies = candidate_data.get("hobbies", [])
        if hobbies:
            context_parts.append(f"Hobbies: {', '.join(hobbies)}")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        prompt = f"""Based on the following candidate information, answer the question accurately and concisely.

Candidate Information:
{context}

Question: {question}

Answer:"""
        return prompt
    
    async def _call_hf_api(self, prompt: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.hf_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                f"{self.hf_api_url}/{self.qa_model}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    if "generated_text" in result[0]:
                        return result[0]["generated_text"].strip()
                    elif isinstance(result[0], dict) and "text" in result[0]:
                        return result[0]["text"].strip()
                
                if isinstance(result, str):
                    return result.strip()
                elif isinstance(result, list) and len(result) > 0:
                    return str(result[0]).strip()
                
                return "I couldn't generate a proper answer. Please try rephrasing your question."
            
            elif response.status_code == 503:
                logger.warning("Model is loading, please try again in a few seconds")
                return "The AI model is currently loading. Please try again in a few seconds."
            
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return self._fallback_answer(prompt)
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error calling HF API: {e}")
            return self._fallback_answer(prompt)
    
    def _fallback_answer(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        
        if "graduation" in prompt_lower or "graduate" in prompt_lower:
            if "education" in prompt_lower:
                years = re.findall(r'\b(19|20)\d{2}\b', prompt)
                if years:
                    return f"The candidate finished graduation in {years[-1]}."
            return "The graduation date information is not explicitly available in the candidate's data."
        elif "skill" in prompt_lower:
            if "skills:" in prompt_lower:
                skills_match = re.search(r'skills:\s*([^\n]+)', prompt_lower, re.IGNORECASE)
                if skills_match:
                    skills_text = skills_match.group(1)
                    return f"The candidate has the following skills: {skills_text}"
            return "Please check the skills section in the candidate's profile for detailed information."
        elif "experience" in prompt_lower or "work" in prompt_lower:
            if "experience:" in prompt_lower:
                exp_match = re.search(r'experience:\s*({[^}]+})', prompt_lower)
                if exp_match:
                    return f"Based on the candidate's experience: {exp_match.group(1)}"
            return "Please check the experience section in the candidate's profile for work history details."
        else:
            return "I couldn't generate a proper answer. Please check the candidate's profile or try rephrasing your question."
