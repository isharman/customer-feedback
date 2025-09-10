import os
import json
import requests
from jira import JIRA
from dotenv import load_dotenv
from datetime import datetime

# ----- PyDrive2 / Google Auth -----
from google.oauth2 import service_account
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# =========================
# Google Drive (PyDrive2)
# =========================
def login_with_service_account():
    settings = {
        "client_config_backend": "service",
        "service_config": {
            "client_json_file_path": "service_account.json",
        }
    }
    gauth = GoogleAuth(settings=settings)
    gauth.ServiceAuth()
    return gauth

def _get_file_metadata(drive: GoogleDrive, file_id: str, fields: str = "id, name, mimeType, driveId, parents, shortcutDetails"):
    return drive.auth.service.files().get(
        fileId=file_id,
        fields=fields,
        supportsAllDrives=True,
    ).execute()

def validate_and_resolve_folder_id(drive: GoogleDrive, folder_id: str) -> str:
    try:
        meta = _get_file_metadata(drive, folder_id)
    except Exception as e:
        raise ValueError(
            f"Folder not found or not shared with the service account. "
            f"Double-check the ID and permissions for '{folder_id}'."
        ) from e

    mime_type = meta.get("mimeType")
    if mime_type == "application/vnd.google-apps.shortcut":
        target_id = meta.get("shortcutDetails", {}).get("targetId")
        if not target_id:
            raise ValueError("Provided ID is a shortcut but targetId is missing.")
        print(f"Provided folder ID is a shortcut. Using target folder ID: {target_id}")
        meta = _get_file_metadata(drive, target_id)
        mime_type = meta.get("mimeType")
        folder_id = target_id

    if mime_type != "application/vnd.google-apps.folder":
        raise ValueError(f"ID '{folder_id}' is not a folder (mimeType={mime_type}).")

    return folder_id

def upload_to_google_drive(drive: GoogleDrive, file_path: str, folder_id: str):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Local file not found: {file_path}")

    file_name = os.path.basename(file_path)
    query = f"title = '{file_name}' and '{folder_id}' in parents and trashed = false"
    existing = drive.ListFile({
        "q": query,
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True
    }).GetList()

    if existing:
        f = existing[0]
        print(f"File '{file_name}' exists. Updating ID: {f['id']}")
        f.SetContentFile(file_path)
        f.Upload(param={"supportsAllDrives": True})
        print("File updated successfully.")
        return f["id"]
    else:
        print(f"File '{file_name}' not found. Creating new file in folder {folder_id}.")
        f = drive.CreateFile({
            "title": file_name,
            "parents": [{"id": folder_id}]
        })
        f.SetContentFile(file_path)
        f.Upload(param={"supportsAllDrives": True})
        print("New file created successfully. ID:", f["id"])
        return f["id"]

# =========================
# Jira -> JSON + TXT export
# =========================
def export_jira_data(jira_url: str, jira_email: str, jira_api_token: str, jql_query: str, json_path: str, txt_path: str):
    print("Authenticating with Jira Cloud REST API v3...")
    api_url = f"{jira_url}/rest/api/3/search"
    headers = {
        "Accept": "application/json"
    }

    params = {
    "jql": jql_query,
    "maxResults": 1000,
    "fields": "summary,description,reporter,assignee,created,status,customfield_17591,customfield_17636,customfield_14707"
    }

    try:
        response = requests.get(api_url, headers=headers, auth=(jira_email, jira_api_token), params=params)
        
        print(f"🔎 Final URL: {response.url}")
        print(f"🔁 Status code: {response.status_code}")
        print(f"🔍 Raw text: {response.text[:500]}")  # ← optional preview
        
        response.raise_for_status()
        data = response.json()
        print(f"Found {data['total']} issues.")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch issues: {e}") from e

    issue_list = []
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        issue_data = {
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "description": fields.get("description"),
            "reporter": fields.get("reporter", {}).get("displayName"),
            "assignee": fields.get("assignee", {}).get("displayName"),
            "created": fields.get("created"),
            "status": fields.get("status", {}).get("name"),
            "product_area": fields.get("customfield_17591", {}).get("value") if fields.get("customfield_17591") else None,
            "idea_priority": fields.get("customfield_17636", {}).get("value") if fields.get("customfield_17636") else None,
            "workaround": fields.get("customfield_14707"),
        }
        issue_list.append(issue_data)

    last_updated = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
    output_data = {
        "last_updated": last_updated,
        "issues": issue_list
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved JSON to {json_path}")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Last updated: {last_updated}\n\n")
        for issue in issue_list:
            f.write(f"{issue['key']}: {issue['summary']}\n")
            f.write(f"Status: {issue['status']}\n")
            f.write(f"Product Area: {issue['product_area']}\n")
            f.write(f"Priority: {issue['idea_priority']}\n")
            f.write(f"Reporter: {issue['reporter']}\n")
            f.write(f"Assignee: {issue['assignee']}\n")
            f.write(f"Created: {issue['created']}\n")
            f.write(f"Description:\n{issue['description']}\n")
            f.write(f"Workaround:\n{issue['workaround']}\n")
            f.write("----------------------------------------\n\n")
    print(f"Successfully saved TXT to {txt_path}")

# =========================
# Main
# =========================
def main():
    load_dotenv()

    jira_url = os.environ.get("JIRA_SERVER_URL")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_api_token = os.environ.get("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_api_token]):
        print("Error: Missing one or more JIRA env vars: JIRA_SERVER_URL, JIRA_EMAIL, JIRA_API_TOKEN")
        return

    service_account_json_content = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json_content:
        print("Error: GOOGLE_SERVICE_ACCOUNT_JSON secret not found.")
        return
    with open("service_account.json", "w") as f:
        f.write(service_account_json_content)

    jql_query = 'project = "PFR" AND issuetype = "Feature Request" ORDER BY created DESC'
    json_file = "jira_issues.json"
    txt_file = "jira_issues.txt"
    try:
        export_jira_data(jira_url, jira_email, jira_api_token, jql_query, json_file, txt_file)
    except Exception as e:
        print(e)
        return

    try:
        gauth = login_with_service_account()
    except Exception as e:
        print(f"Failed to authenticate to Google Drive. Error: {e}")
        return
    drive = GoogleDrive(gauth)

    folder_id = '1ZqgKiDwkYiLpKt5NLKKDOOzZrhfBCuCP'
    try:
        upload_to_google_drive(drive, txt_file, folder_id)
    except Exception as e:
        print(f"Failed to upload to Google Drive. Error: {e}")
        return

if __name__ == "__main__":
    main()
