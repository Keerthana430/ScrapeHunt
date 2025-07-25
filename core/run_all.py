from core.spiders import FreshersworldJobScraper, InternshalaJobScraper
from core.spiders.linkedIn_jobs import main as run_linkedin_scraper
from core.spiders.Shine_jobs import main as FastShineSeleniumScraper
from core.spiders.TimesJobs_jobs import main as run_timesjobs_scraper
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_scrapy_spiders():
    process = CrawlerProcess(get_project_settings())
    process.crawl(FreshersworldJobScraper)
    process.crawl(InternshalaJobScraper)
    process.start()

def run_selenium_scrapers():
    run_linkedin_scraper()
    FastShineSeleniumScraper()
    run_timesjobs_scraper()

if __name__ == "__main__":
    run_scrapy_spiders()
    run_selenium_scrapers()
