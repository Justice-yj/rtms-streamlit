# rtms_app/config.py
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

###############################################################################
# .env → 환경 변수 로드
###############################################################################
load_dotenv()                                   # .env 없으면 조용히 무시

# ── 필수 키 ────────────────────────────────────────────────────────────────
SERVICE_KEY     = os.getenv("RTMS_KEY")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")

if not SERVICE_KEY or not OPENAI_API_KEY:
    st.error("🚨 환경변수 RTMS_KEY·OPENAI_API_KEY 를 설정해 주세요!")
    st.stop()

# RTMS API ENDPOINT
ENDPOINT = (
    "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/"
    "getRTMSDataSvcAptTradeDev"
)


print(SERVICE_KEY)
print(OPENAI_API_KEY)


# 기타 공통 경로
BASE_DIR = Path(__file__).resolve().parent
