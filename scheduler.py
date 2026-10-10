from apscheduler.schedulers.background import BackgroundScheduler
import logging
from datetime import datetime, timedelta
from models import get_session, Receipt
from gmail_helper import get_gmail_service, process_emails
from nylas_helper import get_nylas_client, process_nylas_emails
from utils import process_receipt_file
from notifications import notify_new_receipt
import os


def daily_scan_task(config):
    logging.info("Starting daily background scan...")
    session = get_session()
    files = []
    try:
        if os.environ.get("NYLAS_API_KEY") and os.environ.get("NYLAS_GRANT_ID"):
            client = get_nylas_client()
            files = process_nylas_emails(client)
        else:
            service = get_gmail_service()
            files = process_emails(service)

        for file_path in files:
            receipts_data = process_receipt_file(file_path)
            for data in receipts_data:
                existing = (
                    session.query(Receipt)
                    .filter_by(
                        receipt_number=data.get("receipt_number"),
                        total_amount=data.get("total_amount"),
                        service_provider=data.get("service_provider"),
                    )
                    .first()
                )
                if not existing:
                    receipt = Receipt(
                        receipt_number=data.get("receipt_number"),
                        payment_datetime=data.get("payment_datetime"),
                        total_amount=data.get("total_amount"),
                        transferred_amount=data.get("transferred_amount"),
                        commission=data.get("commission"),
                        service_provider=data.get("service_provider"),
                        service_type=data.get("service_type"),
                        payer_name=data.get("payer_name"),
                        address=data.get("address"),
                        bank_terminal=data.get("bank_terminal"),
                        account_number=data.get("account_number"),
                        payment_status="successful",
                        raw_file_path=file_path,
                    )
                    session.add(receipt)
                    session.commit()

                    if config.get("telegram_token") and config.get("telegram_chat_id"):
                        notify_new_receipt(
                            config["telegram_token"], config["telegram_chat_id"], data
                        )

        # Cleanup old records (older than 1 year)
        one_year_ago = datetime.now() - timedelta(days=365)
        session.query(Receipt).filter(Receipt.payment_datetime < one_year_ago).delete()
        session.commit()

    except Exception as e:
        logging.error(f"Error in background task: {e}")
    finally:
        session.close()


def start_scheduler(config):
    scheduler = BackgroundScheduler()
    # Schedule at midnight
    scheduler.add_job(daily_scan_task, "cron", hour=0, minute=0, args=[config])
    scheduler.start()
    logging.info("Background scheduler started.")
    return scheduler
