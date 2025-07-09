# forecast.py - 시계열 예측 모듈
# Prophet 라이브러리를 사용하여 아파트 평균 거래가의 미래 추세를 예측합니다.
from __future__ import annotations
from typing import Tuple
import pandas as pd
from prophet import Prophet

# --- Prophet 모델 학습 ---
# @st.cache_resource는 Streamlit 전용 기능이므로 FastAPI 환경에서는 사용할 수 없습니다.
# 우선 캐싱 없이 모델을 학습하도록 수정하여 앱이 정상 동작하도록 합니다.
def train_prophet(ts_df: pd.DataFrame) -> Prophet:
    """
    Prophet 모델을 학습시킵니다.

    Args:
        ts_df (pd.DataFrame): 'ds'(날짜)와 'y'(수치) 컬럼을 가진 시계열 데이터프레임.

    Returns:
        Prophet: 학습된 Prophet 모델 객체.
    """
    # Prophet 모델 초기화
    # 아파트 가격은 월 단위 추세가 중요하므로, 연/주/일 계절성은 비활성화합니다.
    # seasonality_mode='multiplicative'는 계절성 효과가 추세에 따라 변할 때 유용합니다.
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.3,  # 추세 변화 감지 민감도 조절
    )
    # 데이터로 모델 학습
    model.fit(ts_df)
    return model

# --- 가격 예측 실행 ---
def make_forecast(raw_df: pd.DataFrame,
                  periods: int = 12) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    주어진 실거래 데이터프레임을 기반으로 미래 가격을 예측합니다.

    Args:
        raw_df (pd.DataFrame): 필터링된 실거래 데이터.
        periods (int, optional): 예측할 기간(월 단위). Defaults to 12.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - hist_df (pd.DataFrame): 모델 학습에 사용된 과거 데이터.
            - forecast_df (pd.DataFrame): 미래 예측 결과 데이터.

    Raises:
        ValueError: 예측에 필요한 데이터가 2개 미만일 경우 발생.
    """
    # --- ① 데이터 전처리: Prophet 입력 형식으로 변환 ---
    # 월별 평균 거래가를 계산하고, Prophet이 요구하는 'ds'와 'y' 컬럼명으로 변경합니다.
    ts_df = (
        raw_df
        .assign(ds=raw_df["거래일"].dt.to_period("M").astype(str) + "-01") # 날짜를 월초로 통일
        .groupby("ds")["거래금액(만원)"].mean()
        .reset_index()
        .rename(columns={"거래금액(만원)": "y"})
    )
    ts_df["ds"] = pd.to_datetime(ts_df["ds"])

    # Prophet은 최소 2개 이상의 데이터 포인트가 필요합니다.
    if len(ts_df) < 2:
        raise ValueError("예측을 위해서는 월별 데이터가 최소 2개 이상 필요합니다.")

    # --- ② 모델 학습 ---
    # 캐시된 train_prophet 함수를 호출하여 모델을 학습시킵니다.
    model = train_prophet(ts_df)

    # --- ③ 미래 예측 ---
    # 지정된 기간(periods)만큼 미래 날짜 데이터프레임을 생성합니다.
    future = model.make_future_dataframe(periods=periods, freq="MS") # MS: 월 시작일 기준
    # 생성된 미래 데이터프레임으로 예측을 수행합니다.
    # 결과에는 예측값(yhat), 신뢰구간(yhat_lower, yhat_upper) 등이 포함됩니다.
    forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    # --- 결과 반환 ---
    # 학습에 사용된 과거 데이터와, 예측된 미래 데이터(마지막 `periods`개)를 분리하여 반환합니다.
    return ts_df, forecast.tail(periods)
