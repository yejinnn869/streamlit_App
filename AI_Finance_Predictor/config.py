# config.py

import streamlit as st

# ==============================
# ECOS API 설정
# ==============================

ECOS_API_KEY = st.secrets.get("ECOS_API_KEY", "")

ECOS_BASE_URL = "https://ecos.bok.or.kr/api"

# ==============================
# 예측 설정
# ==============================

FORECAST_MONTHS = 6

RANDOM_STATE = 42

TEST_SIZE = 0.2

# ==============================
# 정부 금융지원 정책
# (사용자가 슬라이더로 선택)
# ==============================

POLICY_STAGE = {
    0: {
        "name": "정책 없음",
        "interest_effect": 0.00,
        "delinquency_effect": 0.00,
        "description": "시장 상황만 반영"
    },
    1: {
        "name": "소폭 지원",
        "interest_effect": -0.15,
        "delinquency_effect": -0.05,
        "description": "부분적인 금융지원"
    },
    2: {
        "name": "적극 지원",
        "interest_effect": -0.35,
        "delinquency_effect": -0.10,
        "description": "대규모 금융지원"
    },
    3: {
        "name": "강력 지원",
        "interest_effect": -0.55,
        "delinquency_effect": -0.20,
        "description": "상환유예 및 적극 지원"
    }
}

# ==============================
# 개인 위험등급
# ==============================

PERSONAL_RISK = {
    "A": (0, 20),
    "B": (20, 40),
    "C": (40, 60),
    "D": (60, 80),
    "E": (80, 100)
}

# ==============================
# DSR 기준
# ==============================

DSR_LEVEL = {
    "안전": 20,
    "주의": 40,
    "위험": 60
}

# ==============================
# 예상 연체율 기준(%)
# ==============================

DELINQUENCY_LEVEL = {
    "안전": 0.30,
    "주의": 0.80,
    "위험": 1.50
}

# ==============================
# 스트레스 테스트
# ==============================

STRESS_RATE = [
    -1.00,
    -0.50,
    0.50,
    1.00,
    2.00
]

# ==============================
# 머신러닝 입력 변수
# ==============================

FEATURE_COLUMNS = [

    "cd91",

    "base_rate",

    "cpi",

    "exchange",

    "m2",

    "kospi",

    "unemployment",

    "household_credit",

    "household_debt",

    "gdp",

    "policy_stage"

]

# ==============================
# 예측 대상
# ==============================

TARGET_RATE = "cd91"

TARGET_DELINQUENCY = "delinquency"

# ==============================
# 국가 DSR 지수 계산 변수
# ==============================

NATIONAL_DSR_WEIGHT = {

    "household_debt": 0.35,

    "gdp": -0.25,

    "cd91": 0.20,

    "household_credit": 0.10,

    "unemployment": 0.10

}

# ==============================
# 그래프 색상
# ==============================

COLORS = {

    "primary": "#2563EB",

    "secondary": "#16A34A",

    "danger": "#DC2626",

    "warning": "#F59E0B",

    "purple": "#7C3AED"

}

# ==============================
# PDF
# ==============================

PDF_TITLE = "AI 금융 리스크 예측 리포트"

PDF_AUTHOR = "AI Finance Predictor"

# ==============================
# 페이지 설정
# ==============================

PAGE_TITLE = "AI 금융 리스크 예측"

PAGE_ICON = "🏦"

LAYOUT = "wide"
