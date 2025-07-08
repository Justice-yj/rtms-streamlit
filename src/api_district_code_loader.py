# src/api_district_code_loader.py
from __future__ import annotations
import os
import pandas as pd
from typing import Dict

class ApiDistrictCodeLoader:
    """
    FastAPI 환경에서 법정동 코드를 처리하는 클래스.
    Streamlit의 캐싱 기능 대신, 클래스 인스턴스 내에 데이터를 한 번만 로드합니다.
    """
    _instance = None
    _data: Dict[str, Dict[str, str]] | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = cls._instance._build_lawd_dict()
        return cls._instance

    def _load_lawd_table(self) -> pd.DataFrame:
        """
        '법정동코드 전체자료' 원본 파일을 찾아 읽고 정제하여 데이터프레임으로 반환합니다.
        """
        path = None
        # FastAPI 실행 경로를 고려하여 파일 경로 탐색
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for fn in os.listdir(base_dir):
            ext = fn.split(".")[-1].lower()
            if fn.startswith("법정동코드") and ext in {"xlsx", "xls", "csv"}:
                path = os.path.join(base_dir, fn)
                break
        
        if path is None:
            raise FileNotFoundError(f"⚠️ ‘법정동코드…’ 파일을 프로젝트 루트 폴더({base_dir})에 넣어 주세요!")
        print(f"DEBUG: Found file at: {path}")

        ext = path.split(".")[-1].lower()
        if ext in {"xlsx", "xls"}:
            df = pd.read_excel(path, dtype=str)
        else:
            df = pd.read_csv(path, dtype=str, encoding="euc-kr")
        print(f"DEBUG: DataFrame head:\n{df.head()}")

        df.columns = [c.strip() for c in df.columns]
        df = df.rename(columns={"법정동코드": "code", "법정동명": "name", "폐지여부": "status"})
        print(f"DEBUG: Renamed columns and filtered:\n{df.head()}")

        sgg = df[df["code"].str.endswith("00000") & df["status"].eq("존재")].copy()
        print(f"DEBUG: SGG DataFrame head:\n{sgg.head()}")

        parts = sgg["name"].str.split()
        sgg["시도"] = parts.str[0]
        sgg["시군구"] = parts.str[1].fillna(sgg["시도"])
        print(f"DEBUG: Sido/Sigungu added:\n{sgg.head()}")

        sgg["LAWD_CD"] = sgg["code"].str[:5]
        print(f"DEBUG: LAWD_CD added:\n{sgg.head()}")

        return sgg[["시도", "시군구", "LAWD_CD"]]

        ext = path.split(".")[-1].lower()
        if ext in {"xlsx", "xls"}:
            df = pd.read_excel(path, dtype=str)
        else:
            df = pd.read_csv(path, dtype=str, encoding="euc-kr")

        df.columns = [c.strip() for c in df.columns]
        df = df.rename(columns={"법정동코드": "code", "법정동명": "name", "폐지여부": "status"})

        sgg = df[df["code"].str.endswith("00000") & df["status"].eq("존재")].copy()

        parts = sgg["name"].str.split()
        sgg["시도"] = parts.str[0]
        sgg["시군구"] = parts.str[1].fillna(sgg["시도"])

        sgg["LAWD_CD"] = sgg["code"].str[:5]

        return sgg[["시도", "시군구", "LAWD_CD"]]

    def _build_lawd_dict(self) -> Dict[str, Dict[str, str]]:
        """
        정제된 법정동 코드 데이터프레임을 사용하여 중첩 딕셔너리를 생성합니다.
        """
        sgg_df = self._load_lawd_table()
        mapping: Dict[str, Dict[str, str]] = {}
        for _, row in sgg_df.iterrows():
            mapping.setdefault(row["시도"], {})[row["시군구"]] = row["LAWD_CD"]
        return mapping

    def get_code(self, district_name: str) -> str | None:
        """
        전체 시/군/구 데이터에서 입력된 이름과 일치하는 법정동 코드를 찾습니다.
        (예: "종로구" -> "11110")
        """
        if self._data is None:
            return None
            
        for sido, sgg_map in self._data.items():
            if district_name in sgg_map:
                return sgg_map[district_name]
        return None

    def get_sido_list(self) -> list[str]:
        """시도 리스트를 반환합니다."""
        if self._data is None:
            return []
        return list(self._data.keys())

    def get_sgg_list(self, sido: str) -> list[str]:
        """선택된 시도에 해당하는 시군구 리스트를 반환합니다."""
        if self._data is None:
            return []
        return list(self._data.get(sido, {}).keys())