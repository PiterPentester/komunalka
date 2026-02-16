import re
import pdfplumber
import pytesseract
from PIL import Image
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def infer_service_type(provider_name, text):
    text = (provider_name + " " + text).lower()
    if any(k in text for k in ["інт", "теле", "net", "зв", "triolan", "volia"]):
        return "internet"
    if any(k in text for k in ["газ", "gas", "нафтогаз"]):
        return "gas"
    if any(k in text for k in ["вод", "водок", "water"]):
        return "water"
    if any(k in text for k in ["опал", "тепл", "heat", "hot water"]):
        return "heating"
    if any(k in text for k in ["електроен", "енерг", "power", "svitlo", "yee"]):
        return "electricity"
    if any(k in text for k in ["оренда", "rent", "управл", "сервіс", "кварт", "тпв"]):
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
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # If no text extracted, try OCR
        if not text.strip():
            logging.info(f"No text layer found in {pdf_path}, falling back to OCR.")
            # This is a bit more complex, we'd need to convert PDF to images
            # For simplicity, we assume text layer exists for now or handle via direct OCR later
            pass
    except Exception as e:
        logging.error(f"Error reading PDF {pdf_path}: {e}")
    return text


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
            r"Отримувач:\s*([^\n]+)",
            r"Назва:\s*([^\n]+)",
            r"Одержувач\s+([^\n]+)",
        ],
        "payer_name": [
            r"Платник:\s*([^\n]+)",
            r"ПІБ:\s*([^\n]+)",
            r"Платник\s+([^\n]+)",
        ],
        "address": [
            r"Адреса:\s*([^\n,]+,\s*[^\n,]+)",
            r"((?:вул\.|просп\.|пров\.|провулок|пл\.|бул\.|вулиця)\s*[\s\.A-ZА-Яа-яііїє0-9\-]+(?:(?:,|\s+)\s*(?:буд\.|д\.|кв\.|кім\.|квартира|кв)\.?\s*[\d\-/A-ZА-Яа-яііїє]+|(?:\s*,\s*|(?:\s+))[\d\-/A-ZА-Яа-яііїє]+)+)",
            r"вул\.\s*([^,]+,\s*[^,\n]+)",
            r"((?:вул\.|просп\.|пров\.|провулок|пл\.|бул\.|вулиця)\s*[\s\.A-ZА-Яа-яііїє0-9\-]+(?:,|\s+)\s*[\d/A-ZА-Яа-я\-]+)",
        ],
        "bank_terminal": [r"Термінал:\s*([^\n]+)", r"Термінал\s+([^\n]+)"],
    }

    for key, regexes in patterns.items():
        for regex in regexes:
            if key == "address":
                # For address, we might have multiple matches (e.g. Bank address vs Property address)
                # We want to skip the bank's standard address
                matches = re.finditer(regex, text, re.IGNORECASE | re.UNICODE)
                for match in matches:
                    val = match.group(1).strip()
                    # Skip PB head office address specifically
                    if "Грушевського" in val and ("1Д" in val.upper() or "Київ" in val):
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

    import hashlib

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

    return data


def process_receipt_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        text = extract_text_from_image(file_path)

    if not text.strip():
        logging.warning(f"No text extracted from {file_path}")
        return None

    logging.info(
        f"Extracted {len(text)} characters from {file_path}. Sample: {text[:100].replace('\\n', ' ')}..."
    )
    data = extract_data_from_text(text)
    logging.info(f"Extracted data: {data}")
    return data
