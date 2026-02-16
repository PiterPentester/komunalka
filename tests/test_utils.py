from utils import infer_service_type, parse_date, extract_data_from_text
from datetime import datetime


def test_infer_service_type():
    assert infer_service_type("Нафтогаз", "") == "gas"
    assert infer_service_type("", "Оплата за електроенергію") == "electricity"
    assert infer_service_type("Водоканал", "") == "water"
    assert infer_service_type("Triolan", "") == "internet"
    assert infer_service_type("Unknown", "Some random text") == "other"


def test_parse_date():
    assert parse_date("07.02.2026 11:32") == datetime(2026, 2, 7, 11, 32)
    assert parse_date("2026-02-07 11:32:00") == datetime(2026, 2, 7, 11, 32)
    assert parse_date("invalid") is None


def test_extract_data_from_text():
    sample_text = """
    Отримувач: КП Водоканал
    Квитанція № 12345
    Дата та час здійснення операції: 10.02.2026 15:00
    Сума до сплати: 150.50 UAH
    Комісія: 2.00 UAH
    Платник: Іванов Іван
    """
    data = extract_data_from_text(sample_text)

    assert data["receipt_number"] == "12345"
    assert data["total_amount"] == 150.50
    assert data["commission"] == 2.00
    assert data["service_provider"] == "КП Водоканал"
    assert data["service_type"] == "water"
    assert isinstance(data["payment_datetime"], datetime)
    assert data["payment_datetime"].day == 10
