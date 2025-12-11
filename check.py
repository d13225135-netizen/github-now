import os, json, requests
from mcstatus import JavaServer

SERVER = JavaServer.lookup("yaneznau.peniscraft.pro:25565")
BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]

def send(text):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": CHAT, "text": text})

def read_last():
    try:
        with open("last_players.txt","r",encoding="utf-8") as f:
            return set(json.loads(f.read() or "[]"))
    except:
        return set()

def write_last(s):
    with open("last_players.txt","w",encoding="utf-8") as f:
        f.write(json.dumps(list(s), ensure_ascii=False))

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
