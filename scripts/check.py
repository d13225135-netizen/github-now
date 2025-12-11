import os, json, requests
from mcstatus import JavaServer
print("=== check.py started ===")
# Адрес сервера (порт можно не указывать, если стандартный 25565)
SERVER = JavaServer.lookup("yaneznau.peniscraft.pro")

BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]

def send(text: str):
    requests.post(
        f"https://api.telegram.org/bot{BOT}/sendMessage",
        data={"chat_id": CHAT, "text": text}
    )

def read_last():
    try:
        with open("scripts/last_players.txt", "r", encoding="utf-8") as f:
            return set(json.loads(f.read() or "[]"))
    except Exception:
        return set()

def write_last(players: set):
    with open("scripts/last_players.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(list(players), ensure_ascii=False))

last = read_last()

# --- Получаем игроков ---
try:
    # Пробуем полный query (работает только если enable-query=true на сервере)
    status = SERVER.query()
    current = set(status.players.names or [])
except Exception:
    # Если query недоступен, fallback на status()
    status = SERVER.status()
    current = set([p.name for p in (status.players.sample or [])])

joined = current - last
left = last - current

for p in joined:
    send(f"👤 Игрок {p} зашёл на сервер.\n📊 Сейчас {len(current)} игроков: {', '.join(current) if current else 'никого'}")

for p in left:
    send(f"🚪 Игрок {p} вышел с сервера.\n📊 Сейчас {len(current)} игроков: {', '.join(current) if current else 'никого'}")

# Записываем текущее состояние ВСЕГДА
write_last(current)
print("=== check.py finished ===")
