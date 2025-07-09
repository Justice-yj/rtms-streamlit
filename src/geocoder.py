# geocoder.py - 주소-좌표 변환 모듈
# VWorld API를 사용하여 도로명 주소를 위도/경도 좌표로 변환합니다.
# 변환된 결과는 캐시하여 반복적인 API 요청을 최소화합니다.
from __future__ import annotations
from functools import lru_cache

import pandas as pd
import requests
import time
from .config import VWORLD_API_KEY  # config에서 API 키 임포트

# --- VWorld API를 이용한 지오코딩 함수 ---
def _vworld_geocode(address: str) -> tuple[float, float] | None:
    """
    VWorld API를 사용하여 주소를 위도, 경도로 변환합니다.
    """
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "EPSG:4326",  # WGS84 경위도 좌표계
        "address": address,
        "type": "road",  # 도로명 주소 검색
        "format": "json",
        "key": VWORLD_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        
        # VWorld API 응답의 내부 상태를 확인
        response_status = json_data.get("response", {}).get("status")

        if response_status == "OK":
            point = json_data.get("response", {}).get("result", {}).get("point", {})
            if point and "x" in point and "y" in point:
                # VWorld API는 경도(x), 위도(y)를 반환합니다
                return float(point["y"]), float(point["x"])
        else:
            # API가 'NOT_FOUND', 'ERROR' 등의 상태를 반환한 경우
            print(f"[VWorld API Status Error] for '{address}': {response_status}")
            
    except requests.exceptions.RequestException as e: # 네트워크 관련 오류
        print(f"[VWorld Geocoding Request Error] for '{address}': {e}")
    except ValueError: # JSON 디코딩 오류
        print(f"[VWorld Geocoding JSON Error] for '{address}': Invalid JSON response from server")
    return None


# --- 지오코딩(주소 -> 좌표) 함수 ---
@lru_cache(maxsize=None)
def geocode_addresses(addresses: tuple[str]) -> pd.DataFrame:
    """
    주소 목록(tuple)을 받아 위도와 경도를 포함한 데이터프레임으로 반환합니다.
    lru_cache를 위해 hashable한 tuple을 인자로 받습니다.

    Args:
        addresses (tuple[str]): 도로명 주소를 담고 있는 튜플.

    Returns:
        pd.DataFrame: 입력된 주소와 함께 'latitude', 'longitude' 컬럼이 추가된 데이터프레임.
    """
    results = []

    for addr in addresses:
        latlon = _vworld_geocode(addr)
        results.append({
            "도로명": addr,
            "latitude": latlon[0] if latlon else None,
            "longitude": latlon[1] if latlon else None,
        })
        time.sleep(0.11)  # QPS 제한 (VWorld는 초당 9건 이하 권장)

    return pd.DataFrame(results)


# --- 좌표 추가 함수 ---
def add_coordinates_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    원본 데이터프레임에 위도, 경도 좌표를 추가합니다.

    Args:
        df (pd.DataFrame): '도로명' 컬럼을 포함한 원본 데이터프레임.

    Returns:
        pd.DataFrame: 'latitude', 'longitude' 컬럼이 추가된 데이터프레임.
                      좌표를 찾지 못한 행은 제거됩니다.
    """
    if "도로명" not in df.columns or df["도로명"].isna().all():
        return df

    # 캐시를 위해 유니크한 주소 목록을 튜플로 변환
    unique_addrs = tuple(df["도로명"].dropna().astype(str).unique())
    if not unique_addrs:
        return df

    geo_df = geocode_addresses(unique_addrs)
    if geo_df.empty:
        # Add empty coordinate columns to match schema if geocoding returns nothing
        return df.assign(latitude=pd.NA, longitude=pd.NA)

    merged_df = pd.merge(df, geo_df, on="도로명", how="left")
    return merged_df
