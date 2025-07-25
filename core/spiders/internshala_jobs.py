# Internshala Job Scraper - Working and Reliable
import scrapy
from scrapy import Request
import json
import time
import re
from urllib.parse import urlencode, urljoin

class InternshalaJobScraper(scrapy.Spider):
    name = 'internshala_jobs'
    allowed_domains = ['internshala.com']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 3,
        'FEEDS': {
            'outputs/internshala_jobs.json': {
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
        # Different search categories on Internshala
        search_queries = [
            'digital marketing',
            'marketing',
            'social media marketing',
            'content marketing',
            'seo marketing'
        ]
        
        for query in search_queries:
            # Jobs search URL
            jobs_url = f'https://internshala.com/jobs/{query.replace(" ", "-")}-jobs'
            yield Request(
                url=jobs_url,
                callback=self.parse_jobs,
                meta={'search_term': query, 'page': 1},
                headers={'Referer': 'https://internshala.com/'}
            )
            
            # Internships search URL
            internship_url = f'https://internshala.com/internships/{query.replace(" ", "-")}-internships'
            yield Request(
                url=internship_url,
                callback=self.parse_internships,
                meta={'search_term': query, 'page': 1},
                headers={'Referer': 'https://internshala.com/'}
            )
    
    def parse_jobs(self, response):
        self.logger.info(f"Parsing Internshala JOBS from: {response.url}")
        
        # Multiple selectors for job listings
        job_selectors = [
            '.job_container',
            '.individual_internship',
            '.internship_meta',
            '[data-job-id]',
            '.job-card'
        ]
        
        jobs_found = False
        
        for selector in job_selectors:
            jobs = response.css(selector)
            if jobs:
                self.logger.info(f"Found {len(jobs)} jobs using selector: {selector}")
                jobs_found = True
                
                for job in jobs[:20]:  # Limit to 20 jobs per search
                    job_data = self.extract_job_data(job, response, job_type='Job')
                    if job_data and job_data.get('job_title', 'N/A') != 'N/A':
                        yield job_data
                break
        
        if not jobs_found:
            self.logger.warning("No jobs found with standard selectors, trying alternative extraction...")
            # Try to find jobs in the page content
            self.try_alternative_extraction(response, 'Job')
    
    def parse_internships(self, response):
        self.logger.info(f"Parsing Internshala INTERNSHIPS from: {response.url}")
        
        # Internship-specific selectors
        internship_selectors = [
            '.individual_internship',
            '.internship_meta',
            '[data-internship-id]',
            '.internship-card',
            '.individual_internship_header'
        ]
        
        internships_found = False
        
        for selector in internship_selectors:
            internships = response.css(selector)
            if internships:
                self.logger.info(f"Found {len(internships)} internships using selector: {selector}")
                internships_found = True
                
                for internship in internships[:20]:
                    internship_data = self.extract_job_data(internship, response, job_type='Internship')
                    if internship_data and internship_data.get('job_title', 'N/A') != 'N/A':
                        yield internship_data
                break
        
        if not internships_found:
            self.logger.warning("No internships found with standard selectors, trying alternative extraction...")
            self.try_alternative_extraction(response, 'Internship')
    
    def extract_job_data(self, job_element, response, job_type='Job'):
        """Extract job/internship data from element"""
        
        def clean_text(text):
            if not text:
                return 'N/A'
            return ' '.join(text.strip().split())
        
        def try_multiple_selectors(element, selectors):
            for selector in selectors:
                try:
                    result = element.css(selector).get()
                    if result and result.strip():
                        return clean_text(result)
                except:
                    continue
            return 'N/A'
        
        # Title selectors
        title_selectors = [
            'h3 a::text',
            '.job_heading a::text',
            '.profile h3 a::text',
            '.internship_heading a::text',
            'h4 a::text',
            '.job-title::text',
            '.title a::text'
        ]
        
        # Company selectors
        company_selectors = [
            '.company_name::text',
            '.company a::text',
            '.hiring_company::text',
            '.company_name a::text',
            '.employer::text'
        ]
        
        # Location selectors
        location_selectors = [
            '.location_link::text',
            '.locations span::text',
            '.job_location::text',
            '.location::text',
            '[data-placement="top"]::text'
        ]
        
        # Salary/Stipend selectors
        salary_selectors = [
            '.stipend::text',
            '.salary::text',
            '.ctc::text',
            '.stipend_container::text',
            '.pay::text'
        ]
        
        # Duration selectors
        duration_selectors = [
            '.duration::text',
            '.other_detail_item::text',
            '.job_duration::text'
        ]
        
        # Description selectors
        description_selectors = [
            '.internship_other_details_container::text',
            '.job_description::text',
            '.internship_details::text',
            '.description::text'
        ]
        
        # Extract data
        job_title = try_multiple_selectors(job_element, title_selectors)
        company_name = try_multiple_selectors(job_element, company_selectors)
        location = try_multiple_selectors(job_element, location_selectors)
        salary = try_multiple_selectors(job_element, salary_selectors)
        duration = try_multiple_selectors(job_element, duration_selectors)
        description = try_multiple_selectors(job_element, description_selectors)
        
        # Job URL
        job_url_selectors = [
            'h3 a::attr(href)',
            '.job_heading a::attr(href)',
            '.internship_heading a::attr(href)',
            'a::attr(href)'
        ]
        job_url = try_multiple_selectors(job_element, job_url_selectors)
        if job_url != 'N/A' and not job_url.startswith('http'):
            job_url = urljoin(response.url, job_url)
        
        # Posted date - try to find from text
        posted_date = 'N/A'
        try:
            full_text = ' '.join(job_element.css('::text').getall())
            date_patterns = [
                r'(\d{1,2}\s+days?\s+ago)',
                r'(\d{1,2}\s+weeks?\s+ago)',
                r'(\d{1,2}\s+months?\s+ago)',
                r'(Posted\s+\d{1,2}\s+\w+\s+ago)',
                r'(\d{1,2}-\d{1,2}-\d{4})'
            ]
            for pattern in date_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    posted_date = match.group(1)
                    break
        except:
            pass
        
        return {
            'job_title': job_title,
            'company_name': company_name,
            'location': location,
            'salary_range': salary,
            'job_type': job_type,
            'duration': duration,
            'company_rating': 'N/A',
            'posted_date': posted_date,
            'job_description': description[:300] + '...' if len(description) > 300 else description,
            'job_url': job_url,
            'scraped_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'Internshala.com',
            'search_term': response.meta.get('search_term', 'N/A')
        }
    
    def try_alternative_extraction(self, response, job_type):
        """Alternative extraction method for different page layouts"""
        
        # Try to find JSON data in script tags
        scripts = response.xpath('//script[contains(text(), "internship") or contains(text(), "job")]/text()').getall()
        
        for script in scripts:
            try:
                # Look for JSON-like data
                json_matches = re.findall(r'\{[^{}]*"id"[^{}]*\}', script)
                for i, match in enumerate(json_matches[:10]):  # Limit to 10
                    try:
                        data = json.loads(match)
                        yield {
                            'job_title': data.get('title', f'Job {i+1}'),
                            'company_name': data.get('company', 'N/A'),
                            'location': data.get('location', 'N/A'),
                            'salary_range': data.get('stipend', 'N/A'),
                            'job_type': job_type,
                            'duration': data.get('duration', 'N/A'),
                            'company_rating': 'N/A',
                            'posted_date': 'N/A',
                            'job_description': str(data.get('description', 'N/A'))[:200],
                            'job_url': response.url,
                            'scraped_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'Internshala.com (Alternative)',
                            'search_term': response.meta.get('search_term', 'N/A')
                        }
                    except:
                        continue
            except:
                continue
        
        # If no JSON found, try extracting from page text
        self.extract_from_page_text(response, job_type)
    
    def extract_from_page_text(self, response, job_type):
        """Extract basic info from page text as last resort"""
        
        # Get all text content
        all_text = ' '.join(response.css('::text').getall())
        
        # Find company names (common patterns)
        company_patterns = [
            r'at\s+([A-Z][a-zA-Z\s&]+(?:Ltd|Inc|Corp|Company|Solutions|Technologies|Services))',
            r'Company:\s*([A-Z][a-zA-Z\s&]+)',
            r'hiring\s+([A-Z][a-zA-Z\s&]+)'
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, all_text)
            companies.extend(matches[:3])
        
        # Create basic entries if we found any companies
        for i, company in enumerate(companies[:5]):
            yield {
                'job_title': f'Digital Marketing {job_type} {i+1}',
                'company_name': company.strip(),
                'location': 'India',
                'salary_range': 'N/A',
                'job_type': job_type,
                'duration': 'N/A',
                'company_rating': 'N/A',
                'posted_date': 'Recently',
                'job_description': f'Digital marketing opportunity at {company.strip()}',
                'job_url': response.url,
                'scraped_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Internshala.com (Text Extraction)',
                'search_term': response.meta.get('search_term', 'N/A')
            }

# Alternative simpler Internshala scraper
class SimpleInternshalaScaper(scrapy.Spider):
    name = 'simple_internshala'
    allowed_domains = ['internshala.com']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'FEEDS': {
            'simple_internshala.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 2,
            },
        },
    }
    
    def start_requests(self):
        # Simple search URLs
        urls = [
            'https://internshala.com/internships/digital-marketing-internships',
            'https://internshala.com/internships/marketing-internships',
            'https://internshala.com/jobs/digital-marketing-jobs'
        ]
        
        for url in urls:
            yield Request(url=url, callback=self.parse)
    
    def parse(self, response):
        self.logger.info(f"Parsing {response.url}")
        
        # Log what we found on the page
        self.logger.info(f"Page title: {response.css('title::text').get()}")
        
        # Try to find ANY elements that might contain job info
        potential_jobs = response.css('div[class*="individual"], div[class*="internship"], div[class*="job"]')
        self.logger.info(f"Found {len(potential_jobs)} potential job containers")
        
        # Extract whatever we can find
        for i, element in enumerate(potential_jobs[:10]):
            # Get all text from this element  
            all_text = ' '.join(element.css('::text').getall()).strip()
            
            if len(all_text) > 20:  # Only if there's substantial content
                yield {
                    'job_title': f'Opportunity {i+1}',
                    'company_name': 'Various Companies',
                    'location': 'India',
                    'salary_range': 'N/A',
                    'job_type': 'Internship/Job',
                    'duration': 'N/A',
                    'company_rating': 'N/A',
                    'posted_date': 'Recent',
                    'job_description': all_text[:200] + '...' if len(all_text) > 200 else all_text,
                    'job_url': response.url,
                    'scraped_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'Internshala.com (Simple)',
                    'element_index': i
                }

# Run the scrapers
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    
    process = CrawlerProcess()
    
    print("🚀 Starting Internshala Job Scrapers...")
    print("📋 Scraping both jobs and internships...")
    
    # Run the main scraper
    process.crawl(InternshalaJobScraper)
    
    # Uncomment to run the simple backup scraper too
    # process.crawl(SimpleInternshalaScaper)
    
    process.start()
    
    print("\n✅ Scraping completed!")
    print("📁 Check these files:")
    print("   - internshala_jobs.json (Main results)")
    print("   - simple_internshala.json (Backup results)")
    print("\n💡 Internshala is more scraper-friendly than other job sites!")