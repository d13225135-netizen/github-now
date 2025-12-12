#!/usr/bin/env python3
# scripts/check.py
import os
import json
import time
import logging
from typing import Set
import requests
from mcstatus import JavaServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

SERVER_ADDR = os.environ.get("MC_HOST", "yaneznau.peniscraft.pro")
SERVER = JavaServer.lookup(SERVER_ADDR)

BOT = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT = os.environ.get("TELEGRAM_CHAT_ID")
STATE_PATH = os.path.join("scripts", "last_players.txt")
REQUEST_TIMEOUT = float(os.environ.get("MC_TIMEOUT", 5.0))

if not BOT or not CHAT:
    logging.error("TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы в окружении")
    raise SystemExit(1)

def send(text: str):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT}/sendMessage",
            data={"chat_id": CHAT, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        r.raise_for_status()
    except Exception as e:
        logging.exception("Ошибка при отправке Telegram: %s", e)

def read_last() -> Set[str]:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data or [])
    except FileNotFoundError:
        logging.info("Файл состояния не найден, считаем что никто не был онлайн")
        return set()
    except Exception:
        logging.exception("Не удалось прочитать файл состояния, возвращаю пустой набор")
        return set()

def write_last(players: Set[str]):
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(list(players)), f, ensure_ascii=False)
    except Exception:
        logging.exception("Не удалось сохранить файл состояния")

def get_players():
    try:
        q = SERVER.query(timeout=REQUEST_TIMEOUT)
        players = set(q.players.names or [])
        logging.info("Получено через query(): %s", players)
        return players, "query"
    except Exception as e:
        logging.info("Query недоступен (%s), пробую status()", e)
    try:
        s = SERVER.status(timeout=REQUEST_TIMEOUT)
        sample = s.players.sample or []
        players = set([p.name for p in sample if getattr(p, "name", None)])
        logging.info("Получено через status(): %s", players)
        return players, "status"
    except Exception as e:
        logging.exception("Не удалось получить статус сервера: %s", e)
        return set(), "error"

def main():
    logging.info("=== check.py started ===")
    last = read_last()
    current, method = get_players()

    joined = sorted(list(current - last))
    left = sorted(list(last - current))

    if joined:
        logging.info("Зашли: %s", joined)
        for p in joined:
            send(f"👤 *Игрок {p} зашёл на сервер.*\n📊 Сейчас {len(current)} игроков: {', '.join(sorted(current)) if current else 'никого'}")
    if left:
        logging.info("Вышли: %s", left)
        for p in left:
            send(f"🚪 *Игрок {p} вышел с сервера.*\n📊 Сейчас {len(current)} игроков: {', '.join(sorted(current)) if current else 'никого'}")

    # Если изменений нет — логируем, но не спамим Telegram
    if not joined and not left:
        logging.info("Изменений в составе нет. Сейчас: %s", ", ".join(sorted(current)) if current else "никого")

    # Всегда сохраняем текущее состояние (важно для локального запуска)
    write_last(current)

    # Краткая сводка (одним сообщением, опционально)
    summary = f"*Сервер:* `{SERVER_ADDR}`\n*Метод:* {method}\n*Игроки сейчас:* {', '.join(sorted(current)) if current else 'никого'}"
    logging.info("Summary: %s", summary)
    send(summary)  # раскомментируй, если хочешь получать сводку каждый запуск

    logging.info("=== check.py finished ===")

if __name__ == "__main__":
    main()
