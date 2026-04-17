# =============================================
# run_once.py — GitHub Actions 전용 단일 실행
# =============================================

import logging
import config
from storage import init_db
from main    import run_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

init_db(config.DB_PATH)
run_job()
