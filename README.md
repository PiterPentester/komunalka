# 🏠 Komunalka (Комуналка)

A local, private dashboard to track your expenses and receipts directly from your Gmail inbox. Designed for privacy and simplicity, running locally on your device (e.g., Orange Pi, Mac, PC).

## 🚀 Features
- **Smart Scanning**: Fetches potential receipts (PDFs, recognized keywords) from Gmail.
- **Local AI**: Optional on-device AI classification for expense categories.
- **Privacy First**: Your data never leaves your device. Credentials stay local.
- **Visual Analytics**: Beautiful calendar heatmaps and spending trends.
- **Ukrainian Context**: Optimized for Ukrainian receipts ("грн", "рахунок", "PrivatBank").

## 🛠️ Setup Instructions

### 1. Google Cloud Configuration (One-time)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "Komunalka Local").
3. Navigate to **APIs & Services > Library** and enable the **Gmail API**.
4. Go to **APIs & Services > OAuth consent screen**.
   - select **External** (since it's for personal use with your own email).
   - Fill in required fields (App name, support email).
   - Add your email as a **Test User**.
5. Go to **APIs & Services > Credentials**.
   - Click **Create Credentials > OAuth client ID**.
   - Application type: **Desktop app**.
   - Download the JSON file and rename it to `credentials.json`.
   - **Move `credentials.json` to this project folder.**

### 2. Installation
Ensure you have Python 3.10+ installed.

```bash
# Install dependencies
pip install -r requirements.txt
```

*Note for Orange Pi/Raspberry Pi*: If `torch` installation fails, try installing system packages or using a specific pip index for ARM.

### 3. Usage
Run the dashboard locally:

```bash
streamlit run app.py
```
Or to expose it on your local network:
```bash
streamlit run app.py --server.address 0.0.0.0
```

1. The app will open in your browser.
2. Enter the path to `credentials.json` (default is `./credentials.json`).
3. Click **Connect & Scan**.
4. On first run, a browser window will open to authorize access to your Gmail.

## 🤖 AI Features
To enable AI categorization:
1. Toggle "Enable AI Features" in the sidebar.
2. The app will download a small model (`distilbert-base-uncased`) to better understand receipt context.

## 📂 Data
- Data is auto-saved to `receipts_database.csv`.
- You can export reports directly from the dashboard.
