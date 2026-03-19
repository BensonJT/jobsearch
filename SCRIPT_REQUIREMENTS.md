To architect a robust job search tool in 2026, we first need to identify which platforms still offer "open-door" policies for developers. Many major players (LinkedIn, Indeed) have moved behind strict partner paywalls, but several high-quality services remain accessible for a custom Python script.

### Phase 1: Free Job Search APIs (2026 Landscape)

Based on current developer terms, these are the most viable services for a free, automated job search script:

| Service       | Access Type         | Best For                  | Limits (Free Tier)        |
| :------------ | :------------------ | :------------------------ | :------------------------ |
| **Arbeitnow** | **Public (No Key)** | Europe & Remote (English) | Unlimited (Fair use)      |
| **Adzuna**    | **API Key**         | Global Aggregation        | 1,000 requests/month      |
| **Jooble**    | **API Key**         | Worldwide Reach           | ~500,000 requests/month   |
| **The Muse**  | **API Key**         | Tech & Company Culture    | Variable (Generous)       |
| **USAJobs**   | **API Key**         | US Government/Federal     | Restricted to US Gov data |
| **SerpApi**   | **API Key**         | **Google Jobs** results   | 100 searches/month        |

**Recommendation:** For a broad search, I suggest starting with **Adzuna** and **Arbeitnow**. Adzuna provides a deep global index, while Arbeitnow is the easiest to implement because it requires zero authentication.

---

### Phase 2: Application Architecture Specs
Since you intend to pass these specs to a CLI tool for generation, I have designed this with a **Modular, Service-Oriented Architecture**. This makes it easy to add or remove job boards without breaking the script.

#### 1. Technical Stack
* **Language:** Python 3.12+
* **Libraries:** * `httpx` or `requests`: For API calls.
    * `pydantic`: For data validation and standardizing job schemas.
    * `python-dotenv`: To manage API keys securely.
    * `pandas`: For exporting results to CSV/Excel.

#### 2. Class Structure
To keep the code clean, the application should follow this blueprint:

* **`JobModel` (Data Schema):** A Pydantic class that defines exactly what a "Job" looks like (Title, Company, Location, URL, Salary, Date Posted).
* **`BaseSource` (Abstract Class):** A template for all job boards. It ensures every board "adapter" has a `.search()` method.
* **`AdzunaSource` / `ArbeitnowSource`:** Concrete implementations that handle the specific URL structures and JSON parsing for each API.
* **`JobHarvester` (Orchestrator):** The main engine. It loops through all active "Sources," collects data, and merges them into one list.
* **`Deduplicator`:** A utility to remove identical listings (using the URL or a hash of Title+Company).

#### 3. Functional Logic Flow


1.  **Initialize:** Load API keys from `.env`.
2.  **Request:** The user inputs `keyword` (e.g., "Data Engineer") and `location`.
3.  **Dispatch:** The script sends concurrent requests to the selected APIs.
4.  **Normalize:** Converts varied JSON responses (Adzuna's `title` vs. Jooble's `job_title`) into the standard `JobModel`.
5.  **Filter:** Applies logic for "Remote only" or "Minimum Salary" if specified.
6.  **Output:** Saves a timestamped CSV and prints a summary to the console.

---

### Phase 3: Giving the Spec to the CLI
When you are ready to use the Google CLI/Gemini Code Assist, you can provide the following prompt:

> "Build a Python 3.12 script using the 'httpx' and 'pydantic' libraries. Implement a modular architecture where a 'Harvester' class manages multiple job board APIs (Adzuna and Arbeitnow). Standardize all results into a single Job dataclass. Include error handling for API timeouts and a function to export the final list to a CSV file named 'jobs_YYYYMMDD.csv'. Ensure API keys are loaded from an environment file."

**Would you like me to write the specific API endpoint URLs and JSON mapping logic for these boards so you can include that in your design specs?**

This information is exactly what the Google CLI (or any LLM-based code generator) needs to handle the "dirty work" of data normalization. By defining these mappings upfront, you ensure the AI doesn't hallucinate field names.

### Phase 1: API Endpoints & Authentication
Here are the specific endpoints and credential requirements for your primary sources as of early 2026.

| Provider          | Base URL / Endpoint                                                  | Auth Method          | Notes                                     |
| :---------------- | :------------------------------------------------------------------- | :------------------- | :---------------------------------------- |
| **Arbeitnow**     | `https://www.arbeitnow.com/api/job-board-api`                        | **None**             | No key needed. Great for testing.         |
| **Adzuna**        | `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}`         | `app_id` & `app_key` | Replace `{country}` with `us`, `gb`, etc. |
| **Jooble**        | `https://jooble.org/api/combined/{API_KEY}`                          | API Key in URL       | Requires a POST request with JSON body.   |
| **CareerOneStop** | `https://api.careeronestop.org/v1/jobsearch/{userId}/{kw}/{loc}/...` | API Key (Header)     | US Department of Labor data.              |

---

### Phase 2: Data Mapping Logic
To make your Python script "Universal," the Google CLI needs to map these varied JSON responses into a single standard format. 

| Standard Field | Adzuna Mapping                       | Arbeitnow Mapping      | Jooble Mapping    |
| :------------- | :----------------------------------- | :--------------------- | :---------------- |
| **Title**      | `result['title']`                    | `item['title']`        | `job['title']`    |
| **Company**    | `result['company']['display_name']`  | `item['company_name']` | `job['company']`  |
| **Location**   | `result['location']['display_name']` | `item['location']`     | `job['location']` |
| **Link**       | `result['redirect_url']`             | `item['url']`          | `job['link']`     |
| **Salary**     | `result.get('salary_min')`           | N/A (usually in desc)  | `job['salary']`   |

---

### Phase 3: The Design Specs for Google CLI
You can copy and paste the block below directly into your CLI or Gemini Code Assist interface. It provides the exact structural constraints required for a clean build.

> **System Design Specification: Multi-Source Job Harvester**
> 
> **1. Data Schema (Pydantic):**
> Create a `JobListing` model with: `title` (str), `company` (str), `location` (str), `url` (str), `source` (str), and `posted_at` (datetime).
> 
> **2. API Adapters:**
> * **ArbeitnowAdapter:** Perform a GET request. Map `title` to `title` and `url` to `url`. Access the list via the `data` key in JSON.
> * **AdzunaAdapter:** Perform a GET request with `app_id` and `app_key` as params. Map `company['display_name']` to `company`. Access list via `results` key.
> * **JoobleAdapter:** Perform a POST request. Send `{"keywords": "...", "location": "..."}` as JSON body. Access list via `jobs` key.
> 
> **3. Logic Flow:**
> * Create an `async` function `fetch_all_jobs(keyword, location)` that triggers all adapters concurrently using `asyncio.gather`.
> * Implement a deduplication check based on the `url` field.
> * Export results to a CSV using `pandas` or the built-in `csv` module.
> 
> **4. Error Handling:**
> Use try-except blocks for each API call so that if one service is down, the others still return data.

---

### Suggested Next Step
Would you like me to generate a **`.env` template** and the **`requirements.txt`** file so you have the environment ready before you run the CLI command?

To get your environment ready for the Google CLI or your local development, you’ll need these two foundational files. They ensure your credentials stay secure and your dependencies are locked in.

### 1. The `.env` Template
Create a file named `.env` in your project root. **Do not** share this file or commit it to GitHub, as it contains your private API keys.

```bash
# Adzuna API Credentials
# Get these at: https://developer.adzuna.com/
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here

# Jooble API Credentials
# Get these at: https://jooble.org/api-for-developers
JOOBLE_API_KEY=your_jooble_api_key_here

# CareerOneStop (Optional)
# Get these at: https://www.careeronestop.org/Developers/WebAPI/web-api.aspx
CAREERONESTOP_USER_ID=your_userid_here
CAREERONESTOP_API_KEY=your_api_key_here

# Application Settings
SEARCH_COUNTRY=us
DEFAULT_KEYWORDS="Data Scientist, Machine Learning Engineer"
```

---

### 2. The `requirements.txt` File
Create a file named `requirements.txt`. This tells the Python environment exactly which tools to install. I've included `httpx` for modern asynchronous requests and `pydantic` for the data modeling we discussed.

```text
httpx>=0.27.0
pydantic>=2.6.0
python-dotenv>=1.0.1
pandas>=2.2.0
asyncio>=3.4.3
```

---

### 3. Quick Setup Instructions
Before you run the script generated by the CLI, you (or the tool) will need to run the following command in your terminal to install everything:

```bash
pip install -r requirements.txt
```

### How this connects to the Google CLI
When you feed the design specs to the Google CLI, you can now add:
> "The script must use the `python-dotenv` library to load `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, and `JOOBLE_API_KEY` from a `.env` file. Ensure the `pydantic` models match the field types expected by the `pandas` export function."

**Since you're building this for active job searching, would you like me to draft a 'Filtering' logic spec that can automatically prioritize remote roles or jobs posted within the last 24 hours?**

Since your goal is to find **active** roles that actually fit your criteria, the filtering logic is the most critical part of the architecture. It prevents your CSV from being cluttered with "ghost jobs" or expired listings.

### Phase 4: Job Filtering & Prioritization Logic
Add this to your design specs for the Google CLI. It defines how the script should "think" when it evaluates a potential lead.

**1. Recency Filter (The "Freshness" Rule)**
* **Logic:** If `posted_at` is more than **7 days old**, discard or move to a "Backlog" sheet.
* **Why:** In the 2026 market, the highest response rates occur within the first 48 hours.

**2. Keyword "Must-Haves" vs. "Nice-to-Haves"**
* **Logic:** Perform a secondary scan of the `description` field (if available via API).
* **Action:** Tag roles as **"High Match"** if they contain specific tech stack keywords (e.g., "Python", "SQL", "LLM") and **"Low Match"** if they are missing more than two.

**3. Remote/Hybrid Detection**
* **Logic:** Scan the `location` and `description` fields for strings like `["Remote", "Telework", "Work from home", "Anywhere"]`.
* **Action:** Create a boolean `is_remote` column in your output.

---

### Revised CLI Instruction Block
You can now provide this complete "Master Prompt" to the Google CLI to build the full application:

> **Final Build Spec: Automated Job Intelligence Tool**
> 
> **Architecture:** Build a Python 3.12+ application using `httpx` for async requests and `pydantic` for data models.
> 
> **Sources:** Implement adapters for **Adzuna** (GET), **Arbeitnow** (GET), and **Jooble** (POST).
> 
> **Features:**
> 1. **Secure Config:** Load `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, and `JOOBLE_API_KEY` from a `.env` file using `python-dotenv`.
> 2. **Filtering Logic:** >    - Filter out any jobs posted > 7 days ago.
>    - Add a boolean flag `is_remote` if "Remote" appears in the location or title.
>    - Sort the final list by `posted_at` (newest first).
> 3. **Deduplication:** Remove duplicate listings based on a normalized `url` string.
> 4. **Output:** Export to a CSV named `job_leads_[DATE].csv`.
> 
> **Error Handling:** Wrap each API call in a `try-except` block to ensure a single API failure doesn't crash the entire search.

---

### Your Project Files Ready to Go
I've consolidated the environment files we discussed into one place for you to copy.

#### `.env` File
```bash
# Get keys at: developer.adzuna.com & jooble.org/api-for-developers
ADZUNA_APP_ID="your_id"
ADZUNA_APP_KEY="your_key"
JOOBLE_API_KEY="your_key"
```

#### `requirements.txt`
```text
httpx>=0.27.0
pydantic>=2.6.0
python-dotenv>=1.0.1
pandas>=2.2.0
```

<FollowUp label="Want me to help you draft the 'High Match' keyword list for your specific roles?" query="Help me draft a 'High Match' keyword list for Chief of Staff, Director of Business Ops, and Data Scientist roles to use in the filtering logic." />

Based on your career history as an "operator who codes" and the specific strategies outlined in your search strings, I have categorized these "High Match" keywords into three profiles. These lists are designed to be plugged into the filtering logic of your Python script to score and prioritize job leads.

### High Match Keyword Tiers

| Profile                             | Core "Hard" Keywords                                | Strategic "Context" Keywords                                                             |
| :---------------------------------- | :-------------------------------------------------- | :--------------------------------------------------------------------------------------- |
| **Chief of Staff / Ops Director**   | LSSBB, Lean Six Sigma, PMO, Business Transformation | Operating Rhythm, Stakeholder Management, Financial Governance, Strategic Planning       |
| **Data Scientist / Analytics**      | Python, SQL, GenAI, Machine Learning, ETL           | Workforce Analytics, Predictive Modeling, Ops Analytics, Decision Support                |
| **The "Sweet Spot" (Intersection)** | Workforce Planning, Capacity Management, Automation | Process Engineering, Resource Optimization, "Operator Who Codes", Digital Transformation |

---

### 1. Chief of Staff & Director of Business Operations
These keywords prioritize your 31-year tenure in business transformation and your ability to lead large-scale programs like the **IT Asset Lifecycle** reduction.

* **Primary Filter:** "Chief of Staff", "Director of Operations", "Business Transformation", "Operational Excellence".
* **Secondary "High Match" (Weights):** * **Process:** Lean Six Sigma Black Belt (LSSBB), DMAIC, ISO 9000, Continuous Improvement.
    * **Governance:** Financial Governance, FP&A Automation, Capital Budget Management ($30M+), Merger Synergy.
    * **Execution:** Change Management, Program Management Office (PMO), Executive Reporting, Strategy Deployment.

### 2. Data Scientist & Applied Analytics
Use these to filter for roles that value your technical stack (Python/SQL/GenAI) applied to real-world business problems rather than just theoretical modeling.

* **Primary Filter:** "Data Scientist", "Applied AI", "Analytics Manager", "Data Architect".
* **Secondary "High Match" (Weights):**
    * **Technical Stack:** Python (Pandas/Httpx), SQL (CTEs/Window Functions), GenAI (Prompt Engineering), NotebookLM, Gemini.
    * **Domain Specific:** Workforce Planning, Force-to-Load (F2L) Modeling, Capacity Analytics, Operational Data Engineering.
    * **Visualization/BI:** Grafana, Power BI, Tableau, Executive Dashboards.

### 3. Industry & Contextual "Boosters"
Given your location in **Lovettsville, VA**, and your target company watchlist, your script should "boost" roles containing these terms.

* **Defense/GovCon:** "Clearance", "Lockheed Martin", "Booz Allen Hamilton", "SAIC", "Leidos".
* **High-Comp Tech:** "CrowdStrike", "NVIDIA", "ServiceNow", "OpenAI", "Anthropic".
* **Location-Based:** "Remote", "Hybrid", "Northern Virginia", "DC Metro", "Nashville", "Franklin, TN".

---

### Implementation Snippet for your Python Script
When you give the design specs to the Google CLI, you can include this logic for the `Deduplicator` or `Scorer` class:

```python
# Logic for the CLI to implement
HIGH_MATCH_KEYWORDS = [
    "LSSBB", "Python", "Workforce Planning", "Chief of Staff", 
    "GenAI", "Business Transformation", "Capacity Management"
]

def calculate_match_score(description):
    score = 0
    for word in HIGH_MATCH_KEYWORDS:
        if word.lower() in description.lower():
            score += 1
    return score
```

**Would you like me to refine the Jooble or Adzuna API request parameters to specifically include these "Must-Have" strings in the initial search query?**

To maximize the accuracy of your search, we will refine the **API Request Parameters** so the search engines do the "heavy lifting" before the data even reaches your script.

### Phase 1: Refined API Search Strings
Based on your **LinkedIn Search Strings** and **Professional Bio**, here are the optimized query strings for the Adzuna and Jooble APIs. 

| Role Focus           | Adzuna `what` Parameter                     | Jooble `keywords` Parameter                   |
| :------------------- | :------------------------------------------ | :-------------------------------------------- |
| **Strategy & Ops**   | `"Chief of Staff" "Operational Excellence"` | `Chief of Staff OR "Business Transformation"` |
| **Data & Analytics** | `"Data Scientist" Python SQL GenAI`         | `Data Scientist AND (Python OR SQL)`          |
| **LSSBB Focus**      | `"Lean Six Sigma" Black Belt`               | `"LSSBB" OR "Lean Six Sigma"`                 |
| **High Growth AI**   | `"GenAI" "Operations" Strategy`             | `AI Operations OR "Machine Learning"`         |

---

### Phase 2: Implementation Design for Google CLI
You should add this specific logic to your "Master Prompt" for the CLI. It ensures the script uses the correct API syntax for **Adzuna (GET)** and **Jooble (POST)**.

#### Adzuna Adapter Logic
* **Endpoint:** `https://api.adzuna.com/v1/api/jobs/us/search/1`
* **Query Params:**
    * `what`: Use phrases in quotes (e.g., `"Chief of Staff"`).
    * `where`: Set to `"Remote"` or `"Northern Virginia"` based on your preferences.
    * `results_per_page`: Set to `50` to maximize the free tier.
    * `sort_by`: Set to `"date"` to ensure you get the most active roles first.

#### Jooble Adapter Logic
* **Endpoint:** `https://jooble.org/api/combined/{API_KEY}`
* **Request Body (JSON):**
    ```json
    {
      "keywords": "Chief of Staff OR 'Operational Excellence'",
      "location": "Remote",
      "salary": 150000,
      "page": 1
    }
    ```
* **Note:** Jooble supports simple Boolean operators like `OR` and `AND` directly in the `keywords` string.

---

### Phase 3: High-Match Filtering Logic
Once the results are pulled, the script will apply these "Booster" terms from your target company watchlist.

**The Script should prioritize results containing:**
* **Tier 1 Tech:** NVIDIA, OpenAI, Anthropic, ServiceNow, Microsoft.
* **Target Financials:** Mastercard, Capital One, JPMorgan Chase.
* **Defense (NoVa Corridor):** Booz Allen Hamilton, Leidos, Lockheed Martin.
* **Key Identity Terms:** "Operator who codes", "Workforce Planning", "Capacity Management".

---

### Final "Precision" Instruction for the CLI
Add this to your prompt to ensure the final CSV is actionable:

> "In the final output CSV, create a **MatchScore** column. Add +5 points if the company is in the 'Tier 1' watchlist, +3 points if 'Python' or 'LSSBB' is in the description, and +10 points if the job was posted in the last 48 hours. Sort the final CSV by this **MatchScore**."

**Would you like me to generate the final, all-in-one 'Master Prompt' that you can copy and paste directly into the Google CLI now?**