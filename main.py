import asyncio
import argparse
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from backend.models import SearchConfig
from backend.harvester import JobHarvester
from backend.processor import JobProcessor
from backend.database import ensure_schema, upsert_listings, get_new_listings

async def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Multi-Source Job Harvester")
    parser.add_argument("--keywords", type=str, required=True, help="Job search keywords")
    parser.add_argument("--location", type=str, default="Remote", help="Job search location")
    parser.add_argument("--days", type=int, default=7, help="Recency limit in days")
    parser.add_argument("--output", type=str, help="Output CSV filename")
    parser.add_argument("--db", action="store_true", help="Write results to PostgreSQL database")
    parser.add_argument("--new-only", action="store_true", help="Only show/export listings with status=new from DB")
    
    args = parser.parse_args()

    if args.new_only and not args.db:
        print("Warning: --new-only requires --db. Database access is needed to filter by status.")
        args.db = True

    config = SearchConfig(
        keywords=args.keywords,
        location=args.location,
        days_limit=args.days
    )

    if args.db:
        print("Ensuring database schema exists...")
        ensure_schema()

    print(f"Starting harvest for: '{config.keywords}' in '{config.location}' (last {config.days_limit} days)...")
    
    harvester = JobHarvester()
    raw_listings = await harvester.fetch_all(config)
    
    print(f"Total raw listings found: {len(raw_listings)}")
    
    processed_listings = JobProcessor.process(raw_listings, config)
    
    print(f"Total processed listings: {len(processed_listings)}")

    if args.db:
        print(f"Upserting {len(processed_listings)} listings to database...")
        upsert_listings(processed_listings, config.keywords)
        
    if not processed_listings and not args.new_only:
        print("No job listings found matching the criteria.")
        return

    # Prepare for export
    export_data = []
    
    if args.new_only:
        print("Fetching ONLY 'new' listings from database...")
        db_listings = get_new_listings()
        print(f"Found {len(db_listings)} new listings in database.")
        for row in db_listings:
            export_data.append({
                "MatchScore": row["match_score"],
                "Title": row["title"],
                "Company": row["company"],
                "Location": row["location"],
                "PostedAt": row["posted_at"].strftime("%Y-%m-%d") if row["posted_at"] else "Unknown",
                "IsRemote": row["is_remote"],
                "URL": row["url"],
                "Source": row["source"],
                "Status": row["status"]
            })
    else:
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

    if not export_data:
        print("No data to export.")
        return

    df = pd.DataFrame(export_data)
    
    # Generate filename if not provided
    filename = args.output if args.output else f"job_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"Successfully exported {len(export_data)} jobs to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
