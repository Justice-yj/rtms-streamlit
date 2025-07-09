from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # CORS 미들웨어 임포트
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd

# main.py에서 분리된 로직과 LAWD_CODES를 임포트합니다.
from .main import LAWD_CODES, get_trade_data, get_geocoded_data, get_forecast_data, get_chat_agent

app = FastAPI()

# CORS 미들웨어 추가
origins = [
    "http://localhost",
    "http://localhost:3000", # React 앱의 주소
    "https://roaring-pegasus-7d450e.netlify.app",
    "https://searchbudongsan.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LAWD_DATA는 이제 main.py에서 LAWD_CODES로 관리됩니다.
# find_code_for_district 함수는 LAWD_CODES를 사용하도록 수정합니다.
def find_code_for_district(district_name: str) -> str | None:
    """전체 법정동 데이터에서 주어진 시군구 이름에 해당하는 코드를 찾습니다."""
    for districts in LAWD_CODES.values():
        if district_name in districts:
            return districts[district_name]
    return None

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI! 아파트 실거래가 프로젝트에 오신 것을 환영합니다."}

@app.get("/sido-list")
def get_sido_list_api() -> List[str]:
    """
    전체 시/도 목록을 반환합니다.
    """
    return list(LAWD_CODES.keys())

@app.get("/sgg-list/{sido}")
def get_sgg_list_api(sido: str) -> List[str]:
    """
    선택된 시/도에 해당하는 시/군/구 목록을 반환합니다.
    """
    return list(LAWD_CODES.get(sido, {}).keys())

@app.get("/district-code/{district_name}")
def get_district_code(district_name: str) -> Dict:
    """
    지역 이름(구 단위)을 입력받아 해당하는 법정동 코드를 반환합니다.
    """
    district_code = find_code_for_district(district_name)
    if district_code:
        return {"district_name": district_name, "district_code": district_code}
    raise HTTPException(status_code=404, detail="해당하는 지역을 찾을 수 없습니다.")

# 새로운 /trade-data 엔드포인트 (기존 get_trade_history 대체)
@app.get("/trade-data")
def get_filtered_trade_data(
    lawd_cd: str,
    start_ym: str,
    end_ym: str,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    apt_name: Optional[str] = None,
) -> List[Dict]:
    """
    지정된 기간 동안의 실거래가 데이터를 조회하고 필터링합니다.
    """
    df = get_trade_data(lawd_cd, start_ym, end_ym, min_area, max_area, apt_name)
    if df.empty:
        raise HTTPException(status_code=404, detail="해당 조건에 맞는 거래 내역이 없습니다.")
    return df.to_dict(orient="records")

# geocode-trade-history 엔드포인트 업데이트 (get_geocoded_data 사용)
class TradeHistoryRequest(BaseModel):
    trade_data: List[Dict]

@app.post("/geocode-trade-history")
def geocode_trade_history(request: TradeHistoryRequest) -> List[Dict]:
    """
    실거래가 데이터에 위도, 경도 좌표를 추가합니다.
    """
    if not request.trade_data:
        raise HTTPException(status_code=400, detail="거래 데이터가 비어 있습니다.")

    geocoded_df = get_geocoded_data(request.trade_data)

    if geocoded_df.empty:
        raise HTTPException(status_code=404, detail="좌표를 변환할 수 있는 주소가 없습니다.")

    return geocoded_df.to_dict(orient="records")

# 새로운 /forecast 엔드포인트
class ForecastRequest(BaseModel):
    trade_data: List[Dict]
    periods: Optional[int] = 12

@app.post("/forecast")
def get_apartment_forecast(request: ForecastRequest) -> Dict:
    """
    주어진 실거래가 데이터로 아파트 가격을 예측합니다.
    """
    if not request.trade_data:
        raise HTTPException(status_code=400, detail="예측을 위한 거래 데이터가 비어 있습니다.")

    # 서비스 로직(get_forecast_data)은 DataFrame을 인자로 받으므로,
    # 요청으로 받은 list[dict]를 DataFrame으로 변환합니다.

    df_for_forecast = pd.DataFrame(request.trade_data)
    if df_for_forecast.empty:
        raise HTTPException(status_code=400, detail="예측을 위한 유효한 거래 데이터가 없습니다.")

    # '거래일' 컬럼을 datetime 객체로 변환합니다. 이것이 누락되어 에러가 발생했습니다.
    if '거래일' in df_for_forecast.columns:
        df_for_forecast['거래일'] = pd.to_datetime(df_for_forecast['거래일'], errors='coerce')
    else:
        # '거래일' 컬럼이 없으면 예측을 수행할 수 없으므로 에러를 발생시킵니다.
        raise HTTPException(status_code=400, detail="예측에 필요한 '거래일' 필드가 데이터에 없습니다.")

    hist_df, fcst_df = get_forecast_data(df_for_forecast, request.periods)

    if hist_df is None or fcst_df is None:
        raise HTTPException(status_code=400, detail="예측을 수행할 수 없습니다. 데이터가 충분한지 확인하세요.")

    return {
        "historical_data": hist_df.to_dict(orient="records"),
        "forecast_data": fcst_df.to_dict(orient="records"),
    }

# 챗봇 에이전트 엔드포인트 (상태 관리가 필요하므로 초기 버전에서는 간단히 구현)
class ChatRequest(BaseModel):
    trade_data: List[Dict]
    question: str

@app.post("/chat")
def chat_with_agent(request: ChatRequest) -> Dict:
    """
    주어진 데이터에 대해 AI 챗봇에게 질문하고 답변을 받습니다.
    """
    if not request.trade_data:
        raise HTTPException(status_code=400, detail="챗봇을 위한 거래 데이터가 비어 있습니다.")

    df_for_chat = pd.DataFrame(request.trade_data)
    if df_for_chat.empty:
        raise HTTPException(status_code=400, detail="챗봇을 위한 유효한 거래 데이터가 없습니다.")

    try:
        agent = get_chat_agent(df_for_chat)
        answer = agent.run(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 에이전트 실행 중 오류 발생: {e}")
