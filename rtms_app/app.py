# rtms_app/app.py
from __future__ import annotations

import streamlit as st
from datetime import datetime

from rtms_app.lawd import build_lawd_dict
from rtms_app.api import fetch_rtms_range
from rtms_app.agent import get_df_agent

###############################################################################
# 전역: LAWD 코드 딕셔너리 캐시
###############################################################################
LAWD_CODES = build_lawd_dict()

###############################################################################
# Streamlit 앱
###############################################################################
def run() -> None:
    st.set_page_config(page_title="RTMS 실거래가 + AI Q&A", page_icon="🏠", layout="wide")
    st.title("🏠 RTMS 아파트 매매 실거래가 조회기 + 💬 AI Q&A")

    if "raw_df" not in st.session_state:
        st.session_state.raw_df = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ── 📌 사이드바: 조회 조건 입력 ──────────────────────────────────────────
    with st.sidebar:
        st.subheader("🔍 조회 조건")

        priority = ["서울특별시", "대전광역시"]
        ordered_cities = priority + [c for c in sorted(LAWD_CODES) if c not in priority]
        city = st.selectbox("시/도", ordered_cities, index=0)

        district = st.selectbox("시/군/구", sorted(LAWD_CODES[city]))
        lawd_cd = LAWD_CODES[city][district]
        st.caption(f"법정동 코드: **{lawd_cd}**")

        today_ym = datetime.now().strftime("%Y%m")
        start_ym = st.text_input("시작년월 (YYYYMM)", value=today_ym)
        end_ym = st.text_input("종료년월 (YYYYMM)", value=today_ym)
        fetch_btn = st.button("📥 데이터 조회")

    # ── ① 데이터 조회 ─────────────────────────────────────────────────────
    if fetch_btn:
        with st.spinner("RTMS API에서 데이터를 불러오는 중…"):
            st.session_state.raw_df = fetch_rtms_range(lawd_cd, start_ym, end_ym)
            st.session_state.messages.clear()

    # ── ② 결과 + 필터 + 시각화 ──────────────────────────────────────────────
    if st.session_state.raw_df is not None and not st.session_state.raw_df.empty:
        raw_df = st.session_state.raw_df

        # 전용면적 필터
        min_a, max_a = int(raw_df["전용면적(m²)"].min()), int(raw_df["전용면적(m²)"].max())
        area_range = st.sidebar.slider("전용면적 (m²)", min_a, max_a, (min_a, max_a), 1)
        df = raw_df[
             (raw_df["전용면적(m²)"] >= area_range[0]) &
             (raw_df["전용면적(m²)"] <= area_range[1])
             ]
        
        st.success(f"🔎 조건에 맞는 거래 {len(df):,}건 (원본 {len(raw_df):,}건)")
        st.dataframe(df, use_container_width=True)

        # 월별 평균 거래가
        if not df.empty:
            chart_df = (
                df.assign(거래월=df["거래일"].dt.to_period("M").astype(str))
                  .groupby("거래월")["거래금액(만원)"]
                  .mean()
                  .reset_index()
                  .rename(columns={"거래금액(만원)": "평균거래가(만원)"})
            )
            st.line_chart(chart_df, x="거래월", y="평균거래가(만원)")

        st.download_button(
            "CSV로 저장하기",
            data=df.to_csv(index=False).encode(),
            file_name=f"rtms_{lawd_cd}_{start_ym}_{end_ym}.csv",
            mime="text/csv",
        )

        # ── ③ AI Q&A ────────────────────────────────────────────────────
        st.divider(); st.subheader("💬 AI Q&A (LangChain)")

        if "agent_df_id" not in st.session_state or st.session_state.agent_df_id != id(df):
            st.session_state.agent = get_df_agent(df)
            st.session_state.agent_df_id = id(df)

        agent = st.session_state.agent

        # 이전 대화 렌더링
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_q = st.chat_input("궁금한 점을 물어보세요!")
        if user_q:
            st.session_state.messages.append({"role": "user", "content": user_q})
            with st.chat_message("user"):
                st.markdown(user_q)

            with st.chat_message("assistant"):
                with st.spinner("🦊 계산 중…"):
                    try:
                        answer = agent.run(user_q)
                    except Exception as e:
                        answer = f"❌ 에이전트 오류: {e}"
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    else:
        st.info("먼저 사이드바에서 조회 조건을 설정하고 **데이터 조회** 버튼을 눌러주세요!")

###############################################################################
# ⛳️  엔트리포인트
###############################################################################
if __name__ == "__main__":
    run()
