from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from app.config import VERIFY_TOKEN

app = FastAPI(title="AWS WhatsApp Quiz", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True}

# WhatsApp Cloud API VERIFICA el webhook con un GET:
@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    qp = request.query_params  # tipo QueryParams (dict-like)
    mode = (qp.get("hub.mode") or qp.get("hub_mode") or qp.get("mode") or "").lower()
    token = qp.get("hub.verify_token") or qp.get("hub_verify_token") or qp.get("verify_token")
    challenge = qp.get("hub.challenge") or qp.get("hub_challenge") or qp.get("challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return challenge  # texto plano
    raise HTTPException(status_code=403, detail="verification failed")

# POST /webhook: WhatsApp enviará los mensajes aquí
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    # Por ahora: sólo logica mínima de echo/ack
    # Más adelante: parsear mensaje, manejar A/B/C/D, etc.
    # WhatsApp exige 200 rápido; responder vacío si no hay mensaje.
    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return JSONResponse({"ok": True})

        msg = messages[0]
        from_number = msg.get("from")
        text = msg.get("text", {}).get("body", "").strip()

        # Respuesta mínima local (aún no llamamos a Graph API)
        # Cuando lo conectemos, aquí haremos POST al endpoint de WhatsApp.
        print(f"[INCOMING] from={from_number} text={text}")
        return JSONResponse({"ok": True})
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
        return JSONResponse({"ok": True})
