import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service(credentials_path="credentials.json", token_path="token.json"):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"{credentials_path} not found. Please provide Google API credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_receipt_emails(service, query="label:inbox"):
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    return messages


def download_attachment(service, msg_id, attachment_id, filename):
    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=msg_id, id=attachment_id)
        .execute()
    )
    data = attachment.get("data")
    if data:
        file_data = base64.urlsafe_b64decode(data)
        path = os.path.join("attachments", filename)
        os.makedirs("attachments", exist_ok=True)
        with open(path, "wb") as f:
            f.write(file_data)
        return path
    return None


def process_emails(service, keywords=["квитанція", "receipt", "платіж"]):
    query = " OR ".join(keywords)
    messages = fetch_receipt_emails(service, query=query)

    downloaded_files = []

    for msg in messages:
        message = service.users().messages().get(userId="me", id=msg["id"]).execute()
        parts = message.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("filename"):
                attachment_id = part["body"].get("attachmentId")
                if attachment_id:
                    # Use unique filename to prevent overwrites
                    unique_filename = f"{msg['id'][:8]}_{part['filename']}"
                    path = os.path.join("attachments", unique_filename)
                    
                    if os.path.exists(path):
                        downloaded_files.append(path)
                        continue

                    path = download_attachment(
                        service, msg["id"], attachment_id, unique_filename
                    )

                    if path:
                        downloaded_files.append(path)
    return downloaded_files
