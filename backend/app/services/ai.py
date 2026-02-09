import google.generativeai as genai
import logging
import json
import time
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import AIUsageLog

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter: max N calls per minute per user
_rate_limit_store: Dict[int, list] = {}
_RATE_LIMIT_MAX = 15  # max API calls per minute
_RATE_LIMIT_WINDOW = 60  # seconds


def _check_rate_limit(user_id: Optional[int]) -> bool:
    """Return True if the call is allowed, False if rate-limited."""
    if not user_id:
        return True
    now = time.time()
    calls = _rate_limit_store.setdefault(user_id, [])
    # Purge old entries
    _rate_limit_store[user_id] = [t for t in calls if now - t < _RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[user_id]) >= _RATE_LIMIT_MAX:
        return False
    _rate_limit_store[user_id].append(now)
    return True


class AIService:
    def __init__(self, api_key: str, user_id: Optional[int] = None):
        self.api_key = api_key
        self.user_id = user_id
        self.model = None

        if not api_key or not api_key.strip():
            logger.warning("AIService initialised without a valid API key")
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("AIService initialised successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            self.model = None

    def _log_usage(self, service_type: str, response=None, status: str = "success", error_message: str = None):
        """Log AI usage to the database."""
        if not self.user_id:
            return

        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        if response and hasattr(response, 'usage_metadata') and response.usage_metadata:
            metadata = response.usage_metadata
            input_tokens = getattr(metadata, 'prompt_token_count', 0) or 0
            output_tokens = getattr(metadata, 'candidates_token_count', 0) or 0
            total_tokens = getattr(metadata, 'total_token_count', 0) or 0

        db = SessionLocal()
        try:
            log_entry = AIUsageLog(
                user_id=self.user_id,
                service_type=service_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                status=status,
                error_message=error_message,
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log AI usage: {e}")
            db.rollback()
        finally:
            db.close()

    def analyze_job_match(self, job_description: str, resumes: List[Dict[str, Any]]) -> int:
        """
        Analyze job description and resumes to find the best match.
        Returns the ID of the best matching resume.
        """
        if not self.model or not resumes:
            return resumes[0]['id'] if resumes else None

        if not _check_rate_limit(self.user_id):
            logger.warning(f"Rate limit hit for user {self.user_id} on job_match")
            return resumes[0]['id']

        valid_ids = {r['id'] for r in resumes}

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
            self._log_usage("job_match", response=response)
            best_resume_id = int(response.text.strip())
            # Validate: must be one of the provided IDs
            if best_resume_id not in valid_ids:
                logger.warning(f"AI returned invalid resume ID {best_resume_id}, falling back")
                return resumes[0]['id']
            return best_resume_id
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            self._log_usage("job_match", status="error", error_message=str(e))
            return resumes[0]['id'] if resumes else None

    def answer_form_questions(
        self,
        questions: List[Dict[str, Any]],
        job_description: str,
        resume_text: str,
        user_profile: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Answer application form questions using AI.

        Args:
            questions: List of dicts with keys:
                - id: element identifier
                - question: the question text
                - type: "select", "text", "radio", "checkbox"
                - options: list of option values (for select/radio/checkbox)
            job_description: the job posting text
            resume_text: the applicant's resume text
            user_profile: dict with user info (skills, location, phone, etc.)

        Returns:
            Dict mapping question id -> answer value
        """
        if not self.model or not questions:
            return {}

        if not _check_rate_limit(self.user_id):
            logger.warning(f"Rate limit hit for user {self.user_id} on form_questions")
            return {}

        questions_json = json.dumps(questions, indent=2)
        profile_json = json.dumps({k: v for k, v in user_profile.items() if k != 'linkedin_cookies'}, indent=2)

        prompt = f"""You are a job application assistant helping a candidate apply for a position.
Your goal is to answer the application form questions in the way most likely to get the candidate an interview.

CANDIDATE RESUME:
{resume_text[:8000] if resume_text else 'Not available'}

CANDIDATE PROFILE:
{profile_json}

JOB DESCRIPTION:
{job_description[:5000] if job_description else 'Not available'}

FORM QUESTIONS:
{questions_json}

INSTRUCTIONS:
- For each question, provide the best answer based on the candidate's resume and profile.
- For "select" or "radio" type questions, your answer MUST be exactly one of the provided options (copy the option value exactly).
- For "text" type questions, provide a concise, professional answer.
- Always try to present the candidate favorably. If unsure, choose the most positive truthful answer.
- For yes/no questions about skills/experience, answer "Yes" if the resume shows relevant experience, otherwise answer honestly.
- For location questions, answer "Yes" if the candidate is in or near the location, or if the job is remote-friendly.

Return ONLY a valid JSON object mapping each question "id" to the answer string. No extra text.
Example: {{"q1": "Yes", "q2": "5", "q3": "I have 6 years of experience..."}}
"""

        try:
            response = self.model.generate_content(prompt)
            self._log_usage("form_questions", response=response)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            answers = json.loads(text.strip())

            # Validate: for select/radio questions, ensure the answer is one of the options
            for q in questions:
                qid = q.get('id')
                if qid not in answers:
                    continue
                if q.get('type') in ('select', 'radio') and q.get('options'):
                    if answers[qid] not in q['options']:
                        # Try case-insensitive match
                        matched = next(
                            (opt for opt in q['options'] if opt.lower() == str(answers[qid]).lower()),
                            None
                        )
                        if matched:
                            answers[qid] = matched
                        else:
                            # Fall back to first option
                            logger.warning(
                                f"AI answer '{answers[qid]}' not in options {q['options']} for '{q.get('question', qid)}'"
                            )
                            answers[qid] = q['options'][0]

            logger.info(f"AI answered {len(answers)} form questions")
            return answers
        except Exception as e:
            logger.error(f"AI form question answering failed: {e}")
            self._log_usage("form_questions", status="error", error_message=str(e))
            return {}

    def extract_application_data(self, job_description: str, resume_text: str) -> Dict[str, Any]:
        """
        Extract specific data points from resume relevant to the job.
        Returns a dictionary of Q&A.
        """
        if not self.model:
            return {}

        if not _check_rate_limit(self.user_id):
            logger.warning(f"Rate limit hit for user {self.user_id} on data_extraction")
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
            self._log_usage("data_extraction", response=response)
            text = response.text.strip()
            # Clean up markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI data extraction failed: {e}")
            self._log_usage("data_extraction", status="error", error_message=str(e))
            return {}
