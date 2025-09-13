from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any, List
import random

from app.config import (
    VERIFY_TOKEN, LOCAL_ECHO,
    TELEGRAM_BOT_TOKEN, TELEGRAM_SECRET_TOKEN
)
from app.telegram import send_telegram_text

app = FastAPI(title="AWS WhatsApp Quiz", version="0.2.0")

# --- Banco mínimo de preguntas (provisorio, luego lo pasamos a archivo/DB) ---
QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "domain": "Security",
        "q": "¿Qué describe mejor el modelo de responsabilidad compartida en AWS?",
        "options": [
            "AWS gestiona seguridad EN la nube; tú, seguridad DE la nube.",
            "El cliente gestiona todo, incluso data centers.",
            "AWS gestiona todo, incluso tu IAM y tu código.",
            "El cliente solo gestiona su código y nada más."
        ],
        "answer": 0,
        "explanation": "AWS asegura la infraestructura y capas gestionadas; tú configuras IAM, red, SO (en EC2), cifrado, etc."
    },
    {
        "id": 2,
        "domain": "Pricing",
        "q": "¿Qué opción ofrece descuento por compromiso de 1 o 3 años?",
        "options": ["On-Demand", "Savings Plans/Reserved Instances", "Spot", "Dedicated Hosts"],
        "answer": 1,
        "explanation": "Savings Plans y RIs reducen costo frente a On-Demand a cambio de un compromiso."
    },
    {
        "id": 3,
        "domain": "Global Infrastructure",
        "q": "¿Qué es una Availability Zone (AZ) en AWS?",
        "options": [
            "Conjunto de cuentas de un cliente",
            "Uno o más data centers con energía/red redundante en una Región",
            "Un edge location de CDN",
            "Una red virtual en un VPC"
        ],
        "answer": 1,
        "explanation": "Una AZ es una o más instalaciones físicas separadas dentro de la Región, conectadas a baja latencia."
    },
]

# --- Estado en memoria por usuario (solo para local) ---
SESSIONS: Dict[str, Dict[str, Any]] = {}
LETTERS = ["A", "B", "C", "D"]

def format_question(q: Dict[str, Any], idx: int, total: int) -> str:
    opts = "\n".join([f"{LETTERS[i]}) {opt}" for i, opt in enumerate(q["options"])])
    return (
        f"Pregunta {idx}/{total}:\n"
        f"{q['q']}\n\n"
        f"{opts}\n\n"
        f"Responde con A, B, C o D."
    )

def pick_questions(count: int = 3) -> List[Dict[str, Any]]:
    pool = QUESTIONS[:]
    random.shuffle(pool)
    return pool[:count]

def start_quiz_for_user(user: str, count: int = 3) -> str:
    selected = pick_questions(count)
    session = {
        "question_ids": [q["id"] for q in selected],
        "index": 0,
        "correct": 0,
        "responses": [],  # {id, user_answer, correct_answer, correct}
    }
    SESSIONS[user] = session
    qid = session["question_ids"][0]
    q = next(q for q in QUESTIONS if q["id"] == qid)
    return "🧠 AWS Cloud Practitioner – Quiz\n\n" + format_question(q, 1, len(session["question_ids"]))

def answer_to_index(text: str) -> int | None:
    t = (text or "").strip().lower()
    if t.startswith("a") or t == "1": return 0
    if t.startswith("b") or t == "2": return 1
    if t.startswith("c") or t == "3": return 2
    if t.startswith("d") or t == "4": return 3
    return None

def handle_command(user: str, text: str) -> str:
    t = (text or "").strip().lower()

    if t.startswith("/"):
        t = t[1:]  # <-- permite /start, /help, etc.

    if t in ("start", "quiz", "hola", "help", "ayuda"):
        return start_quiz_for_user(user)

    session = SESSIONS.get(user)
    if not session:
        return "Escribe START para comenzar el quiz del día."

    idx = session["index"]
    qid = session["question_ids"][idx]
    q = next((qq for qq in QUESTIONS if qq["id"] == qid), None)
    if not q:
        SESSIONS.pop(user, None)
        return "Error cargando la pregunta. Escribe START para reiniciar."

    ans_index = answer_to_index(t)
    if ans_index is None:
        return "Por favor responde con A, B, C o D."

    correct_idx = int(q["answer"])
    correct = (ans_index == correct_idx)
    if correct:
        session["correct"] += 1

    feedback = (
        f"{'✅ Correcto' if correct else '❌ Incorrecto'}\n"
        f"Respuesta: {LETTERS[correct_idx]}. {q['options'][correct_idx]}\n"
        f"ℹ️ {q.get('explanation','')}"
    )

    session["responses"].append({
        "id": qid,
        "user_answer": ans_index,
        "correct_answer": correct_idx,
        "correct": correct
    })

    session["index"] += 1

    total = len(session["question_ids"])
    if session["index"] >= total:
        score = session["correct"]
        wrong_domains = []
        for r in session["responses"]:
            if not r["correct"]:
                qq = next((x for x in QUESTIONS if x["id"] == r["id"]), None)
                if qq and qq.get("domain"):
                    wrong_domains.append(qq["domain"])
        recap = ""
        if wrong_domains:
            dd = sorted(set(wrong_domains))
            recap = "\n\n📚 Temas para repasar: " + ", ".join(dd)
        SESSIONS.pop(user, None)
        return f"{feedback}\n\n🎉 ¡Quiz completado! Puntuación: {score}/{total}.{recap}\n\nEscribe START para otra ronda."

    next_qid = session["question_ids"][session["index"]]
    next_q = next(x for x in QUESTIONS if x["id"] == next_qid)
    return f"{feedback}\n\n" + format_question(next_q, session["index"]+1, total)

# -------- Rutas --------

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    qp = request.query_params
    mode = (qp.get("hub.mode") or qp.get("hub_mode") or qp.get("mode") or "").lower()
    token = qp.get("hub.verify_token") or qp.get("hub_verify_token") or qp.get("verify_token")
    challenge = qp.get("hub.challenge") or qp.get("hub_challenge") or qp.get("challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return challenge
    raise HTTPException(status_code=403, detail="verification failed")

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return JSONResponse({"ok": True})
        msg = messages[0]
        from_number = msg.get("from", "local-user")
        text = msg.get("text", {}).get("body", "").strip()

        reply = handle_command(from_number, text)

        # En local devolvemos la respuesta para verla en curl;
        # cuando conectemos WhatsApp real, aquí haremos POST al Graph API.
        if LOCAL_ECHO:
            return JSONResponse({"ok": True, "reply": reply})
        return JSONResponse({"ok": True})
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
        return JSONResponse({"ok": True})
    
@app.post("/tg/webhook")
async def tg_webhook(request: Request):
    """
    Webhook de Telegram:
    - Valida secret token si lo configuraste.
    - Soporta mensajes de texto y callbacks (si luego usas botones).
    - Reusa handle_command(...) para contestar.
    """
    # 1) Validar secreto del webhook (opcional pero recomendado)
    if TELEGRAM_SECRET_TOKEN:
        header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header_token != TELEGRAM_SECRET_TOKEN:
            return JSONResponse({"ok": True})  # ignorar silenciosamente

    body = await request.json()
    # 2) Extraer chat_id y texto
    chat_id = None
    text = ""

    # a) Mensaje normal
    msg = body.get("message")
    if msg and msg.get("chat"):
        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()

    # b) Callback de botón (opcional futuro)
    if not chat_id:
        cb = body.get("callback_query")
        if cb and cb.get("message"):
            chat_id = cb["message"]["chat"]["id"]
            text = (cb.get("data") or "").strip()

    if not chat_id:
        return JSONResponse({"ok": True})

    # 3) Reusar el cerebro del quiz
    reply = handle_command(str(chat_id), text or "")

    # 4) Enviar respuesta
    if LOCAL_ECHO or not TELEGRAM_BOT_TOKEN:
        # modo prueba sin enviar realmente
        return JSONResponse({"ok": True, "reply": reply})
    try:
        send_telegram_text(TELEGRAM_BOT_TOKEN, chat_id, reply)
    except Exception as e:
        print(f"[TG SEND ERROR] {e}")

    return JSONResponse({"ok": True})

