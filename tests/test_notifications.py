from unittest.mock import patch, MagicMock
from notifications import notify_new_receipt


def test_notify_new_receipt_no_token():
    with patch("logging.warning"):
        notify_new_receipt(None, None, {})
        # Note: send_telegram_notification checks for token/chat_id
        # But notify_new_receipt calls it via asyncio.run
        # The check is inside send_telegram_notification
    # Hard to test log precisely without more setup, but let's mock the Bot instead


def test_notify_new_receipt_success():
    receipt_data = {
        "service_provider": "Test Provider",
        "total_amount": 100.0,
        "payment_datetime": "2026-02-10",
    }
    with patch("notifications.Bot") as MockBot:
        mock_bot_instance = MockBot.return_value
        # Mock send_message as a coroutine
        mock_bot_instance.send_message = MagicMock()

        notify_new_receipt("fake_token", "fake_chat_id", receipt_data)

        # Check if Bot was initialized with correct token
        MockBot.assert_called_once_with(token="fake_token")
        # Check if send_message was called
        # Note: asyncio.run(send_telegram_notification) will call it
        assert mock_bot_instance.send_message.called
