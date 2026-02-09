"""
Job Application Automation Service using Selenium
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select as SeleniumSelect
from datetime import datetime
import logging
import time
import random
import os

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.crypto import decrypt_value
from app.models.models import JobApplication, Job, User, ApplicationStatus

logger = logging.getLogger(__name__)

# Realistic user agents to rotate through
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]


def _human_delay(min_s: float = 1.0, max_s: float = 3.5):
    """Sleep a random duration to mimic human behaviour."""
    time.sleep(random.uniform(min_s, max_s))


class JobApplicator:
    """Handles automated job applications using Selenium"""

    def __init__(self):
        self.driver = None
        self._use_undetected = True  # prefer undetected-chromedriver

    def _init_driver(self):
        """Initialize Selenium WebDriver with anti-detection measures."""
        user_agent = random.choice(_USER_AGENTS)

        # --- Try undetected-chromedriver first (local/headful mode) ---
        if self._use_undetected:
            try:
                import undetected_chromedriver as uc
                uc_options = uc.ChromeOptions()
                if settings.SELENIUM_HEADLESS:
                    uc_options.add_argument("--headless=new")
                uc_options.add_argument("--no-sandbox")
                uc_options.add_argument("--disable-dev-shm-usage")
                uc_options.add_argument(f"user-agent={user_agent}")
                uc_options.add_argument("--window-size=1920,1080")
                uc_options.add_argument("--disable-extensions")
                uc_options.add_argument("--disable-popup-blocking")

                self.driver = uc.Chrome(options=uc_options)
                self.driver.implicitly_wait(settings.SELENIUM_TIMEOUT)

                # Remove webdriver fingerprint traces
                self.driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {"source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                        window.chrome = {runtime: {}};
                    """},
                )

                logger.info("Initialized undetected-chromedriver successfully")
                return
            except Exception as e:
                logger.warning(f"undetected-chromedriver unavailable ({e}), falling back to Selenium Grid")

        # --- Fallback: Selenium Grid (remote) ---
        options = webdriver.ChromeOptions()
        if settings.SELENIUM_HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--window-size=1920,1080")

        # Extra stealth prefs
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            logger.info(f"Connecting to Selenium Grid at {settings.SELENIUM_URL}")
            self.driver = webdriver.Remote(
                command_executor=settings.SELENIUM_URL,
                options=options,
            )
            self.driver.implicitly_wait(settings.SELENIUM_TIMEOUT)

            # Remove navigator.webdriver flag
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
            )

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
            _human_delay(4.0, 7.0)  # realistic wait for redirects
            
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

    def _find_easy_apply_button(self):
        """Find LinkedIn Easy Apply button using multiple selector strategies"""
        selectors = [
            # Most reliable: the button has a stable id
            (By.ID, "jobs-apply-button-id"),
            # aria-label contains "Easy Apply"
            (By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]"),
            # Button class contains jobs-apply-button (CSS handles multi-class)
            (By.CSS_SELECTOR, "button.jobs-apply-button"),
            # Wrapper div class
            (By.CSS_SELECTOR, ".jobs-apply-button--top-card button"),
            # Text content fallback
            (By.XPATH, "//button[.//span[contains(text(), 'Easy Apply')]]"),
        ]
        for by, selector in selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                return btn
            except TimeoutException:
                continue
        return None

    def apply_linkedin(self, job_url: str, user_profile: dict, resume_path: str,
                       ai_service=None, job_description: str = None, resume_text: str = None):
        """Apply to LinkedIn job"""
        log = []

        try:
            # Authenticate first
            self._authenticate_linkedin(user_profile.get('linkedin_cookies'))

            log.append(f"Opening LinkedIn job: {job_url}")
            self.driver.get(job_url)
            _human_delay(2.5, 5.0)

            # Click Easy Apply button
            log.append("Looking for Easy Apply button")
            easy_apply_btn = self._find_easy_apply_button()
            if not easy_apply_btn:
                log.append("Error: Could not find Easy Apply button")
                return False, log
            easy_apply_btn.click()
            log.append("Clicked Easy Apply")
            _human_delay(1.5, 3.0)

            # Fill application form
            log.append("Filling application form")
            self._fill_linkedin_form(user_profile, resume_path, log,
                                     ai_service=ai_service,
                                     job_description=job_description,
                                     resume_text=resume_text)

            # Submit application — look for the final submit button
            log.append("Submitting application")
            submitted = False
            submit_selectors = [
                (By.XPATH, "//button[contains(@aria-label, 'Submit application')]"),
                (By.XPATH, "//button[contains(., 'Submit application')]"),
                (By.XPATH, "//button[contains(@aria-label, 'Submit')]"),
                (By.CSS_SELECTOR, "button[aria-label*='Submit']"),
            ]
            for by, selector in submit_selectors:
                try:
                    submit_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    submit_btn.click()
                    submitted = True
                    break
                except TimeoutException:
                    continue

            if not submitted:
                log.append("Error: Could not find Submit button")
                return False, log

            _human_delay(2.0, 4.0)
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
            _human_delay(2.0, 4.0)
            
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
    
    def _handle_resume_step(self, resume_path: str, log: list):
        """
        Handle LinkedIn's resume selection step.
        Strategy:
        1. If LinkedIn shows previously uploaded resumes, select the most recently used one.
        2. If no resumes are listed, upload from the portal via file input.
        """
        from datetime import datetime as dt

        # Check if LinkedIn's resume picker is showing (resume list items with radio buttons)
        resume_items = self.driver.find_elements(
            By.XPATH,
            "//div[contains(@class, 'jobs-document-upload-redesign-card')]"
                " | //div[contains(@class, 'ui-attachment')]"
                " | //div[contains(@class, 'jobs-resume-picker')]"
                " | //label[contains(@class, 'jobs-document-upload')]"
        )

        if not resume_items:
            # Broader fallback: look for any list of resume cards with "Last used" text
            resume_items = self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'Last used')]/.."
            )

        if resume_items:
            log.append(f"Found {len(resume_items)} resume(s) on LinkedIn")

            # Find which one is already selected (has active/checked radio)
            already_selected = False
            try:
                selected = self.driver.find_element(
                    By.XPATH,
                    "//input[@type='radio' and @checked]"
                        " | //input[@type='radio'][../..//div[contains(@class, 'selected')]]"
                )
                if selected:
                    already_selected = True
            except NoSuchElementException:
                pass

            # Parse "Last used on" dates to find the most recent resume
            best_item = None
            best_date = None

            for item in resume_items:
                try:
                    text = item.text
                    # Extract date from "Last used on M/D/YYYY" pattern
                    if "Last used on" in text:
                        date_str = text.split("Last used on")[-1].strip().split("\n")[0].strip()
                        try:
                            parsed = dt.strptime(date_str, "%m/%d/%Y")
                        except ValueError:
                            try:
                                parsed = dt.strptime(date_str, "%m/%d/%y")
                            except ValueError:
                                parsed = None

                        if parsed and (best_date is None or parsed > best_date):
                            best_date = parsed
                            best_item = item
                except Exception:
                    continue

            if best_item:
                # Click the most recently used resume to select it
                try:
                    # Try clicking the radio button or the card itself
                    radio = best_item.find_element(By.XPATH, ".//input[@type='radio'] | .//button | .//label")
                    radio.click()
                except NoSuchElementException:
                    best_item.click()
                log.append(f"Selected most recently used resume (last used {best_date.strftime('%m/%d/%Y') if best_date else 'unknown'})")
            elif already_selected:
                log.append("Keeping pre-selected resume (latest already selected)")
            else:
                # Just click the first resume item as fallback
                try:
                    first_radio = resume_items[0].find_element(By.XPATH, ".//input[@type='radio'] | .//button | .//label")
                    first_radio.click()
                except NoSuchElementException:
                    resume_items[0].click()
                log.append("Selected first available resume")
            return

        # No resume picker shown — fall back to file upload
        if resume_path:
            try:
                resume_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                # Fix path: Selenium Chrome container mounts ./storage:/storage
                selenium_path = resume_path.replace("/app/storage", "/storage")
                resume_input.send_keys(selenium_path)
                log.append(f"Uploaded resume via file input: {selenium_path}")
                _human_delay(1.0, 2.0)
            except NoSuchElementException:
                log.append("No file input found for resume upload")
        else:
            log.append("No resume path available and no LinkedIn resumes found")

    def _scrape_form_questions(self):
        """Scrape all form questions from the current LinkedIn Easy Apply step."""
        questions = []

        # Handle select/dropdown questions
        form_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "div[data-test-form-element]"
        )
        if not form_elements:
            # Broader fallback
            form_elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".fb-dash-form-element"
            )

        for idx, elem in enumerate(form_elements):
            question_data = {'id': f'q{idx}', 'question': '', 'type': 'text', 'options': [], 'element': elem}

            # Get question text from label
            try:
                label = elem.find_element(By.CSS_SELECTOR, "label span[aria-hidden='true'], label")
                question_data['question'] = label.text.strip()
            except NoSuchElementException:
                try:
                    label = elem.find_element(By.TAG_NAME, "label")
                    question_data['question'] = label.text.strip()
                except NoSuchElementException:
                    continue

            if not question_data['question']:
                continue

            # Detect element type and options
            # Select dropdown
            try:
                select_el = elem.find_element(By.TAG_NAME, "select")
                question_data['type'] = 'select'
                question_data['select_element'] = select_el
                options = select_el.find_elements(By.TAG_NAME, "option")
                question_data['options'] = [
                    o.get_attribute('value') for o in options
                    if o.get_attribute('value') and o.get_attribute('value') != 'Select an option'
                ]
                questions.append(question_data)
                continue
            except NoSuchElementException:
                pass

            # Radio buttons
            try:
                radios = elem.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                if radios:
                    question_data['type'] = 'radio'
                    question_data['radio_elements'] = radios
                    labels = elem.find_elements(By.CSS_SELECTOR, "label.fb-dash-form-element__label, label")
                    # Get option labels (skip the question label itself)
                    radio_labels = []
                    for r in radios:
                        r_id = r.get_attribute('id')
                        if r_id:
                            try:
                                rl = elem.find_element(By.CSS_SELECTOR, f"label[for='{r_id}']")
                                radio_labels.append(rl.text.strip())
                            except NoSuchElementException:
                                radio_labels.append(r.get_attribute('value') or '')
                        else:
                            radio_labels.append(r.get_attribute('value') or '')
                    question_data['options'] = radio_labels
                    questions.append(question_data)
                    continue
            except NoSuchElementException:
                pass

            # Checkbox
            try:
                checkboxes = elem.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                if checkboxes:
                    question_data['type'] = 'checkbox'
                    question_data['checkbox_elements'] = checkboxes
                    questions.append(question_data)
                    continue
            except NoSuchElementException:
                pass

            # Text input
            try:
                text_input = elem.find_element(By.CSS_SELECTOR, "input[type='text'], input:not([type])")
                question_data['type'] = 'text'
                question_data['input_element'] = text_input
                questions.append(question_data)
                continue
            except NoSuchElementException:
                pass

            # Textarea
            try:
                textarea = elem.find_element(By.TAG_NAME, "textarea")
                question_data['type'] = 'text'
                question_data['input_element'] = textarea
                questions.append(question_data)
                continue
            except NoSuchElementException:
                pass

        return questions

    def _handle_additional_questions(self, ai_service, job_description: str,
                                     resume_text: str, user_profile: dict, log: list):
        """Use AI to answer form questions on the current step."""
        questions = self._scrape_form_questions()
        if not questions:
            log.append("No form questions found on this step")
            return

        log.append(f"Found {len(questions)} form question(s)")

        # Build question list for AI (without Selenium elements)
        ai_questions = [
            {'id': q['id'], 'question': q['question'], 'type': q['type'], 'options': q['options']}
            for q in questions
        ]

        # Get AI answers
        answers = {}
        if ai_service:
            answers = ai_service.answer_form_questions(
                questions=ai_questions,
                job_description=job_description or '',
                resume_text=resume_text or '',
                user_profile=user_profile or {},
            )
            log.append(f"AI provided {len(answers)} answer(s)")
        else:
            log.append("No AI service available, using fallback answers")

        # Apply answers to form elements
        for q in questions:
            answer = answers.get(q['id'])
            if not answer:
                # Fallback: for yes/no selects, default to "Yes"
                if q['type'] == 'select' and q['options']:
                    if 'Yes' in q['options']:
                        answer = 'Yes'
                    else:
                        answer = q['options'][0]
                else:
                    continue

            try:
                if q['type'] == 'select' and 'select_element' in q:
                    sel = SeleniumSelect(q['select_element'])
                    sel.select_by_value(answer)
                    log.append(f"Selected '{answer}' for: {q['question'][:60]}")

                elif q['type'] == 'radio' and 'radio_elements' in q:
                    # Click the radio whose value or label matches the answer
                    clicked = False
                    for radio in q['radio_elements']:
                        val = radio.get_attribute('value') or ''
                        if val == answer:
                            radio.click()
                            clicked = True
                            break
                    if not clicked and q['options']:
                        # Match by option index
                        for i, opt in enumerate(q['options']):
                            if opt == answer and i < len(q['radio_elements']):
                                q['radio_elements'][i].click()
                                break
                    log.append(f"Selected radio '{answer}' for: {q['question'][:60]}")

                elif q['type'] == 'text' and 'input_element' in q:
                    q['input_element'].clear()
                    q['input_element'].send_keys(answer)
                    log.append(f"Entered text for: {q['question'][:60]}")

                elif q['type'] == 'checkbox' and 'checkbox_elements' in q:
                    # If answer is truthy, check it
                    if answer.lower() in ('yes', 'true', '1'):
                        for cb in q['checkbox_elements']:
                            if not cb.is_selected():
                                cb.click()
                    log.append(f"Checked checkbox for: {q['question'][:60]}")

            except Exception as e:
                log.append(f"Failed to fill '{q['question'][:40]}': {str(e)}")

    def _fill_linkedin_form(self, user_profile: dict, resume_path: str, log: list,
                            ai_service=None, job_description: str = None, resume_text: str = None):
        """Fill LinkedIn Easy Apply multi-step modal form"""
        max_steps = 10  # safety limit for multi-step forms

        for step in range(max_steps):
            _human_delay(1.2, 2.5)

            # Detect resume step: look for "Resume" heading or file input
            is_resume_step = False
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//h3[contains(text(), 'Resume')]"
                        " | //span[contains(text(), 'Resume')]"
                        " | //label[contains(text(), 'Resume')]"
                )
                is_resume_step = True
            except NoSuchElementException:
                # Also check if there's a file input or resume picker
                try:
                    self.driver.find_element(By.XPATH, "//*[contains(text(), 'Last used')]")
                    is_resume_step = True
                except NoSuchElementException:
                    pass

            if is_resume_step:
                log.append(f"Resume step detected (step {step + 1})")
                self._handle_resume_step(resume_path, log)

            # Fill phone number if present
            try:
                phone_inputs = self.driver.find_elements(
                    By.XPATH,
                    "//input[contains(@id, 'phoneNumber') or contains(@name, 'phoneNumber')]"
                )
                for phone_input in phone_inputs:
                    if phone_input.get_attribute('value') == '' and user_profile.get('phone'):
                        phone_input.clear()
                        phone_input.send_keys(user_profile['phone'])
                        log.append("Phone number filled")
            except NoSuchElementException:
                pass

            # Handle additional questions (selects, text inputs, radios, etc.)
            # Detect by: "Additional Questions" heading, or form elements with selects/inputs
            has_form_questions = False
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//h3[contains(text(), 'Additional')]"
                        " | //h3[contains(text(), 'Questions')]"
                        " | //h3[contains(text(), 'Work Experience')]"
                        " | //h3[contains(text(), 'Education')]"
                )
                has_form_questions = True
            except NoSuchElementException:
                # Also detect by presence of form elements (selects/inputs in the modal)
                form_selects = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[data-test-form-element] select, .fb-dash-form-element select"
                )
                form_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[data-test-form-element] input[type='text'], "
                    "div[data-test-form-element] textarea, "
                    ".fb-dash-form-element input[type='text'], "
                    ".fb-dash-form-element textarea"
                )
                form_radios = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[data-test-form-element] input[type='radio'], "
                    ".fb-dash-form-element input[type='radio']"
                )
                if form_selects or form_inputs or form_radios:
                    has_form_questions = True

            if has_form_questions and not is_resume_step:
                log.append(f"Additional questions detected (step {step + 1})")
                self._handle_additional_questions(
                    ai_service, job_description, resume_text, user_profile, log
                )
                _human_delay(0.8, 1.8)

            # Check if we reached the review/submit step
            submit_selectors = [
                "//button[contains(@aria-label, 'Submit application')]",
                "//button[contains(., 'Submit application')]",
                "//button[contains(@aria-label, 'Review')]",
                "//button[contains(., 'Review')]",
            ]
            found_submit = False
            for xpath in submit_selectors:
                try:
                    self.driver.find_element(By.XPATH, xpath)
                    found_submit = True
                    log.append(f"Reached final step at step {step + 1}")
                    break
                except NoSuchElementException:
                    continue

            if found_submit:
                # If it's a "Review" button, click it to get to the actual submit
                try:
                    review_btn = self.driver.find_element(
                        By.XPATH,
                        "//button[contains(@aria-label, 'Review') or contains(., 'Review')]"
                    )
                    review_btn.click()
                    log.append("Clicked Review")
                    _human_delay(1.2, 2.5)
                except NoSuchElementException:
                    pass
                break

            # Click Next/Continue to advance to the next step
            next_clicked = False
            next_selectors = [
                "//button[contains(@aria-label, 'Continue')]",
                "//button[contains(@aria-label, 'Next')]",
                "//button[contains(., 'Next')]",
                "//span[text()='Next']/ancestor::button",
            ]
            for xpath in next_selectors:
                try:
                    next_btn = self.driver.find_element(By.XPATH, xpath)
                    next_btn.click()
                    log.append(f"Clicked Next (step {step + 1})")
                    next_clicked = True
                    break
                except NoSuchElementException:
                    continue

            if not next_clicked:
                log.append(f"No Next/Continue/Submit button found at step {step + 1}")
                break
    
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
        
        # Get Gemini Key and initialize AI service (decrypt from DB)
        gemini_key_enc = user.profiles[0].gemini_api_key if user.profiles else None
        gemini_key = decrypt_value(gemini_key_enc) if gemini_key_enc else None
        ai_service = None

        from app.services.ai import AIService
        if gemini_key:
            ai_service = AIService(gemini_key, user_id=user_id)

        # Select best resume
        resume_url = None
        resume_path = None
        resume_text = None

        if user.resumes and ai_service:
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
                resume_text = selected_resume.extracted_text

                # Construct local path from URL logic (assuming local storage)
                resume_path = f"/app/storage/users/{user.id}/resume/{selected_resume.file_name}"

        if not resume_path:
            # Fallback to default
            resume_url = application.resume_used or (
                user.profiles[0].resume_url if user.profiles else None
            )
            if resume_url:
                 filename = resume_url.split('/')[-1]
                 resume_path = f"/app/storage/users/{user.id}/resume/{filename}"

        # Get resume text if not already set
        if not resume_text and user.resumes:
            for r in user.resumes:
                if r.extracted_text:
                    resume_text = r.extracted_text
                    break

        # Get user profile with extra context for AI
        profile = user.profiles[0] if user.profiles else None
        user_profile = {
            'phone': profile.phone if profile else None,
            'linkedin': profile.linkedin_url if profile else None,
            'linkedin_cookies': decrypt_value(profile.linkedin_cookies) if profile and profile.linkedin_cookies else None,
            'location': profile.location if profile else None,
            'skills': profile.skills if profile else None,
            'experience_years': profile.experience_years if profile else None,
        }

        # Apply based on job source
        success = False
        log = []

        if job.source.value == "linkedin":
            success, log = applicator.apply_linkedin(
                job.source_url, user_profile, resume_path,
                ai_service=ai_service,
                job_description=job.description,
                resume_text=resume_text,
            )
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
