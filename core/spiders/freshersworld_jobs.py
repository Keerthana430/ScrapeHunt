# Freshersworld Job Scraper - Fixed and Working Version
import scrapy
from scrapy import Request
import json
import time
import re
from urllib.parse import urlencode, urljoin

class FreshersworldJobScraper(scrapy.Spider):
    name = 'freshersworld_jobs'
    allowed_domains = ['freshersworld.com']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 3,
        'FEEDS': {
            'freshersworld_jobs.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 2,
            },
        },
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
    }
    
    def start_requests(self):
        # Correct URL format as provided by user
        keywords = [
            "web dev", "python developer", "java developer", "data analyst",
            "mechanical engineer", "civil engineer", "ui ux designer", "digital marketing",
            "network engineer", "sales executive", "marketing", "software developer",
            "content marketing", "social media marketing"
        ]
        
        for kw in keywords:
            # Use the correct URL format provided by user
            search_url = f"https://www.freshersworld.com/jobs/jobsearch/{kw.strip().lower().replace(' ', '-')}"
            yield Request(
                url=search_url,
                callback=self.parse_jobs,
                meta={'search_term': kw, 'page': 1},
                headers={'Referer': 'https://www.freshersworld.com/'},
                dont_filter=True  # Allow duplicate URLs for different search terms
            )
        
        # Also try some working general URLs
        general_urls = [
            'https://www.freshersworld.com/jobs'
        ]
        
        for url in general_urls:
            yield Request(
                url=url,
                callback=self.parse_jobs,
                meta={'search_term': 'general', 'page': 1},
                headers={'Referer': 'https://www.freshersworld.com/'}
            )
    
    def parse_jobs(self, response):
        search_term = response.meta.get('search_term', 'N/A')
        self.logger.info(f"Parsing Freshersworld JOBS from: {response.url}")
        self.logger.info(f"Search term: {search_term}")
        
        # Debug: Log page title and content
        page_title = response.css('title::text').get('')
        self.logger.info(f"Page title: {page_title}")
        
        # First, let's try to find any job containers with more specific selectors
        job_selectors = [
            '[data-job-id]',  # This was working according to logs
            '.job-item',
            '.job-container',
            '.latest-jobs-container .job-detail',
            '.job-detail-container',
            '.joblist-item',
            '.job-card',
            'div[class*="job"]',
            'div[id*="job"]',
            '.company-job-detail',
            '.fresh-job-item'
        ]
        
        jobs_found = False
        total_jobs_extracted = 0
        
        for selector in job_selectors:
            jobs = response.css(selector)
            if jobs:
                self.logger.info(f"Found {len(jobs)} jobs using selector: {selector}")
                jobs_found = True
                
                for i, job in enumerate(jobs[:20]):  # Limit to 20 jobs per search
                    try:
                        job_data = self.extract_job_data(job, response, search_term)
                        if job_data:
                            # Validate that we have meaningful data
                            if (job_data.get('job_title', 'N/A') != 'N/A' or 
                                job_data.get('company_name', 'N/A') != 'N/A' or
                                len(job_data.get('job_description', '')) > 10):
                                yield job_data
                                total_jobs_extracted += 1
                            else:
                                self.logger.debug(f"Skipping job {i+1} - insufficient data")
                    except Exception as e:
                        self.logger.error(f"Error extracting job {i+1}: {str(e)}")
                        continue
                
                self.logger.info(f"Successfully extracted {total_jobs_extracted} jobs with selector: {selector}")
                if total_jobs_extracted > 0:
                    break  # Stop trying other selectors if we got data
        
        if not jobs_found or total_jobs_extracted == 0:
            self.logger.warning("No jobs found or extracted with standard selectors, trying alternative extraction...")
            self.try_alternative_extraction(response, search_term)
    
    def extract_job_data(self, job_element, response, search_term='N/A'):
        """Extract job data from element with improved logic"""
        
        def clean_text(text):
            if not text:
                return 'N/A'
            # Remove extra whitespace and clean up
            cleaned = ' '.join(str(text).strip().split())
            return cleaned if cleaned else 'N/A'
        
        def safe_get_text(element, selectors):
            """Safely try multiple selectors and return first valid result"""
            for selector in selectors:
                try:
                    # Try getting text content
                    result = element.css(selector + '::text').get()
                    if result and result.strip():
                        return clean_text(result)
                    
                    # Try getting attribute if it's an attribute selector
                    if '::attr(' in selector:
                        result = element.css(selector).get()
                        if result and result.strip():
                            return clean_text(result)
                    
                    # Try getting inner text from nested elements
                    result = element.css(selector).get()
                    if result and result.strip():
                        # Extract text from HTML
                        import html
                        text = html.unescape(re.sub(r'<[^>]+>', ' ', result))
                        if text and text.strip():
                            return clean_text(text)
                            
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            return 'N/A'
        
        # Get all text from the job element for debugging
        all_element_text = ' '.join(job_element.css('::text').getall())
        self.logger.debug(f"Job element text sample: {all_element_text[:200]}...")
        
        # Enhanced selectors based on common job site patterns
        title_selectors = [
            'h3 a',
            'h2 a', 
            'h4 a',
            '.job-title a',
            '.job-name a',
            '.position-title',
            'a[href*="/jobs/"]',
            '.title',
            'span.job-title',
            '[data-job-title]'
        ]
        
        company_selectors = [
            '.company-name',
            '.company',
            '.employer',
            '.organization',
            '.comp_name',
            '.hiring-company',
            'span[class*="company"]',
            '[data-company]'
        ]
        
        location_selectors = [
            '.location',
            '.job-location', 
            '.city',
            '.place',
            '.loc',
            'span[class*="location"]',
            '[data-location]'
        ]
        
        salary_selectors = [
            '.salary',
            '.ctc',
            '.package',
            '.pay',
            '.wage',
            '.compensation',
            'span[class*="salary"]',
            '[data-salary]'
        ]
        
        # Extract basic data
        job_title = safe_get_text(job_element, title_selectors)
        company_name = safe_get_text(job_element, company_selectors)
        location = safe_get_text(job_element, location_selectors)
        salary = safe_get_text(job_element, salary_selectors)
        
        # Get job URL
        job_url = 'N/A'
        url_selectors = ['a::attr(href)', 'h3 a::attr(href)', 'h2 a::attr(href)']
        for selector in url_selectors:
            try:
                url = job_element.css(selector).get()
                if url:
                    if not url.startswith('http'):
                        url = urljoin(response.url, url)
                    job_url = url
                    break
            except:
                continue
        
        # Extract description from all available text
        description_text = clean_text(all_element_text)
        if len(description_text) > 500:
            description_text = description_text[:500] + '...'
        
        # Try to extract additional info from text
        experience = 'N/A'
        if 'fresher' in all_element_text.lower():
            experience = 'Fresher'
        elif 'year' in all_element_text.lower():
            exp_match = re.search(r'(\d+[-\s]*\d*\s*years?)', all_element_text, re.IGNORECASE)
            if exp_match:
                experience = exp_match.group(1)
        
        # Posted date extraction
        posted_date = 'N/A'
        date_patterns = [
            r'(\d{1,2}\s+days?\s+ago)',
            r'(\d{1,2}\s+hours?\s+ago)',
            r'(today|yesterday)',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, all_element_text, re.IGNORECASE)
            if match:
                posted_date = match.group(1)
                break
        
        # If we don't have basic info, try to extract from element text
        if job_title == 'N/A' and company_name == 'N/A':
            # Try to find patterns in text
            text_lines = [line.strip() for line in all_element_text.split('\n') if line.strip()]
            
            if text_lines:
                # First meaningful line might be job title
                for line in text_lines[:3]:
                    if len(line) > 5 and not line.lower().startswith(('apply', 'view', 'click', 'read')):
                        job_title = line[:100]  # Limit length
                        break
                
                # Look for company patterns
                for line in text_lines:
                    if any(word in line.lower() for word in ['company', 'ltd', 'inc', 'corp', 'pvt', 'technologies', 'solutions']):
                        company_name = line[:100]  # Limit length
                        break
        
        # Create job data object
        job_data = {
            'job_title': job_title,
            'company_name': company_name,
            'location': location if location != 'N/A' else 'India',
            'salary_range': salary,
            'job_type': 'Full-time',
            'experience_required': experience,
            'company_rating': 'N/A',
            'posted_date': posted_date,
            'job_description': description_text,
            'job_url': job_url,
            'scraped_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'Freshersworld.com',
            'search_term': search_term,
            'page_url': response.url
        }
        
        # Log what we extracted for debugging
        self.logger.debug(f"Extracted job: {job_data['job_title']} at {job_data['company_name']}")
        
        return job_data
    
    def try_alternative_extraction(self, response, search_term):
        """Alternative extraction method when standard selectors fail"""
        
        self.logger.info("Trying alternative extraction methods...")
        
        # Method 1: Look for any divs that might contain job information
        potential_containers = response.css('div, article, section')
        
        job_keywords = ['developer', 'engineer', 'marketing', 'analyst', 'executive', 'manager', 'job', 'vacancy', 'position']
        
        found_jobs = []
        
        for container in potential_containers:
            container_text = ' '.join(container.css('::text').getall()).strip()
            
            # Skip if too short or too long
            if len(container_text) < 50 or len(container_text) > 2000:
                continue
            
            # Check if it contains job-related keywords
            if any(keyword in container_text.lower() for keyword in job_keywords):
                found_jobs.append(container_text)
        
        self.logger.info(f"Found {len(found_jobs)} potential jobs using alternative method")
        
        # Extract data from found containers
        for i, job_text in enumerate(found_jobs[:10]):  # Limit to 10
            
            # Try to extract company name
            company_patterns = [
                r'([A-Z][a-zA-Z\s&]+(?:Ltd|Inc|Corp|Company|Solutions|Technologies|Services|Pvt|Private Limited))',
                r'Company:\s*([A-Z][a-zA-Z\s&,\.]+?)(?:\n|,|\||$)',
                r'([A-Z][a-zA-Z\s&]{10,50})'  # Any capitalized text 10-50 chars
            ]
            
            company_name = 'Various Companies'
            for pattern in company_patterns:
                match = re.search(pattern, job_text)
                if match:
                    company_name = match.group(1).strip()[:100]
                    break
            
            # Try to extract job title
            job_title = f'Position {i+1}'
            title_patterns = [
                r'(Developer|Engineer|Analyst|Marketing|Executive|Manager|Specialist|Coordinator)[a-zA-Z\s]*',
                r'^([A-Z][a-zA-Z\s]{5,50}?)(?:\n|at|in|for)',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, job_text, re.IGNORECASE)
                if match:
                    job_title = match.group(1).strip()[:100]
                    break
            
            # Location extraction
            location = 'India'
            indian_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata', 'Ahmedabad', 'Gurgaon', 'Noida']
            for city in indian_cities:
                if city.lower() in job_text.lower():
                    location = city
                    break
            
            yield {
                'job_title': job_title,
                'company_name': company_name,
                'location': location,
                'salary_range': 'N/A',
                'job_type': 'Full-time',
                'experience_required': 'Fresher to 3 years',
                'company_rating': 'N/A',
                'posted_date': 'Recent',
                'job_description': job_text[:300] + '...' if len(job_text) > 300 else job_text,
                'job_url': response.url,
                'scraped_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Freshersworld.com (Alternative)',
                'search_term': search_term,
                'extraction_method': 'alternative'
            }

# Simple backup scraper
class SimpleFreshersworldScraper(scrapy.Spider):
    name = 'simple_freshersworld'
    allowed_domains = ['freshersworld.com']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 4,
        'FEEDS': {
            'simple_freshersworld.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 2,
            },
        },
    }
    
    def start_requests(self):
        # Use only working URLs
        urls = [
            'https://www.freshersworld.com/jobs',
            'https://www.freshersworld.com/jobs/jobsearch/digital-marketing',
            'https://www.freshersworld.com/jobs/jobsearch/marketing'
        ]
        
        for url in urls:
            yield Request(url=url, callback=self.parse)
    
    def parse(self, response):
        self.logger.info(f"Simple parsing: {response.url}")
        
        # Get page text and try to extract any job-like information
        page_text = response.css('body').get('')
        
        # Look for job-related patterns in the HTML
        job_patterns = [
            r'<[^>]*>([^<]*(?:developer|engineer|marketing|analyst)[^<]*)</[^>]*>',
            r'<[^>]*>([^<]*(?:job|vacancy|position|career)[^<]*)</[^>]*>'
        ]
        
        jobs_found = []
        for pattern in job_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                clean_match = re.sub(r'\s+', ' ', match).strip()
                if len(clean_match) > 10 and len(clean_match) < 200:
                    jobs_found.append(clean_match)
        
        # Remove duplicates
        jobs_found = list(set(jobs_found))[:15]
        
        self.logger.info(f"Simple extraction found {len(jobs_found)} potential jobs")
        
        for i, job_text in enumerate(jobs_found):
            yield {
                'job_title': job_text,
                'company_name': 'Various Companies',
                'location': 'India',
                'salary_range': 'N/A',
                'job_type': 'Entry Level',
                'experience_required': 'Fresher',
                'company_rating': 'N/A',
                'posted_date': 'Recent',
                'job_description': job_text,
                'job_url': response.url,
                'scraped_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Freshersworld.com (Simple)',
                'element_index': i
            }

# Run the scrapers
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    
    process = CrawlerProcess()
    
    print("🚀 Starting FIXED Freshersworld Job Scrapers...")
    print("📋 Using correct URL format: /jobs/jobsearch/{keyword}")
    print("🔧 Enhanced data extraction logic...")
    print("🎯 Targeting multiple job categories...")
    
    # Run the main scraper
    process.crawl(FreshersworldJobScraper)
    
    # Uncomment to also run the simple backup scraper
    # process.crawl(SimpleFreshersworldScraper)
    
    process.start()
    
    print("\n✅ Scraping completed!")
    print("📁 Check these files:")
    print("   - freshersworld_jobs.json (Main results)")
    print("   - simple_freshersworld.json (Backup results)")
    print("\n🔍 If still getting empty results, the site may require JavaScript or have anti-bot measures!")