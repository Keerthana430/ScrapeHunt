import requests, json
from datetime import datetime, timezone

def scrape_posts(limit=1000):
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

        with open("jobs.json", "w") as f:
            json.dump(jobs, f, indent=2)

        print(f"✅ Scraped and saved {len(jobs)} jobs to jobs.json")

    except Exception as e:
        print("❌ Error while scraping:", e)

if __name__ == "__main__":
    scrape_posts(limit=40)
