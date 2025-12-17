#!/usr/bin/env python3
# scripts/check.py
import os
import json
import logging
import socket
from typing import Set, Dict
import requests
from mcstatus import JavaServer
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Конфигурация
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "last_players.txt")
PLAYTIME_PATH = os.path.join(BASE_DIR, "playtime.json")

SERVER_ADDR = os.environ.get("MC_HOST", "yaneznau.peniscraft.pro")
SERVER = JavaServer.lookup(SERVER_ADDR)

BOT = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT = os.environ.get("TELEGRAM_CHAT_ID")
REQUEST_TIMEOUT = float(os.environ.get("MC_TIMEOUT", 5.0))

if not BOT or not CHAT:
    logging.error("TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы в окружении")
    raise SystemExit(1)

# --- Telegram ---
def send(text: str):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT}/sendMessage",
            data={"chat_id": CHAT, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        r.raise_for_status()
    except Exception:
        logging.exception("Ошибка при отправке Telegram")

# --- Работа с файлом состояния ---
def read_last() -> Set[str]:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return set()
            data = json.loads(content)
            if isinstance(data, str) and data == "никого":
                return set()
            return set(data or [])
    except FileNotFoundError:
        return set()
    except Exception:
        logging.exception("Не удалось прочитать файл состояния")
        return set()

def write_last(players: Set[str]):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            if players:
                json.dump(sorted(list(players)), f, ensure_ascii=False)
            else:
                json.dump("никого", f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        logging.info("Состояние сохранено: %s", players if players else "никого")
    except Exception:
        logging.exception("Не удалось сохранить файл состояния")

# --- Учёт времени ---
def load_playtime() -> Dict[str, Dict]:
    try:
        with open(PLAYTIME_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        logging.exception("Ошибка чтения playtime.json")
        return {}

def save_playtime(data: Dict[str, Dict]):
    try:
        with open(PLAYTIME_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        logging.exception("Ошибка записи playtime.json")

def update_playtime(joined, left):
    data = load_playtime()
    now = datetime.datetime.now().timestamp()

    for p in joined:
        if p not in data:
            data[p] = {"total": 0, "start": now}
        else:
            data[p]["start"] = now

    for p in left:
        if p in data and "start" in data[p]:
            session = now - data[p]["start"]
            data[p]["total"] += int(session)
            data[p].pop("start", None)

    save_playtime(data)

# --- Получение игроков ---
def get_players():
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(REQUEST_TIMEOUT)
    try:
        try:
            q = SERVER.query()
            players = set(q.players.list or [])
            if players:
                return players, "query"
        except Exception:
            logging.info("Query недоступен, пробую status()")

        try:
            s = SERVER.status()
            if s.players.sample:
                players = {p.name for p in s.players.sample if getattr(p, "name", None)}
                return players, "status"
            else:
                return set(), "status"
        except Exception as e:
            logging.exception("Не удалось получить статус сервера: %s", e)
            return set(), "error"
    finally:
        socket.setdefaulttimeout(old_timeout)

# --- Основная логика ---
def main():
    logging.info("=== check.py started ===")
    last = read_last()
    current, method = get_players()

    joined = sorted(list(current - last))
    left = sorted(list(last - current))

    if joined:
        for p in joined:
            send(f"👤 *Игрок {p} зашёл на сервер.*\n📊 Сейчас {len(current)} игроков: {', '.join(sorted(current)) if current else 'никого'}")
    if left:
        for p in left:
            send(f"🚪 *Игрок {p} вышел с сервера.*\n📊 Сейчас {len(current)} игроков: {', '.join(sorted(current)) if current else 'никого'}")

    if not joined and not left:
        logging.info("Изменений в составе нет. Сейчас: %s", ', '.join(sorted(current)) if current else "никого")

    write_last(current)
    update_playtime(joined, left)

    summary = f"*Сервер:* `{SERVER_ADDR}`\n*Метод:* {method}\n*Игроки сейчас:* {', '.join(sorted(current)) if current else 'никого'}"
    send(summary)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send(f"--------------\n🕒 Сеанс завершён: {now}\n--------------")

    logging.info("=== check.py finished ===")

if __name__ == "__main__":
    main()
