# README: Customer Feedback LLM

## 📝 Project Description

### Goal
To automatically pull customer feedback and feature requests from a Jira Service Board and make the data available for a Notebook LLM, Slackbot, or other easily queryable tool.

### Problem it Solves
Product Managers need a streamlined way to query customer feedback without manually searching through Jira tickets.

### Target Users
Product Managers, Product Marketers, Product Owners, etc.

### Long Description
I am trying to create some sort of app or tool that will enable product managers at my organization to query for customer feedback. I'm not sure yet of the best or easiest way to surface the data for querying (NotebookLM, Slackbot, web app, etc.) I am a non-technical user who is not familiar with writing or hosting code. I will likely need to vibe code most of the functionality I need.

I also want to make this project as accessible to my team as possible, in the event that others need to contribute in the future. This means I do not want to “host” the code locally.

I have access to an Enterprise Github account, Enterprise Gemini account, JIRA, Slack, NotebookLM…etc. I may need to independently seek out vibe coding tools or other code-writing platforms.

## ✨ Features

* Automated fetching of Jira issues based on a specific query (e.g. “How many requests have we received for mobile functionality?”).
* Converts Jira issues into a structured format (e.g., JSON).
* Enables the Notebook LLM to query and analyze customer feedback.

## 🛠️ Prerequisites

* **Jira API Access:** A Jira account with access to the target service board and a Jira API Token.
* **Development Environment:** This project is built using Python 3.9 and hosted in a GitHub repository.

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

* **Environment Variables & Security:** For security, you must **NEVER** commit your Jira API token to GitHub. Instead, your `JIRA_API_TOKEN` and `JIRA_EMAIL`, along with the `JIRA_SERVER_URL` and `GOOGLE_DRIVE_CREDENTIALS_JSON`, are saved as **GitHub Secrets**.
* **Jira Server URL:** `https://yexttest.atlassian.net`
* **JQL Query:** The script uses the following JQL to fetch issues: `project = "PFR" AND issuetype = "Feature Request" ORDER BY created DESC`
* **Google Drive Folder ID:** The script requires the ID of the Google Drive folder where the `jira_issues.json` file will be uploaded. This is configured directly in the `jira_importer.py` script.

## 🏃 Usage

* **Automated Execution:** The script runs automatically once every 24 hours on the GitHub Actions platform.
* **Manual Execution (for testing):** You can manually trigger the workflow from the **Actions** tab in your GitHub repository to run the script at any time.

## How It Works

* The workflow in your GitHub repository executes on a schedule.
* It uses your securely stored
