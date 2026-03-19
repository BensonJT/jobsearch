import asyncio
import argparse
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from backend.models import SearchConfig
from backend.harvester import JobHarvester
from backend.processor import JobProcessor

async def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Multi-Source Job Harvester")
    parser.add_argument("--keywords", type=str, required=True, help="Job search keywords")
    parser.add_argument("--location", type=str, default="Remote", help="Job search location")
    parser.add_argument("--days", type=int, default=7, help="Recency limit in days")
    parser.add_argument("--output", type=str, help="Output CSV filename")
    
    args = parser.parse_args()

    config = SearchConfig(
        keywords=args.keywords,
        location=args.location,
        days_limit=args.days
    )

    print(f"Starting harvest for: '{config.keywords}' in '{config.location}' (last {config.days_limit} days)...")
    
    harvester = JobHarvester()
    raw_listings = await harvester.fetch_all(config)
    
    print(f"Total raw listings found: {len(raw_listings)}")
    
    processed_listings = JobProcessor.process(raw_listings, config)
    
    print(f"Total processed listings: {len(processed_listings)}")

    if not processed_listings:
        print("No job listings found matching the criteria.")
        return

    # Prepare for export
    export_data = []
    for job in processed_listings:
        export_data.append({
            "MatchScore": job.match_score,
            "Title": job.title,
            "Company": job.company,
            "Location": job.location,
            "PostedAt": job.posted_at.strftime("%Y-%m-%d"),
            "IsRemote": job.is_remote,
            "URL": job.url,
            "Source": job.source,
            "Tags": ", ".join(job.tags)
        })

    df = pd.DataFrame(export_data)
    
    # Generate filename if not provided
    filename = args.output if args.output else f"job_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"Successfully exported {len(processed_listings)} jobs to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
