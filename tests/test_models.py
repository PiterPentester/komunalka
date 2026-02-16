from models import Receipt
from datetime import datetime


def test_create_receipt(db_session):
    receipt = Receipt(
        receipt_number="TEST123",
        payment_datetime=datetime.now(),
        total_amount=100.50,
        service_provider="Test Provider",
        service_type="gas",
        payer_name="Test Payer",
        address="Test Address",
        payment_status="successful",
    )
    db_session.add(receipt)
    db_session.commit()

    saved = db_session.query(Receipt).filter_by(receipt_number="TEST123").first()
    assert saved is not None
    assert saved.total_amount == 100.50
    assert saved.service_provider == "Test Provider"
