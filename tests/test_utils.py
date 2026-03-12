import utils
from datetime import datetime


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


def test_extract_data_from_text_by_account():
    sample_text = """
    Отримувач: Славутське УВКГ
    Квитанція № 999
    Особовий рахунок: 3934
    Сума: 200.00
    """
    data = utils.extract_data_from_text(sample_text)
    assert data["account_number"] == "3934"
    assert data["address"] == "пров. Григорія Сковороди, буд. 20, кв. 2"
    assert data["service_type"] == "water"


def test_extract_data_from_text_by_address():
    sample_text = """
    Отримувач: Газмережі
    Сума: 300.00
    Адреса: вул. Грушевського, буд. 82
    """
    data = utils.extract_data_from_text(sample_text)
    assert data["address"] == "вул. Грушевського, буд.82"
    assert data["total_amount"] == 300.00


def test_extract_data_from_text_skipped():
    sample_text = """
    Отримувач: Невідомий
    Сума: 10.00
    Адреса: вул. Чужа, 1
    """
    data = utils.extract_data_from_text(sample_text)
    assert data == {}  # Should be skipped
def test_extract_data_from_text_multiple_accounts():
    # Account 1-5817 has multiple entries: Опалення and Утримання будинку
    # Test for Опалення (heating)
    sample_text_heating = """
    Отримувач: Славутське ЖКО КП
    Квитанція № 123
    Особовий рахунок: 1-5817
    Призначення: Оплата за опалення
    Сума: 500.00
    """
    data = utils.extract_data_from_text(sample_text_heating)
    assert data["account_number"] == "1-5817"
    assert data["service_type"] == "heating"
    assert data["address"] == "вул. Перемоги, буд. 25, кв. 115-116"

    # Test for Утримання будинку (maintenance)
    sample_text_rent = """
    Отримувач: Славутське ЖКО КП
    Квитанція № 124
    Особовий рахунок: 1-5817
    Призначення: Утримання будинку
    Сума: 200.00
    """
    data = utils.extract_data_from_text(sample_text_rent)
    assert data["account_number"] == "1-5817"
    assert data["service_type"] == "maintenance"
    assert data["address"] == "вул. Перемоги, буд. 25, кв. 115-116"

def test_extract_data_from_text_multiple_accounts_diff_address():
    # Mock ACCOUNT_MAPPING for this test
    original_mapping = utils.ACCOUNT_MAPPING
    utils.ACCOUNT_MAPPING = {
        "99-9999": [
            {"address": "Address A", "service": "Газопостачання"},
            {"address": "Address B", "service": "Вода"}
        ]
    }
    try:
        # Test for Gas
        sample_gas = "Особовий рахунок: 99-9999\nНазва: Нафтогаз\nСума: 100"
        data = utils.extract_data_from_text(sample_gas)
        assert data["address"] == "Address A"

        # Test for Water
        sample_water = "Особовий рахунок: 99-9999\nНазва: Водоканал\nСума: 200"
        data = utils.extract_data_from_text(sample_water)
        assert data["address"] == "Address B"
    finally:
        utils.ACCOUNT_MAPPING = original_mapping

def test_extract_data_from_text_garbage():
    sample_text = """
    Отримувач: Славута-Сервіс, КП
    Квитанція № 555
    Особовий рахунок: 5-5817
    Призначення: Вивіз ТПВ
    Сума: 50.00
    """
    data = utils.extract_data_from_text(sample_text)
    assert data["account_number"] == "5-5817"
    assert data["service_type"] == "garbage"
def test_extract_data_from_text_gas_split():
    # Account 360098992 (Supply) and 1400262249 (Transport)
    # Test for Gas Supply
    sample_supply = """
    Отримувач: Хмельницька філія ТОВ ГАЗМЕРЕЖІ
    Особовий рахунок: 360098992
    Сума: 150.00
    """
    data = utils.extract_data_from_text(sample_supply)
    assert data["service_type"] == "gas_supply"
    assert data["address"] == "пров. Григорія Сковороди, буд. 20, кв. 2"
    
    # Test for Gas Transport
    sample_transport = """
    Отримувач: Газорозподільні мережі України
    Особовий рахунок: 1400262249
    Сума: 70.00
    """
    data = utils.extract_data_from_text(sample_transport)
    assert data["service_type"] == "gas_transport"


def test_extract_data_from_text_electricity():
    # Test for Electricity (newly added)
    sample_text = """
    Отримувач: ТОВ "Хмельницькенергозбут"
    Особовий рахунок: 11100008010025
    Сума: 450.00
    """
    data = utils.extract_data_from_text(sample_text)
    assert data["service_type"] == "electricity"
    assert data["account_number"] == "11100008010025"
    assert data["address"] == "пров. Григорія Сковороди, буд. 20, кв. 2"
