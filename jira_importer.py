import os
import json
from jira import JIRA
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()

    # 1. Get credentials from environment variables
    jira_url = os.environ.get("JIRA_SERVER_URL")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_api_token = os.environ.get("JIRA_API_TOKEN")

    # 2. Check if credentials exist
    if not all([jira_url, jira_email, jira_api_token]):
        print("Error: Missing one or more environment variables.")
        print("Please set JIRA_SERVER_URL, JIRA_EMAIL, and JIRA_API_TOKEN.")
        return

    # 3. Authenticate with the Jira API
    try:
        jira = JIRA(server=jira_url, basic_auth=(jira_email, jira_api_token))
        print("Successfully connected to Jira.")
    except Exception as e:
        print(f"Failed to connect to Jira. Error: {e}")
        return

    # 4. Define and execute the JQL query
    jql_query = 'project = "PFR" AND issuetype = "Feature Request" ORDER BY created DESC'
    print(f"Searching for issues with JQL: {jql_query}")

    try:
        issues = jira.search_issues(jql_query, maxResults=None)
        print(f"Found {len(issues)} issues.")

        # 5. Extract relevant data and store it in a list
        issue_list = []
        for issue in issues:
            issue_data = {
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': issue.fields.description if hasattr(issue.fields, 'description') else None,
                'reporter': issue.fields.reporter.displayName if issue.fields.reporter else None,
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
                'created': issue.fields.created,
                'status': issue.fields.status.name,
                'product_area': issue.fields.customfield_17591.value if hasattr(issue.fields, 'customfield_17591') and issue.fields.customfield_17591 else None,
                'idea_priority': issue.fields.customfield_17636.value if hasattr(issue.fields, 'customfield_17636') and issue.fields.customfield_17636 else None,
                'workaround': issue.fields.customfield_14707 if hasattr(issue.fields, 'customfield_14707') else None,
            }
            issue_list.append(issue_data)

        # 6. Save the data to a JSON file
        with open('jira_issues.json', 'w', encoding='utf-8') as f:
            json.dump(issue_list, f, ensure_ascii=False, indent=4)
        print("Successfully saved issues to jira_issues.json")

    except Exception as e:
        print(f"Failed to fetch issues. Error: {e}")
        return

if __name__ == "__main__":
    main()