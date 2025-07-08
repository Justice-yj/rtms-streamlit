# api.py - 국토교통부 실거래가 API 연동 모듈
# RTMS(Real Estate Transaction Management System) API로부터 아파트 매매 실거래 데이터를
# 요청하고, 결과를 Pandas DataFrame으로 정제하여 반환합니다.
# API 요청은 병렬로 처리하여 응답 속도를 최적화합니다.
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta

from .config import ENDPOINT, SERVICE_KEY

# --- 1. 단일 월 데이터 요청 함수 ---
def fetch_rtms(lawd_cd: str, deal_ymd: str, rows: int = 1000, page: int = 1) -> pd.DataFrame:
    """
    특정 지역(법정동 코드)의 한 달치 실거래 데이터를 API로부터 조회합니다.

    Args:
        lawd_cd (str): 5자리 법정동 코드 (예: "11110")
        deal_ymd (str): 조회할 년월 (YYYYMM 형식, 예: "202301")
        rows (int, optional): 한 번에 가져올 데이터 행 수. Defaults to 1000.
        page (int, optional): 페이지 번호. Defaults to 1.

    Returns:
        pd.DataFrame: 조회된 실거래 데이터를 담은 데이터프레임.
                      데이터가 없거나 오류 발생 시 빈 데이터프레임을 반환할 수 있음.
    """
    # API 요청 파라미터 설정
    params: Dict[str, Any] = {
        "serviceKey": SERVICE_KEY,  # 인증키
        "LAWD_CD": lawd_cd,         # 법정동 코드
        "DEAL_YMD": deal_ymd,       # 조회년월
        "numOfRows": rows,          # 행 수
        "pageNo": page,             # 페이지 번호
    }
    try:
        # API 요청 및 예외 처리 (타임아웃 10초)
        res = requests.get(ENDPOINT, params=params, timeout=10)
        res.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        # XML 응답 파싱
        root = ET.fromstring(res.content)
        # API 응답 헤더의 결과 메시지 확인
        if root.findtext("./header/resultMsg") != "OK":
            msg = root.findtext("./header/resultMsg") or "Unknown API error"
            print(f"[API Error] {deal_ymd}: {msg}")
            return pd.DataFrame() # 오류 발생 시 빈 데이터프레임 반환

        # XML item을 순회하며 딕셔너리 리스트 생성
        items: List[Dict[str, Any]] = []
        for it in root.findall(".//item"):
            g = it.findtext
            items.append({
                "아파트": g("aptNm"),
                "거래금액(만원)": g("dealAmount"),
                "deal_amount": g("dealAmount"), # 그래프용 필드 추가
                "전용면적(m²)": g("excluUseAr"),
                "층": g("floor"),
                "건축년도": g("buildYear"),
                "거래일": f"{g('dealYear')}-{g('dealMonth'):0>2}-{g('dealDay'):0>2}",
                "deal_year": g("dealYear"), # 그래프용 필드 추가
                "deal_month": g("dealMonth"), # 그래프용 필드 추가
                "도로명": g("roadNm"),
            })

        # 데이터프레임 생성 및 데이터 타입 정제
        df = pd.DataFrame(items)
        if not df.empty:
            df["거래금액(만원)"] = pd.to_numeric(df["거래금액(만원)"].str.replace(",", ""), errors="coerce")
            df["전용면적(m²)"] = pd.to_numeric(df["전용면적(m²)"], errors="coerce")
            df["층"] = pd.to_numeric(df["층"], errors="coerce")
            df["건축년도"] = pd.to_numeric(df["건축년도"], errors="coerce")
            df["거래일"] = pd.to_datetime(df["거래일"], errors="coerce")
        return df

    except requests.exceptions.RequestException as e:
        print(f"[Request Error] {deal_ymd}: {e}")
        return pd.DataFrame() # 네트워크 오류 시 빈 데이터프레임 반환

# --- 2. 기간별 데이터 조회 및 병합 함수 ---
def month_range(start_ym: str, end_ym: str) -> List[str]:
    """
    시작년월과 종료년월 사이의 모든 년월(YYYYMM) 리스트를 생성합니다.
    """
    start = datetime.strptime(start_ym, "%Y%m")
    end = datetime.strptime(end_ym, "%Y%m")
    if start > end:
        start, end = end, start

    months: List[str] = []
    current = start
    while current <= end:
        months.append(current.strftime("%Y%m"))
        current += relativedelta(months=1)
    return months

def fetch_rtms_range(lawd_cd: str, start_ym: str, end_ym: str) -> pd.DataFrame:
    """
    지정된 기간 동안의 실거래 데이터를 **병렬로 조회**하여 하나의 데이터프레임으로 병합합니다.

    Args:
        lawd_cd (str): 5자리 법정동 코드.
        start_ym (str): 조회 시작년월 (YYYYMM).
        end_ym (str): 조회 종료년월 (YYYYMM).

    Returns:
        pd.DataFrame: 지정된 기간의 모든 실거래 데이터를 담은 데이터프레임.
    """
    ym_list = month_range(start_ym, end_ym)
    frames = []
    # ThreadPoolExecutor를 사용하여 API 요청을 병렬로 처리
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 각 년월별로 fetch_rtms 함수를 실행하는 작업을 제출
        future_to_ym = {executor.submit(fetch_rtms, lawd_cd, ym): ym for ym in ym_list}

        # 작업이 완료되는 순서대로 결과를 처리
        for future in as_completed(future_to_ym):
            try:
                df = future.result()
                if not df.empty:
                    frames.append(df)
            except Exception as e:
                ym = future_to_ym[future]
                print(f"[Future Error] {ym}: {e}")

    # 모든 데이터프레임을 하나로 합침
    if not frames:
        return pd.DataFrame()

    # 월(거래일) 기준으로 정렬하여 최종 결과 반환
    return pd.concat(frames, ignore_index=True).sort_values(by="거래일").reset_index(drop=True)
