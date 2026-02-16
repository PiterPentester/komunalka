import os
import logging
import json
from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession
from dotenv import load_dotenv
from models import init_db, get_session, Receipt
from gmail_helper import get_gmail_service, process_emails
from nylas_helper import get_nylas_client, process_nylas_emails
from utils import process_receipt_file
from scheduler import start_scheduler

load_dotenv()

# Setup
init_db()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Simple login session (using a dict for demo, in production use middleware/JWT)
sessions = {}

# Background scheduler startup
BACKGROUND_CONFIG = {
    "telegram_token": os.environ.get("TG_TOKEN"),
    "telegram_chat_id": os.environ.get("TG_CHAT_ID"),
}
start_scheduler(BACKGROUND_CONFIG)

# i18n Dictionary
I18N = {
    "uk": {
        "title": "Комуналка",
        "dashboard": "Дашборд",
        "settings": "Налаштування",
        "scan_btn": "Сканувати пошту",
        "total_spent": "Всього витрачено",
        "receipts": "Квитанції",
        "addresses": "Активні адреси",
        "recent_receipts": "Останні квитанції",
        "date": "Дата",
        "provider": "Надавач",
        "type": "Тип",
        "amount": "Сума",
        "address": "Адреса",
        "save": "Зберегти",
        "logout": "Вихід",
        "notifications": "Сповіщення",
        "tg_token": "Токен Telegram-бота",
        "tg_chat_id": "ID чату Telegram",
        "nylas_api_key": "Nylas API Key",
        "nylas_grant_id": "Nylas Grant ID",
        "login_title": "Вхід",
        "user": "Користувач",
        "pwd": "Пароль",
        "electricity": "Електроенергія",
        "gas": "Газ",
        "water": "Вода",
        "heating": "Опалення",
        "rent": "Управління",
        "internet": "Інтернет",
        "other": "Інше",
    },
    "en": {
        "title": "Komunalka",
        "dashboard": "Dashboard",
        "settings": "Settings",
        "scan_btn": "Scan Emails",
        "total_spent": "Total Spent",
        "receipts": "Receipts",
        "addresses": "Active Addresses",
        "recent_receipts": "Recent Receipts",
        "date": "Date",
        "provider": "Provider",
        "type": "Type",
        "amount": "Amount",
        "address": "Address",
        "save": "Save",
        "logout": "Logout",
        "notifications": "Notifications",
        "tg_token": "Telegram Bot Token",
        "tg_chat_id": "Telegram Chat ID",
        "nylas_api_key": "Nylas API Key",
        "nylas_grant_id": "Nylas Grant ID",
        "login_title": "Login",
        "user": "User",
        "pwd": "Password",
        "electricity": "Electricity",
        "gas": "Gas",
        "water": "Water",
        "heating": "Heating",
        "rent": "Rent",
        "internet": "Internet",
        "other": "Other",
    },
}


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def get_lang(request: Request):
    return request.cookies.get("lang", "uk")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    lang = get_lang(request)
    return templates.TemplateResponse(
        "login.html", {"request": request, "T": I18N[lang], "lang": lang}
    )


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    lang = get_lang(request)
    env_user = os.environ.get("APP_USERNAME", "admin")
    env_pass = os.environ.get("APP_PASSWORD", "admin")

    if username == env_user and password == env_pass:
        sessions["is_authenticated"] = True
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "T": I18N[lang],
            "lang": lang,
            "error": "Invalid credentials",
        },
    )


@app.get("/lang/{lang_code}")
async def set_language(lang_code: str):
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(key="lang", value=lang_code)
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: DBSession = Depends(get_db)):
    if not sessions.get("is_authenticated"):
        return RedirectResponse(url="/")

    lang = get_lang(request)
    receipts = db.query(Receipt).order_by(Receipt.payment_datetime.desc()).all()

    # Convert to JSON for Chart.js
    data = []
    for r in receipts:
        data.append(
            {
                "id": r.id,
                "provider": r.service_provider,
                "type": r.service_type,
                "amount": r.total_amount,
                "date": r.payment_datetime.strftime("%Y-%m-%d")
                if r.payment_datetime
                else None,
                "address": r.address,
            }
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "receipts": data,
            "json_data": json.dumps(data),
            "T": I18N[lang],
            "lang": lang,
        },
    )


@app.post("/analyze_local")
async def analyze_local(db: DBSession = Depends(get_db)):
    if not sessions.get("is_authenticated"):
        return JSONResponse(
            {"status": "error", "message": "Unauthorized"}, status_code=401
        )

    try:
        att_dir = "attachments"
        if not os.path.exists(att_dir):
            return JSONResponse(
                {
                    "status": "success",
                    "added": 0,
                    "message": "No attachments folder found",
                }
            )

        files = [
            os.path.join(att_dir, f)
            for f in os.listdir(att_dir)
            if os.path.isfile(os.path.join(att_dir, f))
            and f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))
        ]

        count = 0
        for f in files:
            logging.info(f"Local analysis of file: {f}")
            data = process_receipt_file(f)
            if data:
                existing = (
                    db.query(Receipt)
                    .filter_by(receipt_number=data.get("receipt_number"))
                    .first()
                )
                if not existing:
                    r = Receipt(**data, raw_file_path=f, payment_status="successful")
                    db.add(r)
                    db.commit()
                    count += 1
                else:
                    logging.info(
                        f"Receipt {data.get('receipt_number')} already exists."
                    )
            else:
                logging.warning(f"Could not extract data from {f}")

        return JSONResponse({"status": "success", "added": count})
    except Exception as e:
        logging.error(f"Local analysis error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/scan")
async def scan_emails(db: DBSession = Depends(get_db)):
    if not sessions.get("is_authenticated"):
        return JSONResponse({"status": "unauthorized"}, status_code=401)

    files = []
    try:
        if os.environ.get("NYLAS_API_KEY") and os.environ.get("NYLAS_GRANT_ID"):
            logging.info("Scanning using Nylas...")
            client = get_nylas_client()
            files = process_nylas_emails(client)
        else:
            logging.info("Scanning using Gmail direct API...")
            service = get_gmail_service()
            files = process_emails(service)

        count = 0
        for f in files:
            logging.info(f"Analyzing file: {f}")
            data = process_receipt_file(f)
            if data:
                logging.info(
                    f"Successfully extracted data from {f}: {data.get('receipt_number')}"
                )
                existing = (
                    db.query(Receipt)
                    .filter_by(receipt_number=data.get("receipt_number"))
                    .first()
                )
                if not existing:
                    r = Receipt(**data, raw_file_path=f, payment_status="successful")
                    db.add(r)
                    db.commit()
                    count += 1
                else:
                    logging.info(
                        f"Receipt {data.get('receipt_number')} already exists in DB."
                    )
            else:
                logging.warning(f"Failed to extract data from {f}")
        return JSONResponse({"status": "success", "added": count})
    except Exception as e:
        logging.error(f"Scan error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    if not sessions.get("is_authenticated"):
        return RedirectResponse(url="/")
    lang = get_lang(request)
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "tg_token": os.environ.get("TG_TOKEN", ""),
            "tg_chat_id": os.environ.get("TG_CHAT_ID", ""),
            "nylas_api_key": os.environ.get("NYLAS_API_KEY", ""),
            "nylas_grant_id": os.environ.get("NYLAS_GRANT_ID", ""),
            "T": I18N[lang],
            "lang": lang,
        },
    )


@app.post("/settings")
async def save_settings(
    token: str = Form(None),
    chat_id: str = Form(None),
    nylas_api_key: str = Form(None),
    nylas_grant_id: str = Form(None),
):
    if token:
        os.environ["TG_TOKEN"] = token
    if chat_id:
        os.environ["TG_CHAT_ID"] = chat_id
    if nylas_api_key:
        os.environ["NYLAS_API_KEY"] = nylas_api_key
    if nylas_grant_id:
        os.environ["NYLAS_GRANT_ID"] = nylas_grant_id
    # In a real app, save to a .env or config file
    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
