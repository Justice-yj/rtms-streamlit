# agent.py - LangChain AI 에이전트 생성 모듈
# 사용자의 자연어 질문을 이해하고, Pandas DataFrame에서 정보를 찾아 답변하는
# AI 에이전트를 생성하고 관리합니다.
from __future__ import annotations

import os
import pandas as pd
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.agents import AgentType

# --- Pandas DataFrame 분석용 AI 에이전트 생성 ---
# @st.cache_resource: 동일한 데이터프레임에 대해서는 에이전트 객체를 캐시하여
# 중복 생성을 방지하고 리소스를 절약합니다.
def get_df_agent(dataframe: pd.DataFrame):
    """
    주어진 Pandas DataFrame을 분석하고 질문에 답변할 수 있는 LangChain 에이전트를 생성합니다.

    Args:
        dataframe (pd.DataFrame): 분석의 대상이 되는 데이터프레임.

    Returns:
        AgentExecutor: 설정된 LLM과 데이터프레임으로 초기화된 LangChain 에이전트.
    """
    # --- 1. LLM (Large Language Model) 설정 ---
    # OpenAI의 gpt-4o 모델을 사용하여 에이전트의 두뇌 역할을 하도록 설정합니다.
    # temperature=0.2: 모델의 답변이 일관성 있고 예측 가능하도록 설정 (낮을수록 결정적)
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o",
        temperature=0.2,
    )

    # --- 2. 에이전트 프롬프트(지침) 설정 ---
    # prefix: 에이전트에게 역할을 부여하고, 행동의 기본 규칙을 명시합니다.
    prefix = (
        "너는 한국 아파트 실거래 데이터 분석 전문 AI 비서야. "
        "사용자의 질문에 답변할 때는 **반드시 제공된 `df`라는 이름의 DataFrame만 사용**해야 해. "
        "절대로 외부 파일(CSV, Excel 등)을 임의로 읽거나 외부 웹사이트를 참조해서는 안 돼. "
        "모든 답변은 `df` 내의 데이터를 기반으로 생성해야 하며, "
        "답변을 하기 전에 먼저 `python_repl_ast` 툴을 사용해서 데이터를 확인하고 계산해. "
        "데이터를 직접 보여줄 때는 `head()`나 `describe()` 같은 요약 정보를 사용하고, 최대 20행까지만 출력해줘."
    )
    # suffix: 에이전트가 사용할 수 있는 도구와 입력 형식을 안내합니다.
    suffix = f"사용 가능한 컬럼 목록: {list(dataframe.columns)}\n\n이제 사용자의 질문을 바탕으로 작업을 시작해줘!"

    # --- 3. 에이전트 생성 ---
    # create_pandas_dataframe_agent: DataFrame 조작에 특화된 에이전트를 쉽게 생성하는 함수
    agent = create_pandas_dataframe_agent(
        llm=llm,                            # 사용할 언어 모델
        df=dataframe,                       # 분석할 데이터프레임
        agent_type=AgentType.OPENAI_FUNCTIONS, # 최신 OpenAI 모델의 함수 호출 기능 활용
        prefix=prefix,                      # 역할/규칙 프롬프트
        suffix=suffix,                      # 도구/입력 프롬프트
        include_df_in_prompt=None,          # 프롬프트에 데이터프레임 전체를 포함할지 여부 (토큰 절약)
        allow_dangerous_code=True,          # 에이전트가 생성한 파이썬 코드를 실행하도록 허용
        verbose=True,                       # 에이전트의 생각/행동 과정을 로그로 출력
        return_intermediate_steps=False,    # 중간 결과 반환 여부
        max_iterations=8,                   # 작업 당 최대 반복 횟수 (무한 루프 방지)
        handle_parsing_errors=True,         # 모델의 출력 파싱 오류 발생 시 대처
    )
    return agent


