# README: Customer Feedback LLM

## 📝 Project Description

This project pulls customer feedback from JIRA (using a JQL query) and uploads a structured `.json` file into a specific folder on Google Drive. The output file can then be manually uploaded to tools like **NotebookLM** for query-based analysis.

### Problem it Solves
Product Managers need a streamlined way to query customer feedback without manually searching through Jira tickets.

### Target Users
Product Managers, Product Marketers, Product Owners, etc.

### Dependencies
I am a non-technical user who is not familiar with writing or hosting code. I will likely need to vibe code most of the functionality I need.

I also want to make this project as accessible to my team as possible, in the event that others need to contribute in the future. This means I do not want to host the code locally.

I have access to an Enterprise Github account, Enterprise Gemini account, Enterprise GPT account, JIRA, Slack, NotebookLM…etc. I may need to independently seek out vibe coding tools or other code-writing platforms.

## ✨ What It Does

- Authenticates with **JIRA Cloud** using API token
- Fetches all **Feature Request** issues from the `PFR` project using JQL
- Outputs a `jira_issues.json` file with relevant metadata
- Uploads the file to a **Google Drive folder** using a service account
- Compatible with **Shared Drives** and folder shortcuts
- Enables the Notebook LLM to query and analyze customer feedback.

## 🛠️ Prerequisites

* **Jira API Access:** A Jira account with access to the target service board and a Jira API Token.
* **Development Environment:** This project is built using Python 3.9 and hosted in a GitHub repository.
* **Google Drive folder** The folder must be shared with your service account email. You can find your folder ID by visiting the folder and copying the string after `/folders/` in the URL.

## 🚀 Setup & Installation

This project is configured to run automatically using **GitHub Actions**. Manual installation is not required for the automated workflow. To work with the code locally, follow these steps:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/isharman/customer-feedback.git](https://github.com/isharman/customer-feedback.git)
    cd customer-feedback
    ```
2.  **Install Dependencies:**
    * This project's dependencies are listed in `requirements.txt`.
    * To install them, run `pip install -r requirements.txt`.

## ⚙️ Configuration

* **Environment Variables & Security:** For security, you must **NEVER** commit your Jira API token to GitHub. Instead, your `JIRA_API_TOKEN` and `JIRA_EMAIL`, along with the `JIRA_SERVER_URL` and `GOOGLE_SERVICE_ACCOUNT_JSON`, are saved as **GitHub Secrets**.
* **Jira Server URL:** `https://yexttest.atlassian.net`
* **JQL Query:** The script uses the following JQL to fetch issues: `project = "PFR" AND issuetype = "Feature Request" ORDER BY created DESC`
* **Google Drive Folder ID:** The script requires the ID of the Google Drive folder where the `jira_issues.json` file will be uploaded. This is configured directly in the `jira_importer.py` script.

## How It Works

### 📤 Output

- The script writes a `jira_issues.json` file locally.
- That file is uploaded (or updated) into the target folder on Google Drive.
- Output format is clean, structured, and ready for import into tools like **NotebookLM**.

### 🏃 Usage

* **Automated Execution:** The script runs automatically every Monday at midnight UTC **GitHub Actions**. Example `cron` job is included in the workflow YAML (`.github/workflows/...`).
* **Manual Execution (for testing):** You can manually trigger the workflow from the **Actions** tab in your GitHub repository to run the script at any time.


### 📚 Fields Exported

Each JIRA issue includes:

- `key`
- `summary`
- `description`
- `reporter`
- `assignee`
- `created`
- `status`
- `product_area` (custom field)
- `idea_priority` (custom field)
- `workaround` (custom field)

### 🧠 Using with NotebookLM

Once the `.json` file is uploaded to Drive:

1. Open [notebooklm.google](https://notebooklm.google)
2. Create a new notebook
3. Add the Google Drive file as a source
4. Start asking questions!
