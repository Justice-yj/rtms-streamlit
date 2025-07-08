# config.py - 설정 및 환경 변수 관리 모듈
# .env 파일에서 API 키 등의 민감한 정보를 로드하고, 프로젝트 전역에서 사용할
# 주요 설정값들을 정의합니다.
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# --- .env 파일 로드 ---
# 프로젝트 루트의 .env 파일이 존재하면 환경 변수로 로드합니다.
load_dotenv()

# --- 필수 API 키 로드 및 검증 ---
SERVICE_KEY = os.getenv("RTMS_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VWORLD_API_KEY = os.getenv("VWORLD_API_KEY")

# 필수 키가 설정되지 않았으면 에러 메시지를 표시하고 앱 실행을 중지합니다.
if not SERVICE_KEY or not OPENAI_API_KEY or not VWORLD_API_KEY:
    st.error("🚨 환경변수 RTMS_KEY, OPENAI_API_KEY, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET를 .env 파일에 설정해주세요!")
    st.stop()

# --- 서비스 키 자동 보정 (안전장치) ---
# .env 파일에서 마지막 '==' 문자가 누락되는 문제를 방지하기 위해,
# 키가 '=='로 끝나지 않는 경우에만 자동으로 추가합니다.
if not SERVICE_KEY.endswith("=="):
    SERVICE_KEY += "=="

# --- API 엔드포인트 정의 ---
ENDPOINT = (
    "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/"
    "getRTMSDataSvcAptTradeDev"
)

# --- 기타 공통 경로 --- (필요시 사용)
BASE_DIR = Path(__file__).resolve().parent
