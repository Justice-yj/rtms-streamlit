from __future__ import annotations

# main.py - 메인 애플리케이션 (FastAPI 백엔드 로직 포함)

import pandas as pd
from datetime import datetime

from .district_code_loader import build_lawd_dict
from .rtms_client import fetch_rtms_range
from .chatbot_agent import get_df_agent
from .price_predictor import make_forecast
from .geocoder import add_coordinates_to_df # 지도 기능 임포트

# --- 전역 설정 ---
LAWD_CODES = build_lawd_dict()

# --- 핵심 로직 함수 (FastAPI 엔드포인트에서 호출될 예정) ---

def get_trade_data(lawd_cd: str, start_ym: str, end_ym: str,
                   min_area: float | None = None, max_area: float | None = None,
                   apt_name: str | None = None) -> pd.DataFrame:
    """
    지정된 기간 동안의 실거래가 데이터를 조회하고 필터링합니다.
    """
    df = fetch_rtms_range(lawd_cd, start_ym, end_ym)
    if df.empty:
        return pd.DataFrame()

    # Apply area filter
    if min_area is not None:
        df = df[df["전용면적(m²)"] >= min_area]
    if max_area is not None:
        df = df[df["전용면적(m²)"] <= max_area]

    # Apply apartment name filter
    if apt_name:
        df = df[df["아파트"].str.contains(apt_name, case=False, na=False)]

    return df

def get_geocoded_data(trade_data: list[dict]) -> pd.DataFrame:
    """
    실거래가 데이터에 위도, 경도 좌표를 추가합니다.
    """
    df = pd.DataFrame(trade_data)
    if df.empty:
        return pd.DataFrame()

    if '거래일' in df.columns:
        df['거래일'] = pd.to_datetime(df['거래일'], errors='coerce')

    geocoded_df = add_coordinates_to_df(df.copy())
    return geocoded_df

def get_forecast_data(df: pd.DataFrame, periods: int = 12):
    """
    주어진 데이터프레임으로 가격 예측을 수행합니다.
    """
    # --- 데이터 유효성 검사 및 전처리 ---
    # 예측에 필요한 '거래일' 컬럼이 있는지, datetime 타입인지 확인하고 변환합니다.
    if '거래일' not in df.columns:
        # 실제로는 에러를 발생시키는 것이 더 좋습니다.
        return None, None

    # object 타입을 datetime으로 변환
    if not pd.api.types.is_datetime64_any_dtype(df['거래일']):
        df['거래일'] = pd.to_datetime(df['거래일'], errors='coerce')

    # 유효하지 않은 날짜나 금액이 있는 행 제거
    df.dropna(subset=['거래일', '거래금액(만원)'], inplace=True)

    if len(df) < 10:
        # 데이터가 너무 적을 경우 예측 불가 또는 신뢰도 낮음
        return None, None # 또는 적절한 에러 처리
    
    hist_df, fcst_df = make_forecast(df, periods=periods)
    return hist_df, fcst_df

def get_chat_agent(df: pd.DataFrame):
    """
    데이터프레임 기반의 챗봇 에이전트를 생성합니다.
    """
    return get_df_agent(df)
