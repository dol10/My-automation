# =============================================
# config.py — 설정 파일 (이 파일만 수정하면 됩니다)
# =============================================

import os

# DART Open API 키 — GitHub Secrets에서 읽음
DART_API_KEY = os.environ.get("DART_API_KEY", "")

# 지아이이노베이션 고유번호 (변경 불필요)
CORP_CODE = "00684937"
CORP_NAME = "지아이이노베이션"

# 공시 수집 기간
MONTHS_BACK = 12

# 결산 연도
FISCAL_YEAR     = "2024"
FISCAL_YEAR_ALT = "2025"

# ─── 이메일 설정 ──────────────────────────────
EMAIL_ENABLED   = True
EMAIL_SENDER = "dhstjrdlek@gmail.com"    
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = "dhstjrdlek@gmail.com"  
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# ─── 슬랙 (안 쓰면 False) ─────────────────────
SLACK_ENABLED     = False
SLACK_WEBHOOK_URL = ""

# ─── 텔레그램 (안 쓰면 False) ─────────────────
TELEGRAM_ENABLED   = False
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID   = ""

# ─── 스케줄 ───────────────────────────────────
SCHEDULE_HOUR   = 9
SCHEDULE_MINUTE = 0

# ─── 저장 경로 ────────────────────────────────
DB_PATH  = "dart_monitor.db"
LOG_PATH = "dart_monitor.log"
