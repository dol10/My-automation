# =============================================
# main.py — 메인 실행 파일
# 실행: python main.py
# =============================================

import schedule
import time
import logging
from datetime import datetime

import config
from dart_api  import get_disclosure_list, get_income_statement
from storage   import init_db, filter_new_disclosures, save_disclosures, save_financials
from notifier  import build_html_report, send_email, send_slack, send_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def run_job():
    logger.info("=" * 50)
    logger.info(f"DART 모니터링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    init_db(config.DB_PATH)

    # 1. 공시 수집
    logger.info("공시 목록 수집 중...")
    all_disc = get_disclosure_list(config.DART_API_KEY, config.CORP_CODE, config.MONTHS_BACK)
    logger.info(f"수집된 공시: {len(all_disc)}건")

    new_disc = filter_new_disclosures(config.DB_PATH, all_disc)
    logger.info(f"신규 공시: {len(new_disc)}건")

    # 2. 손익계산서 수집
    logger.info("손익계산서 수집 중...")
    financial = get_income_statement(config.DART_API_KEY, config.CORP_CODE, config.FISCAL_YEAR_ALT)
    if not financial:
        financial = get_income_statement(config.DART_API_KEY, config.CORP_CODE, config.FISCAL_YEAR)

    if financial:
        logger.info(f"재무 데이터 수집 완료: {financial['year']}년 {financial['report_type']}")
        for nm, v in financial["accounts"].items():
            logger.info(f"  {nm}: 당기={v.get('당기','')}  전기={v.get('전기','')}")
    else:
        logger.warning("재무 데이터를 가져오지 못했습니다.")

    # 3. 저장
    if new_disc:
        save_disclosures(config.DB_PATH, new_disc)
    if financial:
        save_financials(config.DB_PATH, financial)

    # 4. 알림
    subject   = f"[DART] {config.CORP_NAME} 리포트 · {datetime.now().strftime('%Y.%m.%d')}"
    html_body = build_html_report(config.CORP_NAME, new_disc, financial)

    send_email(config, subject, html_body)
    send_slack(config, f"*{config.CORP_NAME}* 신규공시 {len(new_disc)}건")
    send_telegram(config, f"<b>{config.CORP_NAME}</b> 신규공시 {len(new_disc)}건")

    logger.info("작업 완료")
    logger.info("=" * 50)


def main():
    logger.info(f"에이전트 시작 — 매일 {config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d} 자동 실행")

    logger.info("▶ 즉시 1회 실행 (테스트)")
    run_job()

    schedule.every().day.at(f"{config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d}").do(run_job)
    logger.info("스케줄 등록 완료. 대기 중... (종료: Ctrl+C)")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
