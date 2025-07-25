from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import json
import time
from datetime import datetime
import random

class LinkedInSeleniumScraper:
    def __init__(self, headless=True):
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
    
    def scrape_linkedin_jobs(self, query="software developer", location="India", pages=3):
        """Scrape jobs from LinkedIn.com"""
        all_jobs = []
        base_url = "https://www.linkedin.com"
        
        print(f"🔍 Scraping LinkedIn.com for '{query}' in '{location}'...")
        
        try:
            # Go to LinkedIn jobs page
            jobs_url = f"{base_url}/jobs/search/?keywords={query.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            self.driver.get(jobs_url)
            time.sleep(3)
            
            for page in range(pages):
                print(f"📄 Scraping LinkedIn page {page + 1}/{pages}...")
                
                # Scroll to load more jobs
                self.scroll_to_load_jobs()
                
                # Wait for job cards to load with multiple selectors
                try:
                    job_cards = self.wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                            ".jobs-search__results-list li[data-occludable-job-id], .job-search-card, .jobs-search-results__list-item"))
                    )
                    print(f"✅ Found {len(job_cards)} job cards on page {page + 1}")
                except TimeoutException:
                    print(f"⚠️ Timeout waiting for jobs on page {page + 1}")
                    # Try alternative selector
                    try:
                        job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search__results-list li")
                        print(f"✅ Found {len(job_cards)} job cards with alternative selector")
                    except:
                        print(f"❌ No jobs found on page {page + 1}")
                        continue
                
                if not job_cards:
                    print(f"❌ No jobs found on page {page + 1}")
                    continue
                
                jobs_extracted = 0
                for i, card in enumerate(job_cards[:10]):  # Limit to 10 jobs per page
                    try:
                        print(f"🔍 Extracting job {i + 1}/{min(10, len(job_cards))}...")
                        job_data = self.extract_linkedin_job(card, base_url)
                        if job_data:
                            all_jobs.append(job_data)
                            jobs_extracted += 1
                            print(f"✅ Extracted: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
                        time.sleep(0.5)  # Reduced delay
                    except Exception as e:
                        print(f"⚠️ Error extracting job {i + 1}: {e}")
                        continue
                
                print(f"📊 Successfully extracted {jobs_extracted} jobs from page {page + 1}")
                
                # Navigate to next page
                if page < pages - 1:
                    if not self.navigate_to_next_page():
                        print("❌ Could not navigate to next page, stopping...")
                        break
                    time.sleep(2)
        
        except Exception as e:
            print(f"❌ Error during LinkedIn scraping: {e}")
        
        return all_jobs
    
    def scroll_to_load_jobs(self):
        """Scroll page to load more job listings"""
        try:
            # Scroll down to load more jobs - reduced iterations
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
            # Scroll back up a bit
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Error scrolling: {e}")
    
    def navigate_to_next_page(self):
        """Navigate to next page of results"""
        try:
            # Try multiple selectors for next button
            next_selectors = [
                "button[aria-label*='Next']",
                ".artdeco-pagination__button--next",
                "button[data-li-page-num]",
                ".pv3 button[aria-label='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled() and next_button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", next_button)
                        print("✅ Clicked next page button")
                        return True
                except NoSuchElementException:
                    continue
            
            # If no next button found, try scrolling to load more
            print("⚠️ No next button found, scrolling for more results...")
            self.scroll_to_load_jobs()
            return True
            
        except Exception as e:
            print(f"⚠️ Error navigating to next page: {e}")
            return False
    
    def extract_linkedin_job(self, card, base_url):
        """Extract job data from LinkedIn job card"""
        try:
            job_data = {}
            
            # Debug: Print card HTML to understand structure (removed for speed)
            # print(f"🔍 Card HTML snippet: {card.get_attribute('outerHTML')[:200]}...")
            
            # Title and Link - Try multiple selectors
            title_selectors = [
                "h3.base-search-card__title a",
                ".base-search-card__title a",
                "h3 a[data-tracking-control-name*='job']",
                ".job-card-container__link",
                "a[data-tracking-control-name*='job_title']",
                "h3 a"
            ]
            
            title_found = False
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['title'] = title_elem.text.strip()
                    job_data['link'] = title_elem.get_attribute('href')
                    title_found = True
                    # print(f"✅ Title found with selector: {selector}")  # Removed for speed
                    break
                except NoSuchElementException:
                    continue
            
            if not title_found:
                print("❌ Title not found, trying text-based extraction...")
                try:
                    # Try to get any h3 or title-like element
                    title_elem = card.find_element(By.CSS_SELECTOR, "h3, [role='heading'], .job-title")
                    job_data['title'] = title_elem.text.strip()
                    job_data['link'] = card.find_element(By.CSS_SELECTOR, "a").get_attribute('href') if card.find_elements(By.CSS_SELECTOR, "a") else 'Not available'
                    title_found = True
                except NoSuchElementException:
                    print("❌ Could not extract title")
                    return None
            
            # Company - Try multiple selectors
            company_selectors = [
                ".base-search-card__subtitle a",
                "h4.base-search-card__subtitle a",
                "a[data-tracking-control-name*='company']",
                ".job-card-container__company-name",
                "h4 a"
            ]
            
            company_found = False
            for selector in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['company'] = company_elem.text.strip()
                    company_found = True
                    # print(f"✅ Company found with selector: {selector}")  # Removed for speed
                    break
                except NoSuchElementException:
                    continue
            
            if not company_found:
                try:
                    # Try to get any h4 or company-like element
                    company_elem = card.find_element(By.CSS_SELECTOR, "h4, .company-name")
                    job_data['company'] = company_elem.text.strip()
                except NoSuchElementException:
                    job_data['company'] = 'Not specified'
                    print("⚠️ Company not found")
            
            # Location - Try multiple selectors
            location_selectors = [
                ".job-search-card__location",
                ".base-search-card__metadata",
                "[data-tracking-control-name*='location']",
                ".job-card-container__metadata-item"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['location'] = location_elem.text.strip()
                    break
                except NoSuchElementException:
                    job_data['location'] = 'Not specified'
            
            # Posted date - Try multiple selectors
            date_selectors = [
                ".job-search-card__listdate",
                "time",
                "[data-tracking-control-name*='time']",
                ".job-card-container__metadata-wrapper time"
            ]
            
            for selector in date_selectors:
                try:
                    date_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['posted_date'] = date_elem.text.strip()
                    break
                except NoSuchElementException:
                    job_data['posted_date'] = 'Recently posted'
            
            # Try to click on job to get more details
            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(0.5)
                
                # Try to click on the job card
                clickable_element = card.find_element(By.CSS_SELECTOR, "a")
                self.driver.execute_script("arguments[0].click();", clickable_element)
                time.sleep(1.5)
                
                # Try to extract additional details from job details panel
                try:
                    # Salary selectors
                    salary_selectors = [
                        ".salary",
                        ".compensation-text",
                        "[data-tracking-control-name*='salary']",
                        ".job-details-jobs-unified-top-card__job-insight--highlight"
                    ]
                    
                    salary_found = False
                    for selector in salary_selectors:
                        try:
                            salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            job_data['salary'] = salary_elem.text.strip()
                            salary_found = True
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not salary_found:
                        job_data['salary'] = 'Not disclosed'
                
                    # Description
                    desc_selectors = [
                        ".show-more-less-html__markup",
                        ".job-details-jobs-unified-top-card__job-description",
                        ".jobs-box__html-content"
                    ]
                    
                    desc_found = False
                    for selector in desc_selectors:
                        try:
                            desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            description = desc_elem.text.strip()
                            job_data['description'] = description[:300] + '...' if len(description) > 300 else description
                            desc_found = True
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not desc_found:
                        job_data['description'] = 'No description available'
                
                    # Experience level
                    exp_selectors = [
                        ".job-criteria__text",
                        ".job-details-jobs-unified-top-card__job-insight",
                        "[data-tracking-control-name*='experience']"
                    ]
                    
                    exp_found = False
                    for selector in exp_selectors:
                        try:
                            exp_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            job_data['experience_required'] = exp_elem.text.strip()
                            exp_found = True
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not exp_found:
                        job_data['experience_required'] = 'Not specified'
                    
                except Exception as e:
                    print(f"⚠️ Error extracting additional details: {e}")
                    job_data['salary'] = 'Not disclosed'
                    job_data['description'] = 'No description available'
                    job_data['experience_required'] = 'Not specified'
                    
            except Exception as e:
                print(f"⚠️ Could not click on job card: {e}")
                job_data['salary'] = 'Not disclosed'
                job_data['description'] = 'No description available'
                job_data['experience_required'] = 'Not specified'
            
            # Additional fields
            job_data.update({
                'job_type': self.determine_job_type(job_data.get('title', ''), job_data.get('description', '')),
                'source': 'LinkedIn.com',
                'scraped_at': datetime.now().isoformat()
            })
            
            # Validate that we have essential data
            if job_data.get('title') and job_data.get('company'):
                return job_data
            else:
                print(f"❌ Missing essential data - Title: {job_data.get('title')}, Company: {job_data.get('company')}")
                return None
            
        except Exception as e:
            print(f"⚠️ Error extracting LinkedIn job: {e}")
            return None
    
    def determine_job_type(self, title, description):
        """Determine job type from title and description"""
        text = f"{title} {description}".lower()
        
        if any(term in text for term in ['intern', 'internship', 'trainee']):
            return 'Internship'
        elif any(term in text for term in ['contract', 'contractor', 'freelance']):
            return 'Contract'
        elif any(term in text for term in ['part time', 'part-time']):
            return 'Part Time'
        else:
            return 'Full Time'
    
    def save_jobs(self, jobs, filename):
        """Save jobs to JSON file without summary"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(jobs)} jobs to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving jobs: {e}")
            return False
    
    def print_summary(self, jobs):
        """Print job scraping summary"""
        if not jobs:
            print("❌ No jobs found!")
            return
        
        print(f"\n{'='*50}")
        print(f"📊 LINKEDIN SCRAPING SUMMARY")
        print(f"{'='*50}")
        print(f"Total jobs: {len(jobs)}")
        
        if jobs:
            print(f"\n📝 Sample Jobs:")
            for i, job in enumerate(jobs[:3]):  # Show 3 sample jobs
                print(f"\n  Job {i+1}:")
                print(f"    Title: {job.get('title', 'N/A')}")
                print(f"    Company: {job.get('company', 'N/A')}")
                print(f"    Location: {job.get('location', 'N/A')}")
                print(f"    Salary: {job.get('salary', 'N/A')}")
                print(f"    Type: {job.get('job_type', 'N/A')}")
                print(f"    Posted: {job.get('posted_date', 'N/A')}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run the LinkedIn scraper"""
    scraper = LinkedInSeleniumScraper(headless=True)  # Set to True for headless mode
    
    try:
        # Configuration
        QUERY = "software developer"
        LOCATION = "India"
        PAGES = 2  # Increased for testing
        
        print("🚀 Starting LinkedIn Selenium Scraper")
        print(f"Query: {QUERY}")
        print(f"Location: {LOCATION}")
        print(f"Pages: {PAGES}")
        print("=" * 50)
        
        # Scrape jobs
        jobs = scraper.scrape_linkedin_jobs(QUERY, LOCATION, PAGES)
        
        if jobs:
            scraper.save_jobs(jobs, 'outputs/linkedin_jobs.json')
            scraper.print_summary(jobs)
            print(f"\n🎉 LinkedIn scraping completed!")
            print(f"📁 Results saved in 'linkedin_jobs.json'")
        else:
            print("\n❌ No jobs were scraped from LinkedIn!")
            print("💡 Try running with headless=False to debug the issue")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()