"""
Job Crawler Service using Selenium
Crawls job postings from various platforms
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import logging
import time
import re

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Job, CrawlerJob, JobSource

logger = logging.getLogger(__name__)


class JobCrawler:
    """Crawls job postings from various platforms"""
    
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
    
    def crawl_linkedin(self, search_query: str, location: str = None):
        """Crawl LinkedIn job postings"""
        jobs = []
        
        try:
            # Build LinkedIn search URL
            base_url = "https://www.linkedin.com/jobs/search/"
            params = f"?keywords={search_query.replace(' ', '%20')}"
            if location:
                params += f"&location={location.replace(' ', '%20')}"
            
            url = base_url + params
            logger.info(f"Crawling LinkedIn: {url}")
            
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Scroll to load more jobs
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Find job cards
            job_cards = self.driver.find_elements(By.CLASS_NAME, "base-card")
            
            for card in job_cards[:20]:  # Limit to 20 jobs
                try:
                    job_data = self._parse_linkedin_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"Error parsing LinkedIn job card: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except Exception as e:
            logger.error(f"LinkedIn crawl error: {e}")
            return jobs
    
    def crawl_indeed(self, search_query: str, location: str = None):
        """Crawl Indeed job postings"""
        jobs = []
        
        try:
            # Build Indeed search URL
            base_url = "https://www.indeed.com/jobs"
            params = f"?q={search_query.replace(' ', '+')}"
            if location:
                params += f"&l={location.replace(' ', '+')}"
            
            url = base_url + params
            logger.info(f"Crawling Indeed: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Find job cards
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
            
            for card in job_cards[:20]:
                try:
                    job_data = self._parse_indeed_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"Error parsing Indeed job card: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on Indeed")
            return jobs
            
        except Exception as e:
            logger.error(f"Indeed crawl error: {e}")
            return jobs
    
    def _parse_linkedin_card(self, card):
        """Parse LinkedIn job card"""
        try:
            title = card.find_element(By.CLASS_NAME, "base-search-card__title").text
            company = card.find_element(By.CLASS_NAME, "base-search-card__subtitle").text
            location = card.find_element(By.CLASS_NAME, "job-search-card__location").text
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            
            # Extract job ID from URL
            job_id_match = re.search(r'/jobs/view/(\d+)', link)
            external_id = f"linkedin_{job_id_match.group(1)}" if job_id_match else None
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'source_url': link,
                'external_id': external_id,
                'source': JobSource.LINKEDIN
            }
        except Exception as e:
            logger.warning(f"Error parsing LinkedIn card: {e}")
            return None
    
    def _parse_indeed_card(self, card):
        """Parse Indeed job card"""
        try:
            title_elem = card.find_element(By.CLASS_NAME, "jobTitle")
            title = title_elem.text
            link = title_elem.find_element(By.TAG_NAME, "a").get_attribute("href")
            
            company = card.find_element(By.CLASS_NAME, "companyName").text
            location = card.find_element(By.CLASS_NAME, "companyLocation").text
            
            # Extract job ID from URL
            job_id_match = re.search(r'jk=([a-zA-Z0-9]+)', link)
            external_id = f"indeed_{job_id_match.group(1)}" if job_id_match else None
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'source_url': link,
                'external_id': external_id,
                'source': JobSource.INDEED
            }
        except Exception as e:
            logger.warning(f"Error parsing Indeed card: {e}")
            return None


def start_crawler_job(crawler_job_id: int, search_query: str, location: str, source: JobSource):
    """
    Background task to crawl jobs
    This would typically be run by Celery worker
    """
    db = SessionLocal()
    
    try:
        # Update crawler job status
        crawler_job = db.query(CrawlerJob).filter(
            CrawlerJob.id == crawler_job_id
        ).first()
        
        if not crawler_job:
            logger.error(f"Crawler job {crawler_job_id} not found")
            return
        
        crawler_job.status = "running"
        crawler_job.started_at = datetime.utcnow()
        db.commit()
        
        # Initialize crawler
        crawler = JobCrawler()
        crawler._init_driver()
        
        # Crawl based on source
        jobs_data = []
        if source == JobSource.LINKEDIN:
            jobs_data = crawler.crawl_linkedin(search_query, location)
        elif source == JobSource.INDEED:
            jobs_data = crawler.crawl_indeed(search_query, location)
        
        # Save jobs to database
        jobs_saved = 0
        for job_data in jobs_data:
            try:
                # Check if job already exists
                existing = db.query(Job).filter(
                    Job.external_id == job_data['external_id']
                ).first()
                
                if not existing:
                    new_job = Job(**job_data)
                    db.add(new_job)
                    jobs_saved += 1
            except Exception as e:
                logger.warning(f"Error saving job: {e}")
                continue
        
        db.commit()
        
        # Update crawler job
        crawler_job.status = "completed"
        crawler_job.jobs_found = jobs_saved
        crawler_job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Crawler job {crawler_job_id} completed: {jobs_saved} jobs saved")
        
    except Exception as e:
        logger.error(f"Error in crawler job {crawler_job_id}: {e}")
        if crawler_job:
            crawler_job.status = "failed"
            crawler_job.error_message = str(e)
            crawler_job.completed_at = datetime.utcnow()
            db.commit()
            
    finally:
        if crawler:
            crawler._close_driver()
        db.close()
