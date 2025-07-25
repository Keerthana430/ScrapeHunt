import requests
import json
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
import re

class TimesJobsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.headers.update(self.headers)
    
    def scrape_timesjobs(self, query="software developer", pages=3):
        """Scrape jobs from TimesJobs.com"""
        all_jobs = []
        base_url = "https://www.timesjobs.com"
        
        print(f"🔍 Scraping TimesJobs.com for '{query}'...")
        
        for page in range(1, pages + 1):
            try:
                url = f"{base_url}/candidate/job-search.html"
                params = {
                    'searchType': 'personalizedSearch',
                    'from': 'submit',
                    'txtKeywords': query,
                    'txtLocation': 'India',
                    'cboWorkExp1': '0',
                    'sequence': str(page)
                }
                
                print(f"📄 Scraping TimesJobs page {page}/{pages}...")
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code != 200:
                    print(f"⚠️ Page {page}: Status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job listings
                job_cards = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')
                
                if not job_cards:
                    print(f"❌ No jobs found on page {page}")
                    continue
                
                print(f"✅ Found {len(job_cards)} jobs on page {page}")
                
                for card in job_cards:
                    job_data = self.extract_timesjobs_job(card, base_url)
                    if job_data:
                        all_jobs.append(job_data)
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"⚠️ Error on TimesJobs page {page}: {e}")
                continue
        
        return all_jobs
    
    def extract_timesjobs_job(self, card, base_url):
        """Extract job data from TimesJobs card"""
        try:
            job_data = {}
            
            # Title and Link
            title_elem = card.find('h2') or card.find('a', {'target': '_blank'})
            if title_elem:
                title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if title_link:
                    job_data['title'] = title_link.get_text(strip=True)
                    if title_link.get('href'):
                        job_data['link'] = title_link['href']
            
            # Company
            company_elem = card.find('h3', class_='joblist-comp-name')
            if company_elem:
                company_link = company_elem.find('a')
                job_data['company'] = company_link.get_text(strip=True) if company_link else company_elem.get_text(strip=True)
            
            # Location
            location_elem = card.find('ul', class_='top-jd-dtl clearfix')
            if location_elem:
                location_li = location_elem.find('li')
                if location_li:
                    job_data['location'] = location_li.get_text(strip=True)
            
            # Experience and Salary
            details = card.find_all('li')
            experience = 'Not specified'
            salary = 'Not disclosed'
            
            for li in details:
                text = li.get_text(strip=True).lower()
                if 'experience' in text or 'exp' in text:
                    experience = li.get_text(strip=True)
                elif any(term in text for term in ['salary', 'lpa', 'ctc', '₹', 'rs']):
                    salary = li.get_text(strip=True)
            
            # Description
            desc_elem = card.find('ul', class_='list-job-dtl')
            description = desc_elem.get_text(strip=True) if desc_elem else 'No description available'
            
            # Posted date
            date_elem = card.find('span', class_='sim-posted')
            posted_date = date_elem.get_text(strip=True) if date_elem else 'Recently posted'
            
            job_data.update({
                'salary': salary,
                'job_type': self.determine_job_type(job_data.get('title', ''), description),
                'description': description[:200] + '...' if len(description) > 200 else description,
                'experience_required': experience,
                'posted_date': posted_date,
                'source': 'TimesJobs.com',
                'scraped_at': datetime.now().isoformat()
            })
            
            if job_data.get('title') and job_data.get('company'):
                return job_data
            
        except Exception as e:
            print(f"⚠️ Error extracting TimesJobs job: {e}")
        
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
        """Save jobs to JSON file"""
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
        print(f"📊 SCRAPING SUMMARY")
        print(f"{'='*50}")
        print(f"Total jobs: {len(jobs)}")
        
        # Source breakdown
        sources = {}
        for job in jobs:
            source = job.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print("\n📈 Sources:")
        for source, count in sources.items():
            print(f"  • {source}: {count} jobs")
        
        # Sample job
        if jobs:
            print(f"\n📝 Sample Job:")
            sample = jobs[0]
            print(f"  Title: {sample.get('title', 'N/A')}")
            print(f"  Company: {sample.get('company', 'N/A')}")
            print(f"  Location: {sample.get('location', 'N/A')}")
            print(f"  Salary: {sample.get('salary', 'N/A')}")
            print(f"  Type: {sample.get('job_type', 'N/A')}")

def main():
    """Main function to run the scraper"""
    scraper = TimesJobsScraper()
    
    # Configuration
    QUERY = "software developer"
    PAGES_PER_SITE = 3
    
    print("🚀 Starting TimesJobs Scraper")
    print(f"Query: {QUERY}")
    print(f"Pages per site: {PAGES_PER_SITE}")
    print("=" * 50)
    
    all_jobs = []
    
    # Scrape TimesJobs only
    try:
        timesjobs_jobs = scraper.scrape_timesjobs(QUERY, PAGES_PER_SITE)
        all_jobs.extend(timesjobs_jobs)
        print(f"✅ TimesJobs: {len(timesjobs_jobs)} jobs")
    except Exception as e:
        print(f"❌ TimesJobs error: {e}")
    
    # Save and summarize
    if all_jobs:
        scraper.save_jobs(all_jobs, 'outputs/scrapedTimes_jobs.json')
        scraper.print_summary(all_jobs)
        
        print(f"\n🎉 Scraping completed!")
        print(f"📁 Results saved in 'outputs/scrapedTimes_jobs.json'")
    else:
        print("\n❌ No jobs were scraped!")

if __name__ == "__main__":
    main()