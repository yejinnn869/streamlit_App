import streamlit as st

from config import (
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT
)

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

# ===============================
# CSS
# ===============================

st.markdown("""
<style>

.main-title{
    font-size:42px;
    font-weight:bold;
    color:#2563EB;
}

.sub-title{
    font-size:20px;
    color:gray;
}

.card{

    padding:20px;

    border-radius:15px;

    background:#F8FAFC;

    border:1px solid #E5E7EB;

    margin-bottom:20px;

}

.metric{

    text-align:center;

    font-size:20px;

    font-weight:bold;

}

.footer{

    color:gray;

    text-align:center;

}

</style>
""", unsafe_allow_html=True)

# ===============================
# Sidebar
# ===============================

st.sidebar.title("🏦 메뉴")

menu = st.sidebar.radio(

    "선택",

    [

        "홈",

        "개인 재무 리포트",

        "국가 거시경제 리스크"

    ]

)

# ===============================
# Home
# ===============================

if menu=="홈":

    st.markdown(
        '<p class="main-title">AI 금융 리스크 예측 시스템</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="sub-title">ECOS Open API 기반 머신러닝 금융 예측</p>',
        unsafe_allow_html=True
    )

    st.divider()

    col1,col2=st.columns(2)

    with col1:

        st.markdown("""
<div class="card">

### 👤 개인 재무 리포트

- DSR 계산

- AI 금리 예측

- 연체율 예측

- 위험등급

- PDF 다운로드

- 스트레스 테스트

</div>
""",unsafe_allow_html=True)

    with col2:

        st.markdown("""
<div class="card">

### 🇰🇷 국가 거시경제 리스크

- CD(91일) 금리 예측

- 국가 DSR 지수

- 가계대출 연체율

- 정부 정책 시뮬레이션

- 위험도 분석

</div>
""",unsafe_allow_html=True)

    st.divider()

    st.subheader("📊 사용 데이터")

    st.write("""
- CD(91일) 금리
- 소비자물가지수(CPI)
- 원/달러 환율
- M2 통화량
- 가계신용
- GDP
- 정부 금융지원 정책(0~3단계)
""")

    st.subheader("🤖 머신러닝")

    st.info("""
RandomForest

+

XGBoost

+

LightGBM

↓

Stacking Ensemble
""")

    st.divider()

    st.caption("Made with Streamlit + ECOS Open API")

# ===============================
# 개인 재무
# ===============================

elif menu=="개인 재무 리포트":

    st.header("👤 개인 재무 리포트")

    st.info("다음 Part에서 구현됩니다.")

# ===============================
# 국가
# ===============================

elif menu=="국가 거시경제 리스크":

    st.header("🇰🇷 국가 거시경제 리스크")

    st.info("다음 Part에서 구현됩니다.")
