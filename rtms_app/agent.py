# rtms_app/agent.py
from __future__ import annotations

import os
import pandas as pd
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.agents import AgentType

###############################################################################
# LangChain Pandas DataFrame Agent
###############################################################################
@st.cache_resource(show_spinner=False)
def get_df_agent(dataframe: pd.DataFrame):
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model_name="gpt-4o",
        temperature=0.2,
    )

    prefix = (
        "너는 한국 아파트 실거래 데이터 분석 비서야. "
        "**반드시 제공된 DataFrame 변수 `df`만 사용**하고, "
        "외부 파일(예: CSV, Excel)을 읽지 마라. "
        "매 답변 전 python을 호출해 결과를 검증해. "
        "출력은 df.head(20)·describe() 등 20행 이하 요약만 보여줘."
    )
    suffix = f"열 목록: {', '.join(dataframe.columns)}\n\n자, 이제 사용자 질문을 기다려!"

    agent = create_pandas_dataframe_agent(
        llm,
        dataframe,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        prefix=prefix,
        suffix=suffix,
        include_df_in_prompt=None,
        allow_dangerous_code=True,
        verbose=True,
        return_intermediate_steps=False,
        max_iterations=8,
        handle_parsing_errors=True,
    )
    return agent


