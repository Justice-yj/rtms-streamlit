# rtms_app/api.py
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta

from .config import ENDPOINT, SERVICE_KEY

###############################################################################
# 1. 단일 YYYYMM 데이터 요청
###############################################################################
def fetch_rtms(lawd_cd: str, deal_ymd: str, rows: int = 1000, page: int = 1) -> pd.DataFrame:
    params: Dict[str, Any] = {
        "serviceKey": SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": rows,
        "pageNo": page,
    }
    res = requests.get(ENDPOINT, params=params, timeout=15)
    res.raise_for_status()

    root = ET.fromstring(res.content)
    if root.findtext("./header/resultMsg") != "OK":
        raise RuntimeError(root.findtext("./header/resultMsg") or "Unknown API error")

    items: List[Dict[str, Any]] = []
    for it in root.findall(".//item"):
        g = it.findtext
        items.append(
            {
                "아파트": g("aptNm"),
                "거래금액(만원)": g("dealAmount"),
                "전용면적(m²)": g("excluUseAr"),
                "층": g("floor"),
                "건축년도": g("buildYear"),
                "거래일": f"{g('dealYear')}-{g('dealMonth'):0>2}-{g('dealDay'):0>2}",
                "도로명": g("roadNm"),
            }
        )

    df = pd.DataFrame(items)
    if not df.empty:
        df["거래금액(만원)"] = pd.to_numeric(df["거래금액(만원)"].str.replace(",", ""), errors="coerce")
        df["전용면적(m²)"] = pd.to_numeric(df["전용면적(m²)"], errors="coerce")
        df["층"] = pd.to_numeric(df["층"], errors="coerce")
        df["건축년도"] = pd.to_numeric(df["건축년도"], errors="coerce")
        df["거래일"] = pd.to_datetime(df["거래일"], errors="coerce")
    return df

###############################################################################
# 2. 기간별 데이터 병합
###############################################################################
def month_range(start_ym: str, end_ym: str) -> List[str]:
    start = datetime.strptime(start_ym, "%Y%m"); end = datetime.strptime(end_ym, "%Y%m")
    if start > end:
        start, end = end, start
    months: List[str] = []
    while start <= end:
        months.append(start.strftime("%Y%m"))
        start += relativedelta(months=1)
    return months


def fetch_rtms_range(lawd_cd: str, start_ym: str, end_ym: str) -> pd.DataFrame:
    frames = [fetch_rtms(lawd_cd, ym) for ym in month_range(start_ym, end_ym)]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
