import os
import json
import base64
from jira import JIRA, JIRAError
from dotenv import load_dotenv

# Google Drive API libraries
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload
import io

# --- 1. Functions for Google Drive API ---
def connect_to_google_drive():
    """Authenticates with Google Drive using a service account key from GitHub Secrets."""
    creds_json_string = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON")
    if not creds_json_string:
        raise ValueError("GOOGLE_DRIVE_CREDENTIALS_JSON secret not found.")

    # We load the JSON credentials from the environment variable
    creds_info = json.loads(creds_json_string)

    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)

    service = build('drive', 'v3', credentials=creds)
    print("Successfully connected to Google Drive API.")
    return service

def upload_to_google_drive(service, file_name, folder_id):
    """
    Uploads a file to a specific Google Drive folder.
    If a file with the same name exists, it will be updated.
    """

    # Check if the file already exists in the folder
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed = false"
    response = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
    existing_files = response.get('files', [])

    # Read the file content
    with open(file_name, 'rb') as f:
        file_content = f.read()

    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='application/json')

    if existing_files:
        # File exists, so update it
        file_id = existing_files[0]['id']
        print(f"File '{file_name}' found. Updating existing file with ID: {file_id}")
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print("File updated successfully.")
    else:
        # File does not exist, so create a new one
        print(f"File '{file_name}' not found. Creating a new file.")
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print("New file created successfully.")


# --- 2. Main script logic ---
def main():
    # Load environment variables from .env file (for local testing)
    load_dotenv()

    # Get credentials from environment variables
    jira_url = os.environ.get("JIRA_SERVER_URL")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_api_token = os.environ.get("JIRA_API_TOKEN")

    # Check if Jira credentials exist
    if not all([jira_url, jira_email, jira_api_token]):
        print("Error: Missing one or more JIRA environment variables.")
        print("Please set JIRA_SERVER_URL, JIRA_EMAIL, and JIRA_API_TOKEN.")
        return

    # Authenticate with the Jira API
    try:
        jira = JIRA(server=jira_url, basic_auth=(jira_email, jira_api_token))
        print("Successfully connected to Jira.")
    except Exception as e:
        print(f"Failed to connect to Jira. Error: {e}")
        return

    # Define and execute the JQL query
    jql_query = 'project = "PFR" AND issuetype = "Feature Request" ORDER BY created DESC'
    print(f"Searching for issues with JQL: {jql_query}")

    try:
        issues = jira.search_issues(jql_query, maxResults=None)
        print(f"Found {len(issues)} issues.")

        # Extract relevant data and store it in a list
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

        # Save the data to a local JSON file (temporary)
        local_file_name = 'jira_issues.json'
        with open(local_file_name, 'w', encoding='utf-8') as f:
            json.dump(issue_list, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved issues to {local_file_name}")

    except Exception as e:
        print(f"Failed to fetch issues. Error: {e}")
        return

    # --- 3. Google Drive Upload Logic ---
    try:
        drive_service = connect_to_google_drive()

        # Debugging: List all folders visible to the service account, including Shared Drives
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name, driveId, parents)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        print("Folders accessible to service account:")
        for folder in results.get('files', []):
            print(f"Name: {folder['name']}, ID: {folder['id']}, DriveID: {folder.get('driveId')}, Parents: {folder.get('parents')}")

        # This is the folder ID of the folder you created in Google Drive
        # Go to your folder in the browser. The ID is in the URL after 'folders/'
        google_drive_folder_id = "1wV6bAtXhoRmRskKDEx_SrE6oUuNz4-Jj"

        if google_drive_folder_id == "your_google_drive_folder_id_here":
            print("\nError: Please get your Google Drive folder ID and add it to the script.")
            return

        upload_to_google_drive(drive_service, local_file_name, google_drive_folder_id)

    except Exception as e:
        print(f"Failed to upload to Google Drive. Error: {e}")
        return

if __name__ == "__main__":
    main()
