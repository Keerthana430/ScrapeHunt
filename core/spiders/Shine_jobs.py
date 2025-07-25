from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import json
import time
from datetime import datetime
import random
import re

class FastShineSeleniumScraper:
    def __init__(self, headless=True):
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Setup Chrome driver with minimal options for speed"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Speed optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(3)
            print("✅ Browser initialized successfully")
            
        except Exception as e:
            print(f"❌ Error setting up Chrome driver: {e}")
            raise
    
    def fast_scrape_shine(self, query="software developer", location="India", max_jobs=50):
        """Fast scraping using direct element extraction"""
        print(f"🚀 Fast scraping Shine.com for '{query}' in '{location}' (max {max_jobs} jobs)...")
        
        all_jobs = []
        base_url = f"https://www.shine.com/job-search/{query.replace(' ', '-')}-jobs"
        
        try:
            print(f"🌐 Loading: {base_url}")
            start_time = time.time()
            
            self.driver.get(base_url)
            print(f"⏱️ Page loaded in {time.time() - start_time:.2f} seconds")
            
            # Wait for job listings to load
            time.sleep(4)
            
            # Scroll to load more jobs
            self.scroll_to_load_jobs()
            
            # Extract jobs using direct element method
            jobs = self.extract_jobs_with_selenium(max_jobs)
            
            if jobs:
                all_jobs.extend(jobs)
                print(f"✅ Extracted {len(jobs)} jobs in {time.time() - start_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        
        return all_jobs
    
    def scroll_to_load_jobs(self):
        """Scroll to load more jobs"""
        try:
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
        except Exception as e:
            print(f"⚠️ Error scrolling: {e}")
    
    def extract_jobs_with_selenium(self, max_jobs):
        """Extract jobs using Selenium with proper selectors"""
        jobs = []
        
        try:
            # Try multiple selectors for job cards
            job_selectors = [
                "div[class*='jobCard']",
                ".job-card",
                ".listRow",
                "div[data-id]",
                ".search-results .job",
                "article",
                "div[class*='job'][class*='card']"
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 5:  # Use selector with most results
                        job_elements = elements
                        print(f"✅ Found {len(elements)} jobs with selector: {selector}")
                        break
                except:
                    continue
            
            if not job_elements:
                print("❌ No job elements found with any selector")
                return []
            
            # Extract data from each job element
            for i, element in enumerate(job_elements[:max_jobs]):
                try:
                    job_data = self.extract_job_from_element(element, i+1)
                    if job_data and self.validate_job_data(job_data):
                        jobs.append(job_data)
                except Exception as e:
                    print(f"⚠️ Error extracting job {i+1}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            print(f"❌ Error in Selenium extraction: {e}")
            return []
    
    def extract_job_from_element(self, element, job_num):
        """Extract job data from a single element with improved logic"""
        try:
            # Get all text content
            full_text = element.text.strip()
            if len(full_text) < 20:
                return None
            
            # Split into lines and clean
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            if len(lines) < 2:
                return None
            
            # Initialize job data
            job_data = {
                'title': 'Not specified',
                'company': 'Not specified',
                'location': 'Not specified',
                'salary': 'Not disclosed',
                'experience_required': 'Not specified',
                'posted_date': 'Recently posted'
            }
            
            # Extract title (first meaningful line that looks like a job title)
            title = self.extract_proper_title(lines, element)
            if not title:
                return None
            job_data['title'] = title
            
            # Extract company (second meaningful line or one with company indicators)
            company = self.extract_proper_company(lines, element)
            job_data['company'] = company
            
            # Extract location from lines
            location = self.extract_proper_location(lines)
            job_data['location'] = location
            
            # Extract experience
            experience = self.extract_proper_experience(lines)
            job_data['experience_required'] = experience
            
            # Extract salary
            salary = self.extract_proper_salary(lines)
            job_data['salary'] = salary
            
            # Extract posted date
            posted_date = self.extract_proper_posted_date(lines)
            job_data['posted_date'] = posted_date
            
            # Try to get link
            try:
                link_element = element.find_element(By.CSS_SELECTOR, "a")
                href = link_element.get_attribute('href')
                job_data['link'] = href if href and 'shine.com' in href else 'Not available'
            except:
                job_data['link'] = 'Not available'
            
            # Additional fields
            job_data.update({
                'job_type': self.determine_job_type(job_data['title'], full_text),
                'description': self.clean_description(full_text),
                'source': 'Shine.com',
                'scraped_at': datetime.now().isoformat()
            })
            
            print(f"  ✓ Job {job_num}: {job_data['title'][:40]}... | {job_data['company']}")
            return job_data
            
        except Exception as e:
            print(f"⚠️ Error in job extraction: {e}")
            return None
    
    def extract_proper_title(self, lines, element):
        """Extract proper job title"""
        try:
            # First try to get from title attribute or data attributes
            title_attrs = ['title', 'data-title', 'aria-label']
            for attr in title_attrs:
                attr_value = element.get_attribute(attr)
                if attr_value and len(attr_value) > 5 and self.is_valid_title(attr_value):
                    return attr_value.strip()
        except:
            pass
        
        # Look for title in first few lines
        job_keywords = ['developer', 'engineer', 'analyst', 'manager', 'specialist', 'associate', 
                       'consultant', 'executive', 'lead', 'senior', 'junior', 'intern', 'trainee']
        
        for line in lines[:3]:
            line_lower = line.lower()
            # Check if line contains job keywords and looks like a title
            if (any(keyword in line_lower for keyword in job_keywords) and
                len(line) > 5 and len(line) < 100 and
                not any(skip in line_lower for skip in ['company', 'location', 'salary', 'experience', 'ago', 'posted', 'apply', 'years', 'lpa'])):
                return line.strip()
        
        # Fallback to first line if it's reasonable
        if lines and len(lines[0]) > 5 and len(lines[0]) < 100:
            return lines[0].strip()
        
        return None
    
    def extract_proper_company(self, lines, element):
        """Extract proper company name"""
        try:
            # Try to get from data attributes
            for attr in ['data-company', 'data-employer']:
                attr_value = element.get_attribute(attr)
                if attr_value and len(attr_value) > 2:
                    return attr_value.strip()
        except:
            pass
        
        # Look for company in lines (usually second line or one with company indicators)
        company_indicators = ['ltd', 'pvt', 'inc', 'corp', 'technologies', 'solutions', 'systems', 
                             'services', 'consultancy', 'consulting', 'software', 'infotech']
        
        # Skip first line (usually title) and look in next few lines
        for line in lines[1:5]:
            line_lower = line.lower()
            # Check if line looks like a company name
            if (len(line) > 2 and len(line) < 80 and
                not any(skip in line_lower for skip in ['years', 'experience', 'salary', 'lpa', 'ago', 'posted', 'apply', 'bangalore', 'mumbai', 'delhi', 'hyderabad', 'chennai', 'pune']) and
                (any(indicator in line_lower for indicator in company_indicators) or 
                 (len(line.split()) <= 4 and not line_lower.isdigit()))):
                return line.strip()
        
        return 'Not specified'
    
    def extract_proper_location(self, lines):
        """Extract proper location"""
        indian_cities = ['bangalore', 'mumbai', 'delhi', 'hyderabad', 'chennai', 'pune', 'kolkata', 
                        'gurgaon', 'noida', 'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur', 
                        'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri', 'patna', 
                        'vadodara', 'ludhiana', 'agra', 'nashik', 'kochi', 'coimbatore', 'kozhikode']
        
        for line in lines:
            line_lower = line.lower()
            if any(city in line_lower for city in indian_cities):
                return line.strip()
        
        return 'Not specified'
    
    def extract_proper_experience(self, lines):
        """Extract experience requirement"""
        for line in lines:
            line_lower = line.lower()
            if (any(exp_word in line_lower for exp_word in ['year', 'experience', 'fresher', 'exp', 'yrs']) and 
                len(line) < 50 and
                any(char.isdigit() for char in line)):
                return line.strip()
        
        # Look for fresher specifically
        for line in lines:
            if 'fresher' in line.lower():
                return 'Fresher'
        
        return 'Not specified'
    
    def extract_proper_salary(self, lines):
        """Extract salary information"""
        for line in lines:
            line_lower = line.lower()
            if (any(sal_word in line_lower for sal_word in ['lpa', 'salary', 'ctc', '₹', 'rs', 'lakhs', 'k']) and 
                len(line) < 50 and
                any(char.isdigit() for char in line)):
                return line.strip()
        
        return 'Not disclosed'
    
    def extract_proper_posted_date(self, lines):
        """Extract posted date"""
        for line in lines:
            line_lower = line.lower()
            if any(date_word in line_lower for date_word in ['ago', 'posted', 'days', 'hours', 'today', 'yesterday']):
                return line.strip()
        
        return 'Recently posted'
    
    def is_valid_title(self, title):
        """Check if extracted title is valid"""
        title_lower = title.lower()
        invalid_words = ['company', 'location', 'salary', 'experience', 'apply', 'view', 'details']
        return not any(word in title_lower for word in invalid_words)
    
    def validate_job_data(self, job_data):
        """Validate extracted job data"""
        # Must have title and it should be reasonable
        title = job_data.get('title', '')
        if not title or title == 'Not specified' or len(title) < 5:
            return False
        
        # Title shouldn't be location or other field
        title_lower = title.lower()
        invalid_titles = ['location', 'salary', 'experience', 'company', 'apply', 'view']
        if any(invalid in title_lower for invalid in invalid_titles):
            return False
        
        return True
    
    def clean_description(self, text):
        """Clean and truncate description"""
        # Remove extra whitespace and truncate
        cleaned = ' '.join(text.split())
        return cleaned[:250] + '...' if len(cleaned) > 250 else cleaned
    
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
    
    def save_jobs(self, jobs, filename='shine_jobs.json'):
        """Save jobs to JSON file without summary"""
        try:
            if not jobs:
                print("❌ No jobs to save")
                return False
            
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
        
        print(f"\n{'='*60}")
        print(f"📊 SHINE SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Total jobs scraped: {len(jobs)}")
        
        # Show first few jobs
        print(f"\n📝 Sample Jobs:")
        for i, job in enumerate(jobs[:5], 1):
            print(f"\n  {i}. {job.get('title', 'N/A')}")
            print(f"     Company: {job.get('company', 'N/A')}")
            print(f"     Location: {job.get('location', 'N/A')}")
            print(f"     Salary: {job.get('salary', 'N/A')}")
            print(f"     Experience: {job.get('experience_required', 'N/A')}")
    
    def close(self):
        """Close the browser"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                print("🔒 Browser closed")
        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")

def main():
    """Main function optimized for speed"""
    scraper = None
    
    try:
        print("🚀 Starting FIXED Shine Selenium Scraper")
        print("=" * 60)
        
        start_total = time.time()
        
        # Initialize scraper
        scraper = FastShineSeleniumScraper(headless=True)
        
        # Fast scrape
        jobs = scraper.fast_scrape_shine("software developer", "India", max_jobs=150)
        
        total_time = time.time() - start_total
        
        if jobs:
            scraper.save_jobs(jobs, 'outputs/shine_jobs.json')
            scraper.print_summary(jobs)
            print(f"\n🎉 Scraping completed in {total_time:.2f} seconds!")
            print(f"📁 Results saved in 'shine_jobs.json'")
            print(f"⚡ Speed: {len(jobs)/total_time:.1f} jobs/second")
        else:
            print(f"\n❌ No jobs scraped in {total_time:.2f} seconds")
    
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()