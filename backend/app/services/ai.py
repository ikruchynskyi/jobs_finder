import google.generativeai as genai
import logging
import json
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    def analyze_job_match(self, job_description: str, resumes: List[Dict[str, Any]]) -> int:
        """
        Analyze job description and resumes to find the best match.
        Returns the ID of the best matching resume.
        """
        if not self.model or not resumes:
            return None

        prompt = f"""
        You are an expert HR recruiter.
        
        Job Description:
        {job_description[:5000]}
        
        Resumes:
        {json.dumps([{ 'id': r['id'], 'text': r['extracted_text'][:2000] } for r in resumes])}
        
        Task:
        Select the resume ID that best matches this job description.
        Return ONLY the resume ID as an integer. nothing else.
        """
        
        try:
            response = self.model.generate_content(prompt)
            best_resume_id = int(response.text.strip())
            return best_resume_id
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return resumes[0]['id'] if resumes else None

    def extract_application_data(self, job_description: str, resume_text: str) -> Dict[str, Any]:
        """
        Extract specific data points from resume relevant to the job.
        Returns a dictionary of Q&A.
        """
        if not self.model:
            return {}

        prompt = f"""
        You are a smart applicant assistant.
        
        Resume:
        {resume_text[:10000]}
        
        Job Description:
        {job_description[:5000]}
        
        Task:
        Extract and infer the following information to fill a job application form.
        Return a valid JSON object.
        
        Fields to extract:
        - summary: A brief professional summary tailored to this job (max 500 chars)
        - skills_match: List of matching skills found in resume
        - experience_years_relevant: Estimated years of relevant experience (integer)
        - cover_letter_intro: A generic intro paragraph for a cover letter
        
        JSON Output:
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Clean up markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI data extraction failed: {e}")
            return {}
