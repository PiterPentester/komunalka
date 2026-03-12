"""
Unit tests for utils.py.

All tests use the `fake_account_mapping` fixture defined in conftest.py
(applied via autouse=True), so they are fully isolated from the real
accounts_to_address_mapping.csv file and will not break if that file changes.

Fake accounts used:
  T-0001 – Water
  T-0002 – Gas supply
  T-0003 – Gas transport
  T-0004 – Electricity
  T-0005 – Garbage
  T-0006 – Heating + Maintenance (same account, multi-entry)
  T-0007 – Gas vs Water, two different addresses (same account)
"""

import utils
from datetime import datetime


# ---------------------------------------------------------------------------
# Pure-function tests (no mapping involved)
# ---------------------------------------------------------------------------


def test_infer_service_type():
    assert utils.infer_service_type("Нафтогаз", "") == "gas_supply"
    assert utils.infer_service_type("", "Оплата за електроенергію") == "electricity"
    assert utils.infer_service_type("Водоканал", "") == "water"
    assert utils.infer_service_type("Triolan", "") == "internet"
    assert utils.infer_service_type("", "Розподіл газу") == "gas_transport"
    assert utils.infer_service_type("Unknown", "Some random text") == "other"


def test_parse_date():
    assert utils.parse_date("07.02.2026 11:32") == datetime(2026, 2, 7, 11, 32)
    assert utils.parse_date("2026-02-07 11:32:00") == datetime(2026, 2, 7, 11, 32)
    assert utils.parse_date("invalid") is None


# ---------------------------------------------------------------------------
# Receipt extraction tests (all use fake accounts / addresses)
# ---------------------------------------------------------------------------


def test_extract_data_from_text_by_account_water():
    """Account T-0001 → Water service, resolved from mapping."""
    text = """
    Отримувач: Тест-Водоканал
    Квитанція № TEST-001
    Особовий рахунок: T-0001
    Сума: 200.00
    """
    data = utils.extract_data_from_text(text)
    assert data["account_number"] == "T-0001"
    assert data["address"] == "вул. Тестова, буд. 1, кв. 1"
    assert data["service_type"] == "water"
    assert data["total_amount"] == 200.00


def test_extract_data_from_text_by_address():
    """Address lookup — fake address triggers a match even without an account number."""
    text = """
    Отримувач: Тест-Газ
    Сума: 300.00
    Адреса: вул. Тестова, буд. 1, кв. 1
    """
    data = utils.extract_data_from_text(text)
    # Address should be normalized to the canonical value from mapping
    assert data["address"] == "вул. Тестова, буд. 1, кв. 1"
    assert data["total_amount"] == 300.00


def test_extract_data_from_text_skipped():
    """Receipts with unknown accounts and addresses must be discarded."""
    text = """
    Отримувач: Абсолютно Невідомий
    Сума: 10.00
    Адреса: вул. Чужа, 999
    """
    data = utils.extract_data_from_text(text)
    assert data == {}


def test_extract_data_from_text_gas_supply():
    """Account T-0002 → Gas supply."""
    text = """
    Отримувач: Тест-Газ
    Квитанція № TEST-002
    Особовий рахунок: T-0002
    Сума: 150.00
    """
    data = utils.extract_data_from_text(text)
    assert data["account_number"] == "T-0002"
    assert data["service_type"] == "gas_supply"
    assert data["address"] == "вул. Тестова, буд. 1, кв. 1"


def test_extract_data_from_text_gas_transport():
    """Account T-0003 → Gas transport."""
    text = """
    Отримувач: Тест-Газмережі
    Квитанція № TEST-003
    Особовий рахунок: T-0003
    Сума: 70.00
    """
    data = utils.extract_data_from_text(text)
    assert data["account_number"] == "T-0003"
    assert data["service_type"] == "gas_transport"


def test_extract_data_from_text_electricity():
    """Account T-0004 → Electricity."""
    text = """
    Отримувач: Тест-Енерго
    Квитанція № TEST-004
    Особовий рахунок: T-0004
    Сума: 450.00
    """
    data = utils.extract_data_from_text(text)
    assert data["account_number"] == "T-0004"
    assert data["service_type"] == "electricity"
    assert data["address"] == "вул. Тестова, буд. 1, кв. 1"


def test_extract_data_from_text_garbage():
    """Account T-0005 → Garbage collection."""
    text = """
    Отримувач: Тест-Сервіс
    Квитанція № TEST-005
    Особовий рахунок: T-0005
    Призначення: Вивіз ТПВ
    Сума: 50.00
    """
    data = utils.extract_data_from_text(text)
    assert data["account_number"] == "T-0005"
    assert data["service_type"] == "garbage"


def test_extract_data_from_text_multi_service_heating():
    """Account T-0006 with heating billing → picks Heating entry."""
    text = """
    Отримувач: Тест-ЖКО
    Квитанція № TEST-006-H
    Особовий рахунок: T-0006
    Призначення: Оплата за опалення
    Сума: 500.00
    """
    data = utils.extract_data_from_text(text)
    assert data["account_number"] == "T-0006"
    assert data["service_type"] == "heating"
    assert data["address"] == "вул. Тестова, буд. 3, кв. 5"


def test_extract_data_from_text_multi_service_maintenance():
    """Account T-0006 with maintenance billing → picks Maintenance entry."""
    text = """
    Отримувач: Тест-ЖКО
    Квитанція № TEST-006-M
    Особовий рахунок: T-0006
    Призначення: Утримання будинку
    Сума: 200.00
    """
    data = utils.extract_data_from_text(text)
    assert data["account_number"] == "T-0006"
    assert data["service_type"] == "maintenance"
    assert data["address"] == "вул. Тестова, буд. 3, кв. 5"


def test_extract_data_from_text_multi_account_diff_address():
    """Account T-0007 resolves different addresses based on detected service."""
    # Gas → first mapping entry
    text_gas = "Особовий рахунок: T-0007\nНазва: Нафтогаз\nСума: 100"
    data = utils.extract_data_from_text(text_gas)
    assert data["address"] == "вул. Адресна, буд. 10"

    # Water → second mapping entry
    text_water = "Особовий рахунок: T-0007\nНазва: Водоканал\nСума: 200"
    data = utils.extract_data_from_text(text_water)
    assert data["address"] == "вул. Інша, буд. 20"
