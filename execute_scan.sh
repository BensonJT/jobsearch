
conda activate jobsearch
python main.py --keywords "Chief of Staff, Director Operations, Operational Excellence, Business Transformation, Workforce Planning, Data Scientist, Six Sigma" --location "Remote" --days 14 --output output/job_leads_$(date +%Y%m%d).csv --db --new-only