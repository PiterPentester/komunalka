import asyncio
from telegram import Bot
import logging


async def send_telegram_notification(token, chat_id, message):
    if not token or not chat_id:
        logging.warning("Telegram token or chat_id not provided.")
        return

    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message)
        logging.info("Telegram notification sent.")
    except Exception as e:
        logging.error(f"Error sending Telegram notification: {e}")


def notify_new_receipt(token, chat_id, receipt_data):
    msg = (
        f"✅ Нова квитанція оброблена:\n"
        f"🏢 Надавач: {receipt_data.get('service_provider', 'N/A')}\n"
        f"💰 Сума: {receipt_data.get('total_amount', 'N/A')} UAH\n"
        f"📅 Дата: {receipt_data.get('payment_datetime', 'N/A')}"
    )

    # Run async function in a new event loop if necessary
    try:
        asyncio.run(send_telegram_notification(token, chat_id, msg))
    except Exception as e:
        logging.error(f"Failed to run telegram notification task: {e}")
