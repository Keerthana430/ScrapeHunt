import requests, json
from datetime import datetime, timezone
import feedparser

def scrape_post_remoteOk(limit=1000):
    url = "https://remoteok.io/api"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()[1:]  # skip metadata

        jobs = []
        for job in data[:limit]:
            jobs.append({
                "jobid": str(job.get("id")),
                "jobtitle": job.get("title") or job.get("position"),
                "company": job.get("company"),
                "location": job.get("location"),
                "type": job.get("type"), 
                "salary": None,  # not in API
                "posted-date":  (
                    datetime.fromisoformat(job.get("date")).date().isoformat()
                    if job.get("date") else None
                ),
                "description": None,  # not in API
                "job-link": job.get("url"),
                "source": "remoteok.io",
                "tags": job.get("tags") or [],
                "scrapedAt": datetime.now(timezone.utc).date().isoformat(),
                "isActive": True,
                "remote": "remote" in (job.get("tags") or []),
                "qualification": None,  # not in API
            })

        with open("jsonFiles/remoteok_jobs.json", "w") as f:
            json.dump(jobs, f, indent=2)

        print(f"✅ Scraped and saved {len(jobs)} jobs to jobs.json")

    except Exception as e:
        print("❌ Error while scraping:", e)


def scrape_post_arbeitnow(limit=1000): 
    url = "https://www.arbeitnow.com/api/job-board-api"
    headers = {"User-Agent": "Mozilla/5.0"}

    try: 
        res = requests.get(url, headers=headers, timeout=10 )
        res.raise_for_status()
        data = res.json().get("data", [])  

        jobs = []
        for idx, job in enumerate(data[:limit]):
            jobs.append({
                "jobid": f"arbeitnow-{idx}",  # Unique fallback ID
                "jobtitle": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("location") or job.get("candidate_required_location"),
                "type": job.get("job_type"), 
                "salary": job.get("salary"),
                "posted-date": (
                    datetime.fromisoformat(job.get("publication_date")).date().isoformat()
                    if job.get("publication_date") else None
                ),
                "description": job.get("description"),
                "job-link": job.get("url"),
                "source": "arbeitnow.com",
                "tags": job.get("tags") or [],
                "scrapedAt": datetime.now(timezone.utc).date().isoformat(),
                "isActive": True,
                "remote": "remote" in (job.get("tags") or []),
                "qualification": None,
            })

        with open("jsonFiles/arbeitnow_jobs.json", "w") as f:
            json.dump(jobs, f, indent=2)

        print(f"✅ Scraped and saved {len(jobs)} jobs to arbeitnow_jobs.json")

    except Exception as e:
        print("❌ Error while scraping Arbeitnow:", e)


def scrape_python_jobs(limit=1000):
    url = "https://www.python.org/jobs/feed/rss/"
    feed = feedparser.parse(url)
    jobs = []

    for entry in feed.entries[:limit]:
        jobs.append({
            "jobid": entry.get("id") or entry.get("link"),
            "jobtitle": entry.get("title"),
            "company": entry.get("author", None),
            "location": None,
            "type": None,
            "salary": None,
            "posted-date": (
                datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).date().isoformat()
                if hasattr(entry, "published_parsed") else None
            ),
            "description": entry.get("summary"),
            "job-link": entry.get("link"),
            "source": "python.org",
            "tags": [],
            "scrapedAt": datetime.now(timezone.utc).date().isoformat(),
            "isActive": True,
            "remote": True,
            "qualification": None
        })

    with open("jsonFiles/pythonorg_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"✅ Scraped and saved {len(jobs)} jobs to pythonorg_jobs.json")

def scrape_remote_python(limit=1000):
    url = "https://www.remotepython.com/latest/jobs/feed/"
    feed = feedparser.parse(url)
    jobs = []

    for entry in feed.entries[:limit]:
        jobs.append({
            "jobid": entry.get("id") or entry.get("link"),
            "jobtitle": entry.get("title"),
            "company": entry.get("author", None),
            "location": None,
            "type": None,
            "salary": None,
            "posted-date": (
                datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        .date().isoformat()
                if hasattr(entry, "published_parsed") else None
            ),
            "description": entry.get("summary"),
            "job-link": entry.get("link"),
            "source": "remotepython.com",
            "tags": [],
            "scrapedAt": datetime.now(timezone.utc).date().isoformat(),
            "isActive": True,
            "remote": True,
            "qualification": None
        })

    with open("jsonFiles/remotepython_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"✅ Scraped and saved {len(jobs)} jobs to remotepython_jobs.json")


def scrape_weworkremotely(limit=1000):
    url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    feed = feedparser.parse(url)
    jobs = []

    for entry in feed.entries[:limit]:
        jobs.append({
            "jobid": entry.get("id") or entry.get("link"),
            "jobtitle": entry.get("title"),
            "company": entry.get("author") if "author" in entry else None,
            "location": None,
            "type": None,
            "salary": None,
            "posted-date": (
                datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).date().isoformat()
                if "published_parsed" in entry else None
            ),
            "description": entry.get("summary"),
            "job-link": entry.get("link"),
            "source": "weworkremotely",
            "tags": [],
            "scrapedAt": datetime.now(timezone.utc).date().isoformat(),
            "isActive": True,
            "remote": True,
            "qualification": None
        })

    with open("jsonFiles/weworkremotely_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"✅ Scraped and saved {len(jobs)} jobs to weworkremotely_jobs.json")



if __name__ == "__main__":
    scrape_post_remoteOk(limit=100)
    scrape_post_arbeitnow(limit=100)
    scrape_weworkremotely(limit=100)
    scrape_python_jobs(limit=100)
    scrape_remote_python(limit=100)
