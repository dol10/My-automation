# =============================================
# storage.py — SQLite 저장 & 중복 필터
# =============================================

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS disclosures (
            rcept_no    TEXT PRIMARY KEY,
            corp_name   TEXT,
            report_nm   TEXT,
            rcept_dt    TEXT,
            url         TEXT,
            flr_nm      TEXT,
            notified_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS financials (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            year        TEXT,
            report_type TEXT,
            account_nm  TEXT,
            current_amt TEXT,
            prev_amt    TEXT,
            saved_at    TEXT
        )
    """)
    conn.commit()
    conn.close()


def filter_new_disclosures(db_path, disclosures):
    if not disclosures:
        return []
    conn = sqlite3.connect(db_path)
    existing = set(r[0] for r in conn.execute("SELECT rcept_no FROM disclosures").fetchall())
    conn.close()
    return [d for d in disclosures if d["rcept_no"] not in existing]


def save_disclosures(db_path, disclosures):
    if not disclosures:
        return
    conn = sqlite3.connect(db_path)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for d in disclosures:
        conn.execute("""
            INSERT OR IGNORE INTO disclosures
            (rcept_no, corp_name, report_nm, rcept_dt, url, flr_nm, notified_at)
            VALUES (?,?,?,?,?,?,?)
        """, (d["rcept_no"], d["corp_name"], d["report_nm"],
              d["rcept_dt"], d["url"], d["flr_nm"], now))
    conn.commit()
    conn.close()
    logger.info(f"공시 {len(disclosures)}건 저장")


def save_financials(db_path, financial):
    if not financial or not financial.get("accounts"):
        return
    conn = sqlite3.connect(db_path)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for nm, vals in financial["accounts"].items():
        conn.execute("""
            INSERT INTO financials
            (year, report_type, account_nm, current_amt, prev_amt, saved_at)
            VALUES (?,?,?,?,?,?)
        """, (financial["year"], financial["report_type"],
              nm, vals.get("당기", ""), vals.get("전기", ""), now))
    conn.commit()
    conn.close()
    logger.info(f"재무 데이터 저장 ({financial['year']}년)")
