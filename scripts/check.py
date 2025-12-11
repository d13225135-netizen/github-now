import os, json, requests
from mcstatus import JavaServer

# Адрес твоего сервера Minecraft
SERVER = JavaServer.lookup("yaneznau.peniscraft.pro:25565")

# Переменные окружения из GitHub Secrets
BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]

def send(text: str):
    """Отправка сообщения в Telegram"""
    requests.post(
        f"https://api.telegram.org/bot{BOT}/sendMessage",
        data={"chat_id": CHAT, "text": text}
    )

def read_last():
    """Чтение списка игроков из last_players.txt"""
    try:
        with open("scripts/last_players.txt", "r", encoding="utf-8") as f:
            return set(json.loads(f.read() or "[]"))
    except Exception:
        return set()

def write_last(players: set):
    """Запись списка игроков в last_players.txt"""
    with open("scripts/last_players.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(list(players), ensure_ascii=False))

# --- Основная логика ---
last = read_last()

try:
    status = SERVER.query()
    current = set(status.players.names or [])
except Exception:
    current = set()

joined = current - last
left = last - current

for p in joined:
    send(f"👤 Игрок {p} зашёл на сервер.\n📊 Сейчас {len(current)} игроков: {', '.join(current) if current else 'никого'}")

for p in left:
    send(f"🚪 Игрок {p} вышел с сервера.\n📊 Сейчас {len(current)} игроков: {', '.join(current) if current else 'никого'}")

if joined or left:
    write_last(current)
