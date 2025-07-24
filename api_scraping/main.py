import requests, json

def scrape_posts(limit=1000):
    url = "https://remoteok.io/api"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()[1:]  # skip metadata

        jobs = [
            {
                "company": job.get("company"),
                "position": job.get("position"),
                "url": job.get("url"),
                "location": job.get("location")
            }
            for job in data[:limit]
        ]

        with open("jobs.json", "w") as f:
            json.dump(jobs, f, indent=2)

        print(f"✅ Scraped and saved {len(jobs)} jobs to jobs.json")
    
    except Exception as e:
        print("❌ Error while scraping:", e)

if __name__ == "__main__":
    scrape_posts(limit=10)
