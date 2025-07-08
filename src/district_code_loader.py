# lawd.py - 법정동 코드 처리 모듈
# '법정동코드 전체자료' 파일을 읽어, Streamlit UI에서 사용할
# {시도: {시군구: 법정동코드}} 형태의 딕셔너리를 생성합니다.
from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict
from pathlib import Path

import pandas as pd

# --- 1. 법정동 코드 원본 파일 로드 및 정제 ---
@lru_cache(maxsize=1)
def load_lawd_table() -> pd.DataFrame:
    """
    '법정동코드 전체자료' 원본 파일(CSV 또는 Excel)을 찾아 읽어온 후,
    API 조회에 필요한 [시도, 시군구, 법정동코드(5자리)] 컬럼만 추출하여
    데이터프레임으로 반환합니다.

    - Streamlit의 `@st.cache_data`를 사용하여 결과를 캐시합니다.

    Returns:
        pd.DataFrame: 정제된 법정동 코드 데이터프레임.

    Raises:
        FileNotFoundError: '법정동코드'로 시작하는 파일이 없을 경우 발생합니다.
    """
    # --- ① 파일 탐색 ---
    # 현재 스크립트 파일의 디렉토리를 기준으로 파일을 찾습니다.
    base_dir = Path(__file__).parent.parent
    path = base_dir / "법정동코드_전체자료.csv"

    if not path.exists():
        raise FileNotFoundError(f"⚠️ '{path}' 파일을 찾을 수 없습니다!")
    print(f"DEBUG: Found file at: {path}")

    # --- ② 파일 읽기 ---
    # 파일 확장자에 따라 적절한 Pandas 함수로 데이터를 읽어옵니다.
    ext = path.suffix.lower()
    if ext in {".xlsx", ".xls"}:
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str, encoding="cp949")
    print(f"DEBUG: DataFrame head:\n{df.head()}")

    # --- ③ 데이터 정제 및 필터링 ---
    # 컬럼명의 불필요한 공백을 제거하고, 표준 컬럼명으로 변경합니다.
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"법정동코드": "code", "법정동명": "name", "폐지여부": "status"})
    print(f"DEBUG: Renamed columns and filtered:\n{df.head()}")

    # '존재'하는 법정동 중에서 시/군/구 단위(코드 마지막 5자리가 '00000')만 필터링합니다.
    sgg = df[df["code"].str.endswith("00000") & df["status"].eq("존재")].copy()
    print(f"DEBUG: SGG DataFrame head:\n{sgg.head()}")

    # '법정동명'에서 '시도'와 '시군구'를 분리합니다.
    # (예: '서울특별시 종로구' -> '서울특별시', '종로구')
    parts = sgg["name"].str.split()
    sgg["시도"] = parts.str[0]
    sgg["시군구"] = parts.str[1].fillna(sgg["시도"]) # 세종특별자치시 등 단일 이름 처리
    print(f"DEBUG: Sido/Sigungu added:\n{sgg.head()}")

    # API에서 사용할 5자리 법정동 코드를 추출합니다.
    sgg["LAWD_CD"] = sgg["code"].str[:5]
    print(f"DEBUG: LAWD_CD added:\n{sgg.head()}")

    return sgg[["시도", "시군구", "LAWD_CD"]]

# --- 2. UI용 중첩 딕셔너리 생성 ---
@lru_cache(maxsize=1)
def build_lawd_dict() -> Dict[str, Dict[str, str]]:
    """
    정제된 법정동 코드 데이터프레임을 사용하여
    UI의 Selectbox를 동적으로 채우기 위한 중첩 딕셔너리를 생성합니다.

    - 구조: { "서울특별시": { "종로구": "11110", "중구": "11140", ... } }

    Returns:
        Dict[str, Dict[str, str]]: 시도, 시군구, 법정동 코드로 구성된 중첩 딕셔너리.
    """
    sgg_df = load_lawd_table()
    mapping: Dict[str, Dict[str, str]] = {}
    for _, row in sgg_df.iterrows():
        # setdefault를 이용해 시/도 키가 없으면 빈 딕셔너리를 생성하고, 시군구와 코드를 추가
        mapping.setdefault(row["시도"], {})[row["시군구"]] = row["LAWD_CD"]
    return mapping
