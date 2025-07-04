# rtms_app/lawd.py
from __future__ import annotations

import os
from typing import Dict

import pandas as pd
import streamlit as st

###############################################################################
# 1. 법정동 코드 테이블 로드
###############################################################################
@st.cache_data(show_spinner=False)
def load_lawd_table() -> pd.DataFrame:
    """
    ▸ ‘법정동코드 전체자료’(.xlsx/.xls/.csv) → 시도·시군구·LAWD 코드(5자리) DataFrame
    """
    # ── ① 파일 탐색 ───────────────────────────────────────────────────────
    for fn in os.listdir("."):
        ext = fn.split(".")[-1].lower()
        if fn.startswith("법정동코드") and ext in {"xlsx", "xls", "csv"}:
            path = fn
            break
    else:
        raise FileNotFoundError("⚠️ ‘법정동코드…’ 파일을 앱 폴더에 넣어 주세요!")

    # ── ② 파일 읽기 ───────────────────────────────────────────────────────
    if ext in {"xlsx", "xls"}:
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str, encoding="euc-kr")

    # ── ③ 정리 & 필터 ─────────────────────────────────────────────────────
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"법정동코드": "code", "법정동명": "name", "폐지여부": "status"})
    sgg = df[df["code"].str[-5:].eq("00000") & df["status"].eq("존재")].copy()

    parts = sgg["name"].str.split()
    sgg["시도"] = parts.str[0]
    sgg["시군구"] = parts.str[1].fillna(sgg["시도"])
    sgg["LAWD_CD"] = sgg["code"].str[:5]

    return sgg[["시도", "시군구", "LAWD_CD"]]

###############################################################################
# 2. 딕셔너리 빌드 {시도: {시군구: LAWD_CD}}
###############################################################################
@st.cache_data(show_spinner=False)
def build_lawd_dict() -> Dict[str, Dict[str, str]]:
    sgg = load_lawd_table()
    mapping: Dict[str, Dict[str, str]] = {}
    for _, row in sgg.iterrows():
        mapping.setdefault(row["시도"], {})[row["시군구"]] = row["LAWD_CD"]
    return mapping
