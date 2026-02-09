"""
Job Application Automation Service using Selenium
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import logging
import logging
import time
import os

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import JobApplication, Job, User, ApplicationStatus

logger = logging.getLogger(__name__)


class JobApplicator:
    """Handles automated job applications using Selenium"""
    
    def __init__(self):
        self.driver = None
        
    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        
        if settings.SELENIUM_HEADLESS:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'user-agent={settings.CRAWLER_USER_AGENT}')
        
        try:
            logger.info(f"Connecting to Selenium Grid at {settings.SELENIUM_URL}")
            self.driver = webdriver.Remote(
                command_executor=settings.SELENIUM_URL,
                options=options
            )
            self.driver.implicitly_wait(settings.SELENIUM_TIMEOUT)
            logger.info("Successfully connected to Selenium Grid")
        except Exception as e:
            logger.error(f"Failed to connect to Selenium Grid: {e}")
            raise
        
    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def login_linkedin(self, email: str, password: str) -> str:
        """
        Log in to LinkedIn and return the li_at cookie.
        Raises Exception if login fails.
        """
        try:
            self._init_driver()
            logger.info("Navigating to LinkedIn login page...")
            self.driver.get("https://www.linkedin.com/login")
            
            # Enter credentials
            logger.info("Entering credentials...")
            email_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_elem.send_keys(email)
            
            pass_elem = self.driver.find_element(By.ID, "password")
            pass_elem.send_keys(password)
            
            # Submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            
            # Wait for login to complete (check for feed or challenge)
            logger.info("Waiting for login completion...")
            time.sleep(5)  # specific wait for potential redirects
            
            # Check for security challenge (manual intervention needed)
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                raise Exception("LinkedIn triggered a security challenge (CAPTCHA/2FA). Please use manual cookie entry.")
            
            # Check for failed login
            if "login-submit" in self.driver.current_url or "uas/login" in self.driver.current_url:
                raise Exception("Login failed. Check your credentials.")

            # Extract cookie
            cookie = self.driver.get_cookie('li_at')
            if cookie:
                logger.info("Successfully retrieved li_at cookie")
                return cookie['value']
            else:
                raise Exception("Could not find li_at cookie after login.")
                
        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            raise e
        finally:
            self._close_driver()

    def _authenticate_linkedin(self, cookie_value: str = None):
        """Authenticate with LinkedIn using session cookie"""
        if not cookie_value:
            logger.warning("No LinkedIn cookie provided, skipping authentication")
            return

        try:
            logger.info("Authenticating with LinkedIn...")
            self.driver.get("https://www.linkedin.com")
            self.driver.add_cookie({
                'name': 'li_at',
                'value': cookie_value,
                'domain': '.linkedin.com'
            })
            logger.info("LinkedIn cookie injected")
        except Exception as e:
            logger.error(f"Failed to inject LinkedIn cookie: {e}")

    def apply_linkedin(self, job_url: str, user_profile: dict, resume_path: str):
        """Apply to LinkedIn job"""
        log = []
        
        try:
            # Authenticate first
            self._authenticate_linkedin(user_profile.get('linkedin_cookies'))
            
            log.append(f"Opening LinkedIn job: {job_url}")
            self.driver.get(job_url)
            time.sleep(2)
            
            # Click Easy Apply button
            log.append("Looking for Easy Apply button")
            easy_apply_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button"))
            )
            easy_apply_btn.click()
            log.append("Clicked Easy Apply")
            
            # Fill application form
            log.append("Filling application form")
            self._fill_linkedin_form(user_profile, resume_path, log)
            
            # Submit application
            log.append("Submitting application")
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Submit']")
            submit_btn.click()
            
            log.append("Application submitted successfully")
            return True, log
            
        except Exception as e:
            log.append(f"Error: {str(e)}")
            logger.error(f"LinkedIn application error: {e}")
            return False, log
    
    def apply_indeed(self, job_url: str, user_profile: dict, resume_path: str):
        """Apply to Indeed job"""
        log = []
        
        try:
            log.append(f"Opening Indeed job: {job_url}")
            self.driver.get(job_url)
            time.sleep(2)
            
            # Click Apply Now button
            log.append("Looking for Apply button")
            apply_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "indeedApplyButton"))
            )
            apply_btn.click()
            log.append("Clicked Apply Now")
            
            # Fill application
            log.append("Filling application form")
            self._fill_indeed_form(user_profile, resume_path, log)
            
            # Submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            
            log.append("Application submitted successfully")
            return True, log
            
        except Exception as e:
            log.append(f"Error: {str(e)}")
            logger.error(f"Indeed application error: {e}")
            return False, log
    
    def _fill_linkedin_form(self, user_profile: dict, resume_path: str, log: list):
        """Fill LinkedIn application form"""
        try:
            # Upload resume
            resume_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            resume_input.send_keys(resume_path)
            log.append("Resume uploaded")
            
            # Fill contact info if requested
            try:
                phone_input = self.driver.find_element(By.NAME, "phoneNumber")
                if phone_input:
                    phone_input.clear()
                    phone_input.send_keys(user_profile.get('phone', ''))
                    log.append("Phone number filled")
            except NoSuchElementException:
                pass
            
            # Continue through multi-step form
            while True:
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Continue']")
                    next_btn.click()
                    time.sleep(1)
                    log.append("Clicked Continue")
                except NoSuchElementException:
                    break
                    
        except Exception as e:
            log.append(f"Form filling error: {str(e)}")
            raise
    
    def _fill_indeed_form(self, user_profile: dict, resume_path: str, log: list):
        """Fill Indeed application form"""
        try:
            # Similar logic for Indeed
            resume_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            resume_input.send_keys(resume_path)
            log.append("Resume uploaded")
            
            # Fill additional fields as needed
            # This would be customized based on Indeed's form structure
            
        except Exception as e:
            log.append(f"Form filling error: {str(e)}")
            raise

    def _capture_screenshot(self, application_id: int):
        """Capture screenshot and return URL"""
        try:
            if self.driver:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"application_{application_id}_{timestamp}.png"
                storage_dir = "/app/storage/screenshots"
                os.makedirs(storage_dir, exist_ok=True)
                filepath = os.path.join(storage_dir, filename)
                
                self.driver.save_screenshot(filepath)
                logger.info(f"Screenshot saved to {filepath}")
                return f"/static/screenshots/{filename}"
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
        return None

def apply_to_job_task(application_id: int, user_id: int, job_id: int):
    """
    Background task to apply to a job
    This would typically be run by Celery worker
    """
    db = SessionLocal()
    applicator = None
    
    try:
        # Get application, user, and job details
        application = db.query(JobApplication).filter(
            JobApplication.id == application_id
        ).first()
        
        job = db.query(Job).filter(Job.id == job_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not all([application, job, user]):
            logger.error(f"Missing data for application {application_id}")
            return
        
        # Update status to in progress
        application.status = ApplicationStatus.IN_PROGRESS
        db.commit()
        
        # Initialize applicator and AI service
        applicator = JobApplicator()
        applicator._init_driver()
        
        # Get Gemini Key
        gemini_key = user.profiles[0].gemini_api_key if user.profiles else None
        
        # Select best resume
        resume_url = None
        resume_path = None
        
        if user.resumes and gemini_key:
            from app.services.ai import AIService
            ai_service = AIService(gemini_key)
            
            # Use AI to pick best resume
            resumes_data = [
                {'id': r.id, 'extracted_text': r.extracted_text} 
                for r in user.resumes if r.extracted_text
            ]
            
            if resumes_data:
                logger.info("Using AI to select best resume...")
                best_resume_id = ai_service.analyze_job_match(
                    job.description, 
                    resumes_data
                )
                
                selected_resume = next((r for r in user.resumes if r.id == best_resume_id), user.resumes[0])
                logger.info(f"AI selected resume: {selected_resume.file_name}")
                
                # Construct local path from URL logic (assuming local storage)
                # URL: /static/resumes/user_id/filename
                # Path: /app/storage/users/user_id/resume/filename
                resume_path = f"/app/storage/users/{user.id}/resume/{selected_resume.file_name}"
        
        if not resume_path:
            # Fallback to default
            resume_url = application.resume_used or (
                user.profiles[0].resume_url if user.profiles else None
            )
            # Convert URL to local path if needed, or use logic similar to above
            if resume_url:
                 filename = resume_url.split('/')[-1]
                 resume_path = f"/app/storage/users/{user.id}/resume/{filename}"

        # Get user profile
        user_profile = {
            'phone': user.profiles[0].phone if user.profiles else None,
            'linkedin': user.profiles[0].linkedin_url if user.profiles else None,
            'linkedin_cookies': user.profiles[0].linkedin_cookies if user.profiles else None,
        }
        
        # Apply based on job source
        success = False
        log = []
        
        if job.source.value == "linkedin":
            success, log = applicator.apply_linkedin(job.source_url, user_profile, resume_path)
        elif job.source.value == "indeed":
            success, log = applicator.apply_indeed(job.source_url, user_profile, resume_path)
        else:
            log.append(f"Unsupported job source: {job.source.value}")
        
        # Update application
        if success:
            application.status = ApplicationStatus.APPLIED
            application.applied_at = datetime.utcnow()
        else:
            application.status = ApplicationStatus.FAILED
            application.error_message = "Application automation failed"
            # Capture screenshot for functional failures
            if applicator:
                screenshot_url = applicator._capture_screenshot(application.id)
                if screenshot_url:
                    application.screenshot_url = screenshot_url
        
        application.automation_log = log
        db.commit()
        
        logger.info(f"Application {application_id} processed: {application.status}")
        
    except Exception as e:
        logger.error(f"Error in apply_to_job_task: {e}")
        if application:
            application.status = ApplicationStatus.FAILED
            application.error_message = str(e)
            
            # Capture screenshot for exceptions
            if applicator:
                screenshot_url = applicator._capture_screenshot(application.id)
                if screenshot_url:
                    application.screenshot_url = screenshot_url
            
            db.commit()
            
    finally:
        if applicator:
            applicator._close_driver()
        db.close()
