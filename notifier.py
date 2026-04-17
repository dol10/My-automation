# =============================================
# notifier.py — 알림 발송 모듈
# =============================================

import smtplib
import logging
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)


def _fmt(amount_str):
    """숫자 문자열 → 억원/만원 단위 변환"""
    if not amount_str:
        return "정보없음"
    try:
        amt  = int(amount_str.replace(",", "").replace(" ", ""))
        sign = "-" if amt < 0 else ""
        amt  = abs(amt)
        if amt >= 100_000_000:
            eok = amt // 100_000_000
            man = (amt % 100_000_000) // 10_000
            return f"{sign}{eok:,}억 {man:,}만원" if man else f"{sign}{eok:,}억원"
        elif amt >= 10_000:
            return f"{sign}{amt // 10_000:,}만원"
        return f"{sign}{amt:,}원"
    except ValueError:
        return amount_str


def build_html_report(corp_name, disclosures, financial):
    today = datetime.now().strftime("%Y년 %m월 %d일")

    # 공시 섹션
    if disclosures:
        rows = "".join(f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;">
            {d['rcept_dt'][:4]}.{d['rcept_dt'][4:6]}.{d['rcept_dt'][6:]}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;">
            <a href="{d['url']}" style="color:#1a73e8;text-decoration:none;">{d['report_nm']}</a>
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;color:#666;">{d['flr_nm']}</td>
        </tr>""" for d in disclosures)
        disc_html = f"""
        <h2 style="font-size:15px;color:#333;margin:24px 0 10px;">📋 신규 공시 ({len(disclosures)}건)</h2>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead><tr style="background:#f5f5f5;">
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ddd;">날짜</th>
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ddd;">공시명</th>
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ddd;">제출인</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>"""
    else:
        disc_html = "<p style='color:#888;font-size:13px;'>신규 공시가 없습니다.</p>"

    # 재무 섹션
    if financial and financial.get("accounts"):
        rows = "".join(f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:500;">{nm}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;">{_fmt(v.get('당기',''))}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;color:#888;">{_fmt(v.get('전기',''))}</td>
        </tr>""" for nm, v in financial["accounts"].items())
        fin_html = f"""
        <h2 style="font-size:15px;color:#333;margin:24px 0 10px;">
          💰 {financial['year']}년 손익계산서 ({financial['report_type']})
        </h2>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead><tr style="background:#f5f5f5;">
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #ddd;">항목</th>
            <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd;">당기</th>
            <th style="padding:8px 12px;text-align:right;border-bottom:2px solid #ddd;">전기</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>"""
    else:
        fin_html = "<p style='color:#888;font-size:13px;'>재무제표 데이터를 가져올 수 없습니다.</p>"

    return f"""
    <html><body style="font-family:'Malgun Gothic',Arial,sans-serif;max-width:680px;margin:auto;color:#333;">
      <div style="background:#1a73e8;padding:20px 24px;border-radius:8px 8px 0 0;">
        <h1 style="color:#fff;margin:0;font-size:18px;">DART 모니터링 리포트</h1>
        <p style="color:#e8f0fe;margin:4px 0 0;font-size:12px;">{corp_name} · {today}</p>
      </div>
      <div style="padding:20px 24px;background:#fff;border:1px solid #e8eaed;border-top:none;border-radius:0 0 8px 8px;">
        {disc_html}
        {fin_html}
        <p style="margin-top:24px;font-size:11px;color:#aaa;">DART 자동화 모니터링 시스템</p>
      </div>
    </body></html>"""


def send_email(cfg, subject, html_body):
    if not cfg.EMAIL_ENABLED:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = cfg.EMAIL_SENDER
        msg["To"]      = cfg.EMAIL_RECEIVER
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP(cfg.EMAIL_SMTP_HOST, cfg.EMAIL_SMTP_PORT) as s:
            s.starttls()
            s.login(cfg.EMAIL_SENDER, cfg.EMAIL_PASSWORD)
            s.sendmail(cfg.EMAIL_SENDER, cfg.EMAIL_RECEIVER, msg.as_string())
        logger.info(f"이메일 발송 완료 → {cfg.EMAIL_RECEIVER}")
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")


def send_slack(cfg, text):
    if not cfg.SLACK_ENABLED:
        return
    try:
        requests.post(cfg.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        logger.info("슬랙 발송 완료")
    except Exception as e:
        logger.error(f"슬랙 발송 실패: {e}")


def send_telegram(cfg, text):
    if not cfg.TELEGRAM_ENABLED:
        return
    try:
        url = f"https://api.telegram.org/bot{cfg.TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": cfg.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
        logger.info("텔레그램 발송 완료")
    except Exception as e:
        logger.error(f"텔레그램 발송 실패: {e}")
