from scrapy.crawler import CrawlerProcess
from core.spiders import FreshersworldJobScraper, InternshalaJobScraper

def run_all_spiders():
    process = CrawlerProcess()
    process.crawl(FreshersworldJobScraper)
    process.crawl(InternshalaJobScraper)
   
    process.start()

if __name__ == "__main__":
    run_all_spiders()
