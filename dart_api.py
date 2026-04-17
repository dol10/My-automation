# =============================================
# dart_api.py — DART API 수집 모듈
# =============================================

import requests
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)
DART_BASE = "https://opendart.fss.or.kr/api"


def get_disclosure_list(api_key, corp_code, months_back=3):
    """최근 N개월 공시 목록 조회"""
    end_date   = datetime.today()
    start_date = end_date - relativedelta(months=months_back)

    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bgn_de":    start_date.strftime("%Y%m%d"),
        "end_de":    end_date.strftime("%Y%m%d"),
        "page_count": 40,
    }
    try:
        resp = requests.get(f"{DART_BASE}/list.json", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "000":
            logger.warning(f"공시목록 오류: {data.get('message')}")
            return []

        result = []
        for item in data.get("list", []):
            result.append({
                "rcept_no":  item.get("rcept_no"),
                "corp_name": item.get("corp_name"),
                "report_nm": item.get("report_nm"),
                "rcept_dt":  item.get("rcept_dt"),
                "flr_nm":    item.get("flr_nm"),
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no')}",
            })
        return result

    except requests.RequestException as e:
        logger.error(f"공시 목록 API 실패: {e}")
        return []


def get_income_statement(api_key, corp_code, year):
    """손익계산서 조회 — 사업보고서 없으면 분기보고서로 재시도"""
    result = _fetch_financial(api_key, corp_code, year, "11011", "사업보고서")
    if result:
        return result
    for code, label in [("11014", "3분기보고서"), ("11012", "반기보고서"), ("11013", "1분기보고서")]:
        result = _fetch_financial(api_key, corp_code, year, code, label)
        if result:
            logger.info(f"{year}년 {label} 데이터 사용")
            return result
    return None


def _fetch_financial(api_key, corp_code, year, reprt_code, label):
    params = {
        "crtfc_key":  api_key,
        "corp_code":  corp_code,
        "bsns_year":  year,
        "reprt_code": reprt_code,
        "fs_div":     "OFS",
    }
    try:
        resp = requests.get(f"{DART_BASE}/fnlttSinglAcntAll.json", params=params, timeout=10)
        data = resp.json()
        if data.get("status") != "000":
            return None
        return _parse_income(data.get("list", []), year, label)
    except Exception:
        return None


def _parse_income(items, year, label):
    targets = {
        "매출액":     ["매출액", "영업수익", "수익(매출액)"],
        "영업이익":   ["영업이익", "영업이익(손실)"],
        "당기순이익": ["당기순이익", "당기순이익(손실)", "분기순이익"],
        "연구개발비": ["연구개발비", "연구비"],
    }
    accounts = {}
    for item in items:
        if item.get("sj_div") not in ("IS", "CIS"):
            continue
        acct = item.get("account_nm", "")
        for key, names in targets.items():
            if acct in names and key not in accounts:
                accounts[key] = {
                    "당기": item.get("thstrm_amount", ""),
                    "전기": item.get("frmtrm_amount", ""),
                }
    return {"year": year, "report_type": label, "accounts": accounts} if accounts else None
