# config.py - 설정 및 환경 변수 관리 모듈
# .env 파일에서 API 키 등의 민감한 정보를 로드하고, 프로젝트 전역에서 사용할
# 주요 설정값들을 정의합니다.
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
# --- .env 파일 로드 ---
# 프로젝트 루트의 .env 파일이 존재하면 환경 변수로 로드합니다.
load_dotenv()

# --- 필수 API 키 로드 및 검증 ---
SERVICE_KEY = os.getenv("RTMS_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VWORLD_API_KEY = os.getenv("VWORLD_API_KEY")

# 필수 키가 설정되지 않았으면 에러를 발생시킵니다.
if not SERVICE_KEY:
    raise ValueError("환경변수 RTMS_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
if not OPENAI_API_KEY:
    raise ValueError("환경변수 OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
if not VWORLD_API_KEY:
    raise ValueError("환경변수 VWORLD_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

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

# --- 법정동 코드 파일 경로 ---
# 환경 변수 `LAWD_CODE_FILE_PATH`가 있으면 그 값을 사용하고,
# 없으면 프로젝트 루트의 '법정동코드_전체자료.csv'를 기본값으로 사용합니다.
LAWD_CODE_FILE = os.getenv(
    "LAWD_CODE_FILE_PATH",
    default=str(BASE_DIR.parent / "법정동코드_전체자료.csv")
)
