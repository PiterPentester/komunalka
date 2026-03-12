import csv
import re
import pdfplumber
import pytesseract
from PIL import Image
import os
from datetime import datetime
import logging
import hashlib
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_account_mapping(csv_path=None):
    if csv_path is None:
        csv_path = os.environ.get(
            "ACCOUNTS_MAPPING_PATH", "accounts_to_address_mapping.csv"
        )

    mapping = {}
    content = os.environ.get("ACCOUNTS_MAPPING_CSV")

    f = None
    if content:
        f = io.StringIO(content.strip())
        logging.info("Loading mapping from environment variable ACCOUNTS_MAPPING_CSV.")
    elif os.path.exists(csv_path):
        f = open(csv_path, mode="r", encoding="utf-8")
        logging.info(f"Loading mapping from file {csv_path}.")
    else:
        logging.warning(
            f"Mapping source not found (path: {csv_path}, env: ACCOUNTS_MAPPING_CSV)."
        )
        return mapping

    try:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            acc = row["AccountNumber"].strip()
            if acc not in mapping:
                mapping[acc] = []
            mapping[acc].append(
                {
                    "address": row["Address"].strip(),
                    "service": row["Service"].strip(),
                    "company": row["Company"].strip(),
                }
            )
    except Exception as e:
        logging.error(f"Error loading mapping: {e}")
    finally:
        if not content and f:
            f.close()

    return mapping


ACCOUNT_MAPPING = load_account_mapping()


def normalize_string(s):
    if not s:
        return ""
    return re.sub(r"[^\w\d]", "", s.lower())


def get_known_addresses():
    addresses = set()
    for mappings in ACCOUNT_MAPPING.values():
        for m in mappings:
            addresses.add(m["address"])
    return sorted(list(addresses))


def is_receipt_relevant(data, text):
    """
    Check if the receipt is relevant based on account number or address.
    """
    # 1. Check if account number is in our mapping
    acc_num = data.get("account_number")
    if acc_num and acc_num in ACCOUNT_MAPPING:
        return True

    # 2. Check for manual account number presence in text if regex missed it
    for acc in ACCOUNT_MAPPING.keys():
        if acc in text:
            data["account_number"] = acc
            return True

    # 3. Fallback: check raw text for any of our known addresses (normalized)
    norm_text = normalize_string(text)

    for mappings in ACCOUNT_MAPPING.values():
        for m in mappings:
            addr = m["address"]
            if normalize_string(addr) in norm_text:
                if not data.get("address"):
                    data["address"] = addr
                return True
            # More relaxed check
            relaxed_addr = re.sub(
                r"(?:вул|буд|кв|пров|провулок|просп|бул)\.?",
                "",
                addr,
                flags=re.IGNORECASE,
            )
            if normalize_string(relaxed_addr) in norm_text:
                if not data.get("address"):
                    data["address"] = addr
                return True

    return False


def infer_service_type(provider_name, text):
    text = (provider_name + " " + text).lower()
    if any(k in text for k in ["інт", "теле", "net", "зв'яз", "triolan", "volia"]):
        return "internet"
    if any(k in text for k in ["трансп", "розпод", "газмереж", "delivery", "distrib"]):
        return "gas_transport"
    if any(k in text for k in ["постач", "supply", "нафтогаз", "газзбут"]):
        return "gas_supply"
    if any(k in text for k in ["газ", "gas"]):
        return "gas_supply"
    if any(k in text for k in ["вод", "водок", "water"]):
        return "water"
    if any(k in text for k in ["опал", "тепл", "heat", "hot water"]):
        return "heating"
    if any(k in text for k in ["електроен", "енерг", "power", "svitlo", "yee"]):
        return "electricity"
    if any(k in text for k in ["тпв", "смітт", "garbage", "trash"]):
        return "garbage"
    if any(k in text for k in ["утрим", "сервіс", "управл", "maintenance"]):
        return "maintenance"
    if any(k in text for k in ["оренда", "rent", "кварт"]):
        return "rent"
    return "other"


def parse_date(date_str):
    # Try different formats
    formats = ["%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def extract_text_from_pdf(pdf_path):
    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"

        # If no text extracted, try OCR (future fallback)
        if not all_text.strip():
            logging.info(f"No text layer found in {pdf_path}")
            pass
    except Exception as e:
        logging.error(f"Error reading PDF {pdf_path}: {e}")
    return all_text


def extract_text_from_image(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang="ukr+eng")
    except Exception as e:
        logging.error(f"Error performing OCR on {image_path}: {e}")
        return ""


def extract_data_from_text(text):
    data = {}

    # Regex patterns (generalized based on typical Ukrainian receipts)
    patterns = {
        "receipt_number": [
            r"Квитанція №\s*([A-Za-z0-9\-\.]+)",
            r"Номер квитанції\s*([A-Za-z0-9\-\.]+)",
            r"Receipt №\s*([A-Za-z0-9\-\.]+)",
            r"ID:\s*([A-Za-z0-9\-\.]+)",
            r"Квитанція електронна\s+([\d\-]+)",
        ],
        "payment_datetime": [
            r"Дата та час здійснення операції:\s*([\d\.\s:]+)",
            r"Дата:\s*([\d\.\s:]+)",
            r"Date:\s*([\d\.\s:]+)",
            r"Час:\s*([\d\.\s:]+)",
            r"Дата та час операції\s*([\d\.\s:]+)",
        ],
        "total_amount": [
            r"Сума до сплати:\s*([\d\.,\s]+)\s*UAH",
            r"Разом до сплати:\s*([\d\.,\s]+)",
            r"Total:\s*([\d\.,\s]+)\s*UAH",
            r"Сплачено\s*([\d\.,\s]+)\s*грн",
            r"Загальна сума\s*([\d\.,\s]+)\s*грн",
        ],
        "transferred_amount": [
            r"Сума:\s*([\d\.,\s]+)\s*UAH",
            r"Сума:\s*([\d\.,\s]+)",
            r"Amount:\s*([\d\.,\s]+)",
            r"Сума операції:\s*([\d\.,\s]+)",
            r"Сума переказу\s*([\d\.,\s]+)\s*грн",
        ],
        "commission": [
            r"Комісія:\s*([\d\.,\s]+)\s*UAH",
            r"Fee:\s*([\d\.,\s]+)",
            r"Сума комісії\s*([\d\.,\s]+)\s*грн",
        ],
        "service_provider": [
            r"Отримувач:?\s*([^\n]+)",
            r"Назва:?\s*([^\n]+)",
            r"Одержувач:?\s+([^\n]+)",
        ],
        "payer_name": [
            r"Платник:?\s*([^\n]+)",
            r"ПІБ:?\s*([^\n]+)",
            r"Платник:?\s+([^\n]+)",
        ],
        "address": [
            r"Адреса:?\s*([^\n]+)",
            # Capture everything after 'вул.' etc. until a known receipt keyword, allowing newlines
            r"((?:вул\.|просп\.|пров\.|провулок|пл\.|бул\.|вулиця)\s+(?:(?![СC]ума|Сума|Дата|Комісія|Разом|Одержувач|Платник|Призначення|грн|UAH|ID).)*)",
        ],
        "bank_terminal": [r"Термінал:\s*([^\n]+)", r"Термінал\s+([^\n]+)"],
        "account_number": [
            r"(?:Особовий рахунок|О/р|Л/р|Лиц. счет|Лицевой счет|№ о/р|№ рахунку)[:\s]*([\d\-]+)",
            r"Рахунок №\s*([\d\-]+)",
            r"Платник р/р\s*([\d\-]+)",
        ],
    }

    for key, regexes in patterns.items():
        for regex in regexes:
            if key == "address":
                # For address, we allow it to span lines but look for multiple potential hits
                matches = re.finditer(
                    regex, text, re.IGNORECASE | re.UNICODE | re.DOTALL
                )
                for match in matches:
                    val = match.group(1).strip()
                    # Clean up internal newlines and extra spaces
                    val = re.sub(r"\s+", " ", val)
                    # Skip PB head office address specifically
                    if "Грушевського" in val and ("1Д" in val.upper() or "Київ" in val):
                        continue
                    # Clean up trailing punctuation
                    val = val.rstrip(",. ")
                    # Skip if it's just the prefix or too short
                    if len(val) < 8 or val.lower().strip() in [
                        "вул.",
                        "вулиця",
                        "просп.",
                        "бул.",
                        "пров.",
                    ]:
                        continue
                    data[key] = val
                    break
                if key in data:
                    break
                continue

            match = re.search(regex, text, re.IGNORECASE | re.UNICODE)
            if match:
                val = match.group(1).strip()
                if key in ["total_amount", "transferred_amount", "commission"]:
                    # Handle multiple dots/commas
                    clean_val = val.replace(" ", "").replace(",", ".")
                    if clean_val.count(".") > 1:
                        # Probably thousands separator
                        clean_val = clean_val.replace(".", "", clean_val.count(".") - 1)
                    try:
                        val = float(clean_val)
                    except ValueError:
                        continue
                elif key == "payment_datetime":
                    val = parse_date(val)
                data[key] = val
                break

    # Post-process amounts: ensure total_amount is populated
    if "total_amount" not in data and "transferred_amount" in data:
        data["total_amount"] = data["transferred_amount"] + data.get("commission", 0)

    # Ensure receipt_number is present (fallback to hash of text if missing)
    if not data.get("receipt_number"):
        data["receipt_number"] = "AUTO-" + hashlib.md5(text.encode()).hexdigest()[:10]

    # Fallback/Debug
    if not data:
        logging.debug(f"No data extracted from text. Length: {len(text)}")

    if "service_provider" in data:
        data["service_type"] = infer_service_type(data["service_provider"], text)

    # Filtering and data enhancement
    if not is_receipt_relevant(data, text):
        logging.info(
            "Receipt skipped: does not match any valid account number or address."
        )
        return {}

    # If we have an account number, enhance with mapping data
    acc_num = data.get("account_number")
    if acc_num and acc_num in ACCOUNT_MAPPING:
        mappings = ACCOUNT_MAPPING[acc_num]

        # Pick the best mapping based on service type
        best_mapping = mappings[0]
        service_type = data.get("service_type")

        if len(mappings) > 1 and service_type:
            for m in mappings:
                m_service = m["service"].lower()
                if service_type == "gas_supply" and (
                    "постач" in m_service or "посулу" in m_service
                ):
                    best_mapping = m
                    break
                elif service_type == "gas_transport" and any(
                    k in m_service for k in ["трансп", "розпод"]
                ):
                    best_mapping = m
                    break
                elif service_type.startswith("gas") and "газ" in m_service:
                    best_mapping = m
                    break
                elif service_type == "water" and "вода" in m_service:
                    best_mapping = m
                    break
                elif service_type == "heating" and "опал" in m_service:
                    best_mapping = m
                    break
                elif service_type == "garbage" and "тпв" in m_service:
                    best_mapping = m
                    break
                elif service_type == "maintenance" and any(
                    k in m_service for k in ["утрим", "управл", "сервіс"]
                ):
                    best_mapping = m
                    break
                elif service_type == "rent" and "оренд" in m_service:
                    best_mapping = m
                    break

        # Override address with canonical version
        data["address"] = best_mapping["address"]

        # Preference mapping's service info over inferred one if inferred is 'other' or mismatch
        mapping_service = best_mapping["service"].lower()
        if any(k in mapping_service for k in ["електр", "енерг", "svitlo"]):
            data["service_type"] = "electricity"
        elif "постач" in mapping_service:
            data["service_type"] = "gas_supply"
        elif any(k in mapping_service for k in ["трансп", "розпод"]):
            data["service_type"] = "gas_transport"
        elif "газ" in mapping_service:
            data["service_type"] = "gas_supply"
        elif "вода" in mapping_service:
            data["service_type"] = "water"
        elif "опал" in mapping_service:
            data["service_type"] = "heating"
        elif "тпв" in mapping_service:
            data["service_type"] = "garbage"
        elif any(k in mapping_service for k in ["утрим", "управл", "сервіс"]):
            data["service_type"] = "maintenance"
        elif "оренд" in mapping_service:
            data["service_type"] = "rent"

    # If account missing but address known, try to infer account and normalize address
    elif data.get("address"):
        norm_data_addr = normalize_string(data["address"])
        found_match = False
        for acc, mappings in ACCOUNT_MAPPING.items():
            for m in mappings:
                if normalize_string(m["address"]) == norm_data_addr:
                    # Found a canonical address match!
                    data["address"] = m["address"]
                    # If service matches, we found the account!
                    if data.get("service_type") and data["service_type"] != "other":
                        # ... check service match (future improvement)
                        pass
                    found_match = True
                    break
            if found_match:
                break

    return data


def process_receipt_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    full_text = ""
    if ext == ".pdf":
        full_text = extract_text_from_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        full_text = extract_text_from_image(file_path)

    if not full_text.strip():
        logging.warning(f"No text extracted from {file_path}")
        return []

    # Identify receipt boundaries
    markers = [
        r"Квитанція електронна",
        r"Квитанція №",
        r"Номер квитанції",
        r"Receipt №",
    ]

    indices = []
    for marker in markers:
        for m in re.finditer(marker, full_text, re.IGNORECASE):
            indices.append(m.start())

    indices = sorted(list(set(indices)))

    chunks = []
    if not indices:
        chunks = [full_text]
    else:
        # If text starts with content before any marker, prepend it to first chunk
        if indices[0] > 0:
            # Check if there's significant content before (e.g. logos, headers)
            # For simplicity, we'll start chunks from 0 if there's only one marker
            if len(indices) == 1:
                indices[0] = 0
            # Otherwise, first chunk starts from 0 but first receipt marker is at indices[0]
            # Actually, most receipts start with the marker. Let's just use indices.

        for i in range(len(indices)):
            start = indices[i]
            end = indices[i + 1] if i + 1 < len(indices) else len(full_text)
            chunks.append(full_text[start:end])

    results = []
    for text in chunks:
        logging.info(
            f"Processing chunk of {len(text)} characters. Sample: {text[:50].replace('\\n', ' ')}..."
        )
        data = extract_data_from_text(text)
        # Only add if it looks like a real receipt
        if data and (data.get("total_amount") or data.get("receipt_number")):
            # If we don't have total_amount yet but have a receipt number, it might be a partial page
            # But the logic in extract_data_from_text should handle it if pages were joined correctly.
            results.append(data)

    logging.info(f"Extracted {len(results)} receipt(s) from {file_path}")
    return results
