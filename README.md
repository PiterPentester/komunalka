# Komunalka Dashboard

A full-stack Python web application to automate utility receipt tracking from Gmail/Nylas, designed with modern aesthetics and production-ready infrastructure.

## 🚀 Features
- **Smart Integration**: Automatically fetches receipt emails (PDF/Images) using Gmail API or Nylas.
- **Advanced Data Extraction**: Uses `pdfplumber` and `pytesseract` (OCR) with highly optimized regex for Ukrainian utility providers (PrivatBank, Naftogaz, etc.).
- **Modern Dashboard**: High-performance dashboard with Chart.js, featuring stacked area trends, synchronized color coding, and deep-dive breakouts.
- **📱 Mobile Friendly**: Specifically optimized for the **Pixel 3a** and other small screens.
- **🌍 Internationalization**: Complete support for **Ukrainian** and **English** (UI and service types).
- **🔒 Secure & Production Ready**:
    - Optimized **multi-stage Docker builds** using `python:3.12-slim-bookworm` for efficiency.
    - Multi-arch support (**AMD64/ARM64**) for deployment on desktops or edge devices like **Orange Pi**.
    - Fully configurable via environment variables and Kubernetes secrets.

- **🤖 Automation**:
    - Daily background scans via APScheduler.
    - Telegram bot notifications for new receipts.
    - Automated CI/CD via GitHub Actions pushing to GHCR.

## 📋 Requirements
- **Python 3.12+**
- **uv** (recommended package manager)
- **Tesseract OCR** (with Ukrainian/English language packs)
- **Google API / Nylas Credentials**
- **Docker** (optional for containerized deployment)

## 🛠️ Setup & Development

### 1. Local Installation
This project uses `uv` for fast dependency management.
```bash
# Install dependencies
make install

# Start development server
make dev
```
*The app is available at [http://localhost:8000](http://localhost:8000)*

### 2. Tesseract OCR Setup
#### macOS:
```bash
brew install tesseract tesseract-lang
```
#### Ubuntu/Debian/OrangePi:
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-ukr tesseract-ocr-eng
```

### 3. Makefile Commands
| Command | Description |
| :--- | :--- |
| `make dev` | Run FastAPI with hot-reload |
| `make test` | Run pytest suite |
| `make lint` | Run ruff linter |
| `make format` | Auto-format code with ruff |
| `make check-format` | Verify code formatting (CI) |
| `make docker-build` | Build local Docker image |
| `make docker-arm64-build` | Build and push ARM64 image |
| `make k8s-deploy` | Deploy to Kubernetes via kubectl |


## 🐳 Docker & Kubernetes

### Docker (Multi-stage)
The project uses optimized multi-stage builds. To build and run natively:
```bash
make docker-build
make docker-run
```

### Kubernetes (k3s/Orange Pi 5)
Manifests are located in `/k8s`. A `PersistentVolumeClaim` is used for the SQLite database and attachments.
```bash
# 1. Update k8s/secret.yaml with your tokens
# 2. Deploy the stack
make k8s-deploy
```

## ⚙️ Configuration
- **Environment**: Copy `.env.example` to `.env` (secrets for Telegram, Nylas, Gmail).
- **Login**: Configurable via `APP_USERNAME` and `APP_PASSWORD`. Defaults to `admin`.
- **Database**: `DATABASE_URL` env var allows switching SQLite paths for K8s volumes.

## 📁 Project Structure
- `app.py`: Core FastAPI application and i18n logic.
- `utils.py`: OCR and smart extraction logic.
- `models.py`: Database schema and persistence.
- `k8s/`: Kubernetes deployment manifests.
- `.github/workflows/`: CI/CD multi-arch build pipeline.
- `templates/` & `static/`: Glassmorphism UI and responsive styles.

## 🍊 Orange Pi 5 / ARM64 Notes
- The image is fully ARM64 compatible via Docker Buildx.
- Memory limits in `k8s/deployment.yaml` are tuned for edge devices (512Mi-1Gi).
- Tesseract runs efficiently on the OP5's RK3588 CPU.
