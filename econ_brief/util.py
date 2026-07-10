"""운영 유틸 (W5) — 재시도, 장애 알림."""
import time

import requests

from econ_brief import config


def retry(fn, *, tries: int = 3, delay: float = 2.0, backoff: float = 2.0, label: str = ""):
    """fn()을 실패 시 지수 백오프로 재시도. 마지막 예외는 그대로 올린다."""
    wait = delay
    last = None
    for attempt in range(1, tries + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt < tries:
                print(f"  ↻ 재시도 {attempt}/{tries - 1} ({label or fn.__name__}): "
                      f"{type(e).__name__} — {wait:.0f}s 후")
                time.sleep(wait)
                wait *= backoff
    raise last


def ops_notify(text: str) -> bool:
    """운영 장애 알림을 텔레그램으로(설정돼 있으면). 실패해도 조용히 False."""
    token = config.TELEGRAM_BOT_TOKEN
    chat = config.TELEGRAM_CHAT_ID
    if not (token and chat):
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": f"🚨 [econ-brief] {text}"},
            timeout=15,
        )
        return r.ok
    except Exception:  # noqa: BLE001
        return False
