"""환경설정 로드 — .env를 의존성 없이 직접 파싱(기존 스크립트와 동일 방식).

.env가 없는 환경(GitHub Actions 등)을 위해 OS 환경변수가 .env보다 우선한다.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = {**load_env(), **os.environ}

FRED_API_KEY = ENV.get("FRED_API_KEY", "")
ECOS_API_KEY = ENV.get("ECOS_API_KEY", "")
GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")

# Gmail SMTP (앱 비밀번호) — 미설정 시 dispatcher가 안내 후 중단
SMTP_USER = ENV.get("SMTP_USER", "")
SMTP_PASS = ENV.get("SMTP_PASS", "")
# 기본 수신자 = 발신 계정(W2: 나 혼자 받기)
MAIL_TO = ENV.get("MAIL_TO", SMTP_USER)

# Slack (봇 토큰 방식) — W2 브리핑 수신 채널
SLACK_BOT_TOKEN = ENV.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = ENV.get("SLACK_CHANNEL", "")

# Telegram (봇 토큰 방식) — W2 브리핑 수신. chat_id는 getUpdates로 자동 탐색 가능
TELEGRAM_BOT_TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = ENV.get("TELEGRAM_CHAT_ID", "")


def dsn() -> str:
    """psycopg 연결 문자열. docker-compose 기본값과 동일하게 폴백."""
    return (
        f"host={ENV.get('POSTGRES_HOST', 'localhost')} "
        f"port={ENV.get('POSTGRES_PORT', '5432')} "
        f"dbname={ENV.get('POSTGRES_DB', 'econ_brief')} "
        f"user={ENV.get('POSTGRES_USER', 'econ')} "
        f"password={ENV.get('POSTGRES_PASSWORD', 'econ_dev_pw')}"
    )
