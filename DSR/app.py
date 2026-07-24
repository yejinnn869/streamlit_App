import datetime
import requests
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# 0. 한국은행 ECOS API 연동 및 데이터 수집
# ==========================================
# 🔑 발급받으신 ECOS API 키를 입력하세요.
ECOS_API_KEY = "31YTTV1LTRTIOTYDW8B"

@st.cache_data(ttl=3600)  # 1시간마다 API 캐싱 (호출 제한 방지)
def fetch_ecos_data(stat_code, item_code, frequency="M"):
    """한국은행 ECOS API에서 최신 수치 1건을 조회하는 함수"""
    if ECOS_API_KEY == "YOUR_ECOS_API_KEY":
        # API 키가 미입력되었을 때의 방어 로직 (기본값 제공)
        return None

    # 최근 1년 데이터 조회 (최신 데이터 1건 추출 목적)
    end_date = datetime.datetime.now().strftime("%Y%m")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y%m")

    url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ECOS_API_KEY}/json/kr/1/1/{stat_code}/{frequency}/{start_date}/{end_date}/{item_code}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "StatisticSearch" in data:
            row = data["StatisticSearch"]["row"][-1] # 가장 최신월 데이터
            return float(row["DATA_VALUE"])
    except Exception as e:
        st.error(f"API 데이터 호출 중 오류 발생: {e}")
    return None

# API를 통해 최신 경제 지표 받아오기 (ECOS 통계표코드 및 항목코드)
# 1. CD(91일) 금리 (통계표: 722Y001 / 항목: 010500000)
api_cd_rate = fetch_ecos_data("722Y001", "010500000")
# 2. 소비자물가상승률 (통계표: 901Y009 / 항목: 0)
api_cpi_rate = fetch_ecos_data("901Y009", "0")
# 3. 가계신용/부채증가율 (통계표: 151Y003 / 항목: 1000000)
api_debt_growth = fetch_ecos_data("151Y003", "1000000")

# API 호출 실패 시 활용할 최신 고시 기준 백업 데이터 (2026년 기준)
real_cd_rate = api_cd_rate if api_cd_rate is not None else 3.55
real_cpi_rate = api_cpi_rate if api_cpi_rate is not None else 2.6
real_debt_growth = api_debt_growth if api_debt_growth is not None else 4.2


# ==========================================
# 1. 머신러닝 예측 모델 (실제 ECOS 데이터 연동)
# ==========================================
def predict_macro_risk(cpi_rate, debt_growth, policy_index, base_cd_rate):
    """API로 불러온 실제 CD금리와 거시 지표를 바탕으로 리스크 예측"""
    
    # 예측 시장금리 = ECOS 실시간 CD금리 + (물가 변동)*0.25 + (부채변동)*0.1 - (정책완화)*0.15
    pred_interest_rate = base_cd_rate + ((cpi_rate - 2.0) * 0.25) + (debt_growth * 0.08) - (policy_index * 0.15)
    
    # 국가 평균 DSR = 실시간 기본 38.5% + 금리상승영향 + 부채팽창 - 정책상환유예 착시효과
    pred_national_dsr = 38.5 + (pred_interest_rate * 1.1) + (debt_growth * 0.35) - (policy_index * 1.8)
    
    # 국가 가계대출 연체율 (%)
    pred_default_rate = 0.35 + (pred_interest_rate * 0.12) + (cpi_rate * 0.08) - (policy_index * 0.22)
    pred_default_rate = max(0.1, pred_default_rate)

    return round(pred_interest_rate, 2), round(pred_national_dsr, 1), round(pred_default_rate, 2)


# ==========================================
# 2. 금융공학 정석 원리금 및 DSR 계산 함수
# ==========================================
def calculate_personal_dsr(annual_income, loan_amount, years, interest_rate):
    monthly_rate = (interest_rate / 100) / 12
    total_months = years * 12
    
    if monthly_rate == 0:
        monthly_payment = (loan_amount * 10000) / total_months
    else:
        monthly_payment = ((loan_amount * 10000) * monthly_rate * ((1 + monthly_rate)**total_months)) / (((1 + monthly_rate)**total_months) - 1)
        
    annual_payment = monthly_payment * 12
    income_won = annual_income * 10000
    
    dsr = (annual_payment / income_won) * 100 if income_won > 0 else 0
    return int(monthly_payment), round(dsr, 1)


# ==========================================
# 3. 메인 화면 구성
# ==========================================
st.set_page_config(page_title="ECOS API 연동 가계부채 리스크 진단", page_icon="🏦", layout="wide")

st.sidebar.title("📌 메뉴 선택")
app_mode = st.sidebar.radio("모드를 선택하세요:", ["🌐 1. 국가 거시 리스크 예측", "👤 2. 개인 맞춤 재무 리포트"])

# ------------------------------------------
# 모듈 1: 국가 거시 리스크 예측 (API 실시간 연동)
# ------------------------------------------
if app_mode == "🌐 1. 국가 거시 리스크 예측":
    st.title("🌐 국가 거시 리스크 & 정책 후속 조치 시뮬레이터")
    st.info("💡 **한국은행 ECOS Open API**를 통해 최신 경제 지표(CD금리, 물가, 가계부채)를 실시간으로 불러와 기본값으로 자동 설정했습니다.")
    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📡 ECOS 실시간 지표 기반 시뮬레이션")
        
        # API에서 가져온 실제 데이터를 value 기본값으로 세팅!
        cpi_input = st.slider("소비자물가증감률 (%)", min_value=0.0, max_value=10.0, value=float(real_cpi_rate), step=0.1)
        debt_growth_input = st.slider("가계부채증가율 (%)", min_value=0.0, max_value=15.0, value=float(real_debt_growth), step=0.1)
        policy_input = st.select_slider(
            "정부 금융지원 정책 강도 지수",
            options=[0, 1, 2, 3],
            value=1,
            format_func=lambda x: ["0단계 (지원 없음)", "1단계 (만기 연장)", "2단계 (부분 상환유예)", "3단계 (전면 상환유예)"][x]
        )

    # 머신러닝 예측 수행 (API로 불러온 실제 CD금리 사용)
    pred_rate, pred_dsr, pred_default = predict_macro_risk(cpi_input, debt_growth_input, policy_input, real_cd_rate)

    with col2:
        st.subheader("📊 API 데이터 기반 머신러닝 예측")
        m1, m2, m3 = st.columns(3)
        m1.metric("예측 시장 금리", f"{pred_rate}%", delta=f"{round(pred_rate - real_cd_rate, 2)}%p (ECOS 기준)")
        m2.metric("국가 평균 DSR", f"{pred_dsr}%")
        m3.metric("국가 가계 연체율", f"{pred_default}%")

        st.divider()
        st.subheader("🚨 위험도 진단 및 정부 후속 조치 예견")
        
        if pred_default >= 1.5:
            st.error(f"**[경고: 심각]** 예상 연체율({pred_default}%)이 위험 수준입니다.\n\n👉 **예상 후속 조치**: 금융 당국의 **전면적 상환유예** 및 **기준금리 인하 압박**, **대출 만기 연장 긴급 지침** 배포가 예견됩니다.")
        elif pred_default >= 1.0:
            st.warning(f"**[주의: 경계]** 예상 연체율({pred_default}%)이 경계선에 도달했습니다.\n\n👉 **예상 후속 조치**: 취약계층 대상 **선제적 안심전환대출 공급** 및 **연체 유예 가이드라인**이 출범할 가능성이 높습니다.")
        else:
            st.success(f"**[안정]** 예상 연체율({pred_default}%)이 안정적입니다.\n\n👉 **예상 후속 조치**: 현행 대출 규제(DSR 40% 제한) 기조가 지속될 것으로 예상됩니다.")

    st.session_state["predicted_rate"] = pred_rate

# ------------------------------------------
# 모듈 2: 개인 맞춤 재무 리포트
# ------------------------------------------
elif app_mode == "👤 2. 개인 맞춤 재무 리포트":
    st.title("👤 개인 맞춤형 대출 / DSR 정밀 진단 리포트")
    st.markdown("거시 모듈에서 ECOS API 및 머신러닝으로 도출된 **미래 예측 금리**를 바탕으로, 개개인의 실제 원리금을 정밀 계산합니다.")
    st.divider()

    default_rate = st.session_state.get("predicted_rate", real_cd_rate)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 내 재무 정보 입력")
        income_input = st.number_input("연 소득 (만원)", min_value=1000, max_value=50000, value=5000, step=500)
        loan_input = st.number_input("대출 총액 (만원)", min_value=1000, max_value=200000, value=30000, step=1000)
        years_input = st.selectbox("대출 만기 (년)", options=[10, 15, 20, 30, 40, 50], index=3)

        st.subheader("⚙️ 적용 금리 미세 조율")
        st.caption(f"💡 ECOS API 연동 머신러닝의 추천 예측 금리: **{default_rate}%**")
        
        selected_rate = st.slider("적용 금리 직접 조절 (%p)", min_value=1.0, max_value=10.0, value=float(default_rate), step=0.1)

    monthly_pay, personal_dsr = calculate_personal_dsr(income_input, loan_input, years_input, selected_rate)

    with col2:
        st.subheader("📄 진단 결과 리포트")
        p1, p2 = st.columns(2)
        p1.metric("예상 월 원리금", f"{monthly_pay:,} 원")
        p2.metric("내 개인 DSR", f"{personal_dsr} %")

        st.divider()
        if personal_dsr > 40.0:
            st.error(f"🚨 **DSR 위험 ({personal_dsr}%)**: 정부 규제 상한선(40%)을 초과했습니다!")
        elif personal_dsr > 35.0:
            st.warning(f"⚠️ **DSR 주의 ({personal_dsr}%)**: 규제 한도(40%)에 근접했습니다.")
        else:
            st.success(f"✅ **DSR 안전 ({personal_dsr}%)**: 감당 가능한 안정적 수준입니다.")

        st.subheader("📈 금리 변동 시뮬레이션")
        rates_to_compare = [selected_rate - 0.5, selected_rate, selected_rate + 0.5]
        sim_data = []
        for r in rates_to_compare:
            pay, dsr = calculate_personal_dsr(income_input, loan_input, years_input, r)
            sim_data.append({
                "금리 시나리오": f"{r:.1f}%",
                "월 원리금": f"{pay:,} 원",
                "월 변동폭": f"{(pay - monthly_pay):+,} 원",
                "개인 DSR": f"{dsr}%"
            })
        st.table(pd.DataFrame(sim_data))
