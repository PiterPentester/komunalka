import os
import logging
from nylas import Client
from dotenv import load_dotenv

load_dotenv()

NYLAS_API_KEY = os.environ.get("NYLAS_API_KEY")
NYLAS_API_URI = os.environ.get("NYLAS_API_URI", "https://api.us.nylas.com")
NYLAS_GRANT_ID = os.environ.get("NYLAS_GRANT_ID")


def get_nylas_client():
    if not NYLAS_API_KEY:
        raise ValueError("NYLAS_API_KEY not found in environment variables.")
    return Client(api_key=NYLAS_API_KEY, api_uri=NYLAS_API_URI)


def fetch_receipt_messages(client, grant_id, query):
    # In Nylas v3 Python SDK (v6.x), list() returns a ListResponseObject
    response = client.messages.list(
        grant_id, query_params={"search_query_native": query}
    )
    return response.data


def download_nylas_attachment(client, grant_id, attachment_id, message_id, filename):
    try:
        # download_bytes returns the raw byte array in v3
        attachment_bytes = client.attachments.download_bytes(
            grant_id, attachment_id, query_params={"message_id": message_id}
        )

        path = os.path.join("attachments", filename)
        os.makedirs("attachments", exist_ok=True)

        with open(path, "wb") as f:
            f.write(attachment_bytes)
        return path
    except Exception as e:
        logging.error(f"Error downloading attachment {filename}: {e}")
        return None


def process_nylas_emails(
    client, grant_id=NYLAS_GRANT_ID, keywords=["квитанція", "receipt", "платіж"]
):
    if not grant_id:
        raise ValueError(
            "NYLAS_GRANT_ID not provided or found in environment variables."
        )

    query = " OR ".join(keywords)
    messages = fetch_receipt_messages(client, grant_id, query)
    downloaded_files = []

    for msg in messages:
        # msg.attachments is a list of Attachment objects in v3
        msg_attachments = getattr(msg, "attachments", [])
        if msg_attachments:
            for attachment in msg_attachments:
                att_id = getattr(attachment, "id", None)
                att_filename = getattr(attachment, "filename", None)
                getattr(attachment, "content_type", "")

                if att_id and att_filename:
                    # Filter for likely receipt files
                    ext = os.path.splitext(att_filename)[1].lower()
                    if ext in [".pdf", ".jpg", ".jpeg", ".png"]:
                        # Skip small icons/logos
                        size = getattr(attachment, "size", 0)
                        if size > 0 and size < 10000:  # Smaller than 10KB
                            continue

                        # Use unique filename to prevent overwrites (e.g. many files named receipt.pdf)
                        unique_filename = f"{msg.id[:8]}_{att_filename}"
                        path = os.path.join("attachments", unique_filename)

                        if os.path.exists(path):
                            logging.info(
                                f"Attachment {unique_filename} already exists, skipping download."
                            )
                            downloaded_files.append(path)
                            continue

                        logging.info(
                            f"Downloading attachment: {unique_filename} ({size} bytes)"
                        )
                        path = download_nylas_attachment(
                            client, grant_id, att_id, msg.id, unique_filename
                        )

                        if path:
                            downloaded_files.append(path)
    return downloaded_files
