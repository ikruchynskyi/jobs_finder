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
import time

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
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(settings.SELENIUM_TIMEOUT)
        
    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def apply_linkedin(self, job_url: str, user_profile: dict, resume_path: str):
        """Apply to LinkedIn job"""
        log = []
        
        try:
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


def apply_to_job_task(application_id: int, user_id: int, job_id: int):
    """
    Background task to apply to a job
    This would typically be run by Celery worker
    """
    db = SessionLocal()
    
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
        
        # Initialize applicator
        applicator = JobApplicator()
        applicator._init_driver()
        
        # Get user profile
        user_profile = {
            'phone': user.profiles[0].phone if user.profiles else None,
            'linkedin': user.profiles[0].linkedin_url if user.profiles else None,
        }
        
        resume_path = application.resume_used or (
            user.profiles[0].resume_url if user.profiles else None
        )
        
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
        
        application.automation_log = log
        db.commit()
        
        logger.info(f"Application {application_id} processed: {application.status}")
        
    except Exception as e:
        logger.error(f"Error in apply_to_job_task: {e}")
        if application:
            application.status = ApplicationStatus.FAILED
            application.error_message = str(e)
            db.commit()
            
    finally:
        if applicator:
            applicator._close_driver()
        db.close()
