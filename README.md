# AWS Cloud Practitioner – Quiz Bot (Telegram/WhatsApp)

Bot de práctica para el examen **AWS Cloud Practitioner**. Envía preguntas tipo test y corrige en el acto. 
Funciona localmente y puede conectarse a **Telegram Bot API** (gratis).

## Stack
- **Python** (FastAPI, Uvicorn)
- **Webhook**: Telegram Bot API (y/o WhatsApp Cloud API)
- **Ngrok** para exponer el servidor local
- Preparado para **AWS Lambda + API Gateway** (con `mangum`) más adelante

## Requisitos
- Python 3.10+
- `pip` o `uv`/`pipx`
- (Opcional) **ngrok** para URL pública del webhook

## Instalación
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env

> Estado: **Telegram-only**. Integración WhatsApp pendiente.

