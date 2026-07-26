import streamlit as st

# ECOS API Key
ECOS_API_KEY = st.secrets.get("ECOS_API_KEY")

# ECOS 기본 URL
ECOS_BASE_URL = "https://ecos.bok.or.kr/api"

# 예측 기간
FORECAST_MONTHS = 6

# 정책 단계
POLICY_STAGE = {
    0: {"name": "정책 없음", "effect": 0.00},
    1: {"name": "소폭 지원", "effect": -0.15},
    2: {"name": "적극 지원", "effect": -0.35},
    3: {"name": "강력 지원", "effect": -0.55},
}
