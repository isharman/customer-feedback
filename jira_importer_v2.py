#!/usr/bin/env python3
import os
import json
from jira import JIRA
from dotenv import load_dotenv

# ----- PyDrive2 / Google Auth -----
from google.oauth2 import service_account
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


# =========================
# Google Drive (PyDrive2)
# =========================
def login_with_service_account():
    """
    Google Drive service with a service account.
    note: for the service account to work, you need to share the folder or
    files with the service account email.

    :return: google auth
    """
    # Define the settings dict to use a service account
    # We also can use all options available for the settings dict like
    # oauth_scope,save_credentials,etc.
    settings = {
                "client_config_backend": "service",
                "service_config": {
                    "client_json_file_path": "service_account.json",
                }
            }
    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth


def _get_file_metadata(drive: GoogleDrive, file_id: str, fields: str = "id, name, mimeType, driveId, parents, shortcutDetails"):
    """
    Low-level helper to fetch file metadata using the underlying Drive v3 API client exposed by PyDrive2.
    """
    return drive.auth.service.files().get(
        fileId=file_id,
        fields=fields,
        supportsAllDrives=True,
    ).execute()


def validate_and_resolve_folder_id(drive: GoogleDrive, folder_id: str) -> str:
    """
    Validates that folder_id is visible to the service account and resolves shortcuts.
    Returns a proper folder ID (target if the given ID is a shortcut).
    Raises ValueError if not found or not a folder.
    """
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
    """
    Uploads a file to a specific Google Drive folder (Shared Drives supported).
    If a file with the same name exists in that folder, it will be updated.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Local file not found: {file_path}")

    # Validate folder and resolve shortcut if needed
    folder_id = validate_and_resolve_folder_id(drive, folder_id)

    file_name = os.path.basename(file_path)

    # Find existing file by name inside the folder
    query = f"title = '{file_name}' and '{folder_id}' in parents and trashed = false"
    existing = drive.ListFile({
        "q": query,
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True
    }).GetList()

    if existing:
        # Update existing file
        f = existing[0]
        print(f"File '{file_name}' exists. Updating ID: {f['id']}")
        f.SetContentFile(file_path)
        f.Upload(param={"supportsAllDrives": True})
        print("File updated successfully.")
        return f["id"]
    else:
        # Create new file in folder
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
# Jira -> JSON export
# =========================
def export_jira_to_json(jira_url: str, jira_email: str, jira_api_token: str, jql_query: str, out_path: str) -> str:
    """
    Queries Jira with the given JQL and writes results to out_path as JSON.
    Returns the output path.
    """
    try:
        jira = JIRA(server=jira_url, basic_auth=(jira_email, jira_api_token))
        print("Successfully connected to Jira.")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Jira: {e}") from e

    print(f"Searching for issues with JQL: {jql_query}")

    try:
        issues = jira.search_issues(jql_query, maxResults=None)
        print(f"Found {len(issues)} issues.")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch issues: {e}") from e

    # Extract relevant fields
    issue_list = []
    for issue in issues:
        fields = issue.fields
        issue_data = {
            "key": issue.key,
            "summary": getattr(fields, "summary", None),
            "description": getattr(fields, "description", None),
            "reporter": fields.reporter.displayName if getattr(fields, "reporter", None) else None,
            "assignee": fields.assignee.displayName if getattr(fields, "assignee", None) else None,
            "created": getattr(fields, "created", None),
            "status": fields.status.name if getattr(fields, "status", None) else None,
            # custom fields (keep as in your original code)
            "product_area": (getattr(fields, "customfield_17591", None).value
                             if getattr(fields, "customfield_17591", None) else None),
            "idea_priority": (getattr(fields, "customfield_17636", None).value
                              if getattr(fields, "customfield_17636", None) else None),
            "workaround": getattr(fields, "customfield_14707", None),
        }
        issue_list.append(issue_data)

    # Write to JSON
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(issue_list, f, ensure_ascii=False, indent=4)

    print(f"Successfully saved issues to {out_path}")
    return out_path


# =========================
# Main
# =========================
def main():
    # Load environment variables for local dev
    load_dotenv()

    # Jira env vars
    jira_url = os.environ.get("JIRA_SERVER_URL")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_api_token = os.environ.get("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_api_token]):
        print("Error: Missing one or more JIRA env vars: JIRA_SERVER_URL, JIRA_EMAIL, JIRA_API_TOKEN")
        return

    # 1) Export from Jira to local JSON
    jql_query = 'project = "PFR" AND issuetype = "Feature Request" ORDER BY created DESC'
    local_file_name = "jira_issues.json"
    try:
        export_jira_to_json(jira_url, jira_email, jira_api_token, jql_query, local_file_name)
    except Exception as e:
        print(e)
        return

    # 2) Connect to Google Drive (PyDrive2)
    try:
        yes = login_with_service_account()
    except Exception as e:
        print(f"Failed to authenticate to Google Drive. Error: {e}")
        return
    drive = GoogleDrive(yes)
    # Optional: list some folders visible to the service account (debug)
    try:
        folders = drive.ListFile({
            "q": "mimeType='application/vnd.google-apps.folder' and trashed = false",
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True
        }).GetList()
        print("Folders accessible to service account:")
        for folder in folders:
            print(f" - {folder.get('title')} (ID: {folder.get('id')})")
    except Exception as e:
        print(f"Warning: failed to list folders: {e}")

    # 3) Upload/Update JSON into your target folder (Shared Drive/folder must be shared with the SA)
    folder_id = '1ZqgKiDwkYiLpKt5NLKKDOOzZrhfBCuCP' # Replace with the actual folder ID
    file_path = local_file_name # Replace with the actual path to your local file

    # Create a GoogleDriveFile instance, specifying the parent folder
    file_to_upload = drive.CreateFile({'parents': [{'id': folder_id}]})

    # Set the content of the file from your local file
    file_to_upload.SetContentFile(file_path)

    # Upload the file
    try:
        file_to_upload.Upload()
    except Exception as e:
        print(f"Failed to upload to Google Drive. Error: {e}")
        return
    print(f"Uploaded file '{file_to_upload['title']}' to folder ID '{folder_id}'")

if __name__ == "__main__":
    main()
