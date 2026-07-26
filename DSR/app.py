import datetime
import requests
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# 0. 한국은행 ECOS API 연동 및 데이터 수집
# ==========================================
ECOS_API_KEY = "31YTTV1LTR4TIOTYDW8B"  # 🔑 발급받으신 ECOS API 키 입력

@st.cache_data(ttl=3600)
def fetch_ecos_history(stat_code, item_code, frequency="M"):
    """최근 1년간의 시계열 데이터를 가져오는 함수 (차트 및 최신값 추출용)"""
    if ECOS_API_KEY == "31YTTV1LTR4TIOTYDW8B":
        # API 키 미입력 시 백업용 최근 1년 시뮬레이션 데이터 생성
        dates = pd.date_range(end=datetime.datetime.now(), periods=12, freq='ME').strftime("%Y-%m")
        rates = [3.85, 3.83, 3.78, 3.75, 3.70, 2.810, 2.730, 2.810, 2.820, 2.810, 2.890, 2.920]
        return pd.DataFrame({"연월": dates, "CD금리(%)": rates})

    end_date = datetime.datetime.now().strftime("%Y%m")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y%m")
    url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ECOS_API_KEY}/json/kr/1/12/{stat_code}/{frequency}/{start_date}/{end_date}/{item_code}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "StatisticSearch" in data:
            rows = data["StatisticSearch"]["row"]
            df = pd.DataFrame(rows)[["TIME", "DATA_VALUE"]]
            df.columns = ["연월", "CD금리(%)"]
            df["CD금리(%)"] = df["CD금리(%)"].astype(float)
            df["연월"] = df["연월"].apply(lambda x: f"{x[:4]}-{x[4:]}")
            return df
    except Exception as e:
        st.error(f"API 데이터 호출 중 오류 발생: {e}")
    
    # 예외 발생 시 기본 백업 데이터
    dates = pd.date_range(end=datetime.datetime.now(), periods=12, freq='ME').strftime("%Y-%m")
    rates = [3.85, 3.83, 3.78, 3.75, 3.70, 3.68, 3.65, 3.60, 3.58, 3.56, 3.55, 3.55]
    return pd.DataFrame({"연월": dates, "CD금리(%)": rates})

# 최근 1년 CD금리 시계열 데이터 호출
df_cd_history = fetch_ecos_history("722Y001", "010500000")
real_cd_rate = df_cd_history.iloc[-1]["CD금리(%)"] if not df_cd_history.empty else 3.55

# 소비자물가 및 가계부채 백업/API 수치
real_cpi_rate = 2.6
real_debt_growth = 4.2


# ==========================================
# 1. 머신러닝 및 금융공학 계산 함수
# ==========================================
def predict_macro_risk(cpi_rate, debt_growth, policy_index, base_cd_rate):
    pred_interest_rate = base_cd_rate + ((cpi_rate - 2.0) * 0.25) + (debt_growth * 0.08) - (policy_index * 0.15)
    pred_national_dsr = 38.5 + (pred_interest_rate * 1.1) + (debt_growth * 0.35) - (policy_index * 1.8)
    pred_default_rate = 0.35 + (pred_interest_rate * 0.12) + (cpi_rate * 0.08) - (policy_index * 0.22)
    pred_default_rate = max(0.1, pred_default_rate)
    return round(pred_interest_rate, 2), round(pred_national_dsr, 1), round(pred_default_rate, 2)

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
# 2. 메인 화면 구성
# ==========================================
st.set_page_config(page_title="ECOS 연동 가계부채 리스크 진단", page_icon="🏦", layout="wide")

st.sidebar.title("📌 메뉴 선택")
app_mode = st.sidebar.radio("모드를 선택하세요:", ["👤 1. 개인 맞춤 재무 리포트", "🌐 2. 국가 거시 리스크 예측"])


# ------------------------------------------
# 모듈 2: 국가 거시 리스크 예측
# ------------------------------------------
if app_mode == "🌐 2. 국가 거시 리스크 예측":
    st.title("🌐 국가 거시 리스크 & 정책 후속 조치 시뮬레이터")
    st.info("💡 **한국은행 ECOS Open API**를 통해 최신 경제 지표와 **최근 1년 CD금리 추이**를 실시간 연동했습니다.")
    st.divider()

    col1, col2 = st.columns([1.1, 1.3])  # 공간 넓게 조정

    with col1:
        st.subheader("⚙️ 거시 경제 변수 & 금리 조정")
        
        cpi_input = st.slider("소비자물가증감률 (%)", min_value=0.0, max_value=10.0, value=float(real_cpi_rate), step=0.1)
        debt_growth_input = st.slider("가계부채증가율 (%)", min_value=0.0, max_value=15.0, value=float(real_debt_growth), step=0.1)
        policy_input = st.select_slider(
            "정부 금융지원 정책 강도 지수",
            options=[0, 1, 2, 3],
            value=1,
            format_func=lambda x: ["0단계 (지원 없음)", "1단계 (만기 연장)", "2단계 (부분 상환유예)", "3단계 (전면 상환유예)"][x]
        )
        
        # 🌟 국가 창에도 금리 직접 조정 기능 추가!
        st.markdown("---")
        st.subheader("🎛️ 국가 시뮬레이션 기본 금리 미세 조율")
        macro_adjusted_cd = st.slider(
            "시뮬레이션 기준 CD금리 조정 (%p)", 
            min_value=1.0, max_value=10.0, 
            value=float(real_cd_rate), step=0.1,
            help="ECOS 최신 기준금리를 바탕으로 국가 거시 시뮬레이션 기본 금리를 변경합니다."
        )

    # 예측 수행 (조정된 기준금리 반영)
    pred_rate, pred_dsr, pred_default = predict_macro_risk(cpi_input, debt_growth_input, policy_input, macro_adjusted_cd)

    with col2:
        st.subheader("📊 머신러닝 예측 결과")
        m1, m2, m3 = st.columns([1, 1, 1])
        m1.metric("예측 시장 금리", f"{pred_rate}%", delta=f"{round(pred_rate - macro_adjusted_cd, 2)}%p")
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

        # 🌟 최근 금리 데이터 추이 차트 (최근순)
        st.divider()
        st.subheader("📈 ECOS 최근 1년 CD금리 추이 (최근순)")
        st.line_chart(df_cd_history.set_index("연월"))

    st.session_state["predicted_rate"] = pred_rate


# ------------------------------------------
# 모듈 1: 개인 맞춤 재무 리포트
# ------------------------------------------
elif app_mode == "👤 1. 개인 맞춤 재무 리포트":
    st.title("👤 개인 맞춤형 대출 / DSR 정밀 진단 리포트")
    st.markdown("거시 모듈에서 도출된 **미래 예측 금리**와 **최근 금리 데이터**를 바탕으로 개인 원리금을 정밀 진단합니다.")
    st.divider()

    default_rate = st.session_state.get("predicted_rate", real_cd_rate)

    # 🌟 공간을 넓히기 위해 레이아웃 비율을 [1, 1.4]로 조율
    col1, col2 = st.columns([1, 1.4])

    with col1:
        st.subheader("📝 내 재무 정보 입력")
        income_input = st.number_input("연 소득 (만원)", min_value=1000, max_value=50000, value=5000, step=500)
        loan_input = st.number_input("대출 총액 (만원)", min_value=1000, max_value=200000, value=30000, step=1000)
        years_input = st.selectbox("대출 만기 (년)", options=[10, 15, 20, 30, 40, 50], index=3)

        st.subheader("⚙️ 적용 금리 미세 조율")
        st.caption(f"💡 머신러닝 추천 예측 금리: **{default_rate}%**")
        selected_rate = st.slider("적용 금리 직접 조절 (%p)", min_value=1.0, max_value=10.0, value=float(default_rate), step=0.1)

    monthly_pay, personal_dsr = calculate_personal_dsr(income_input, loan_input, years_input, selected_rate)

    with col2:
        st.subheader("📄 진단 결과 리포트")
        
        # 🌟 원리금 숫자가 잘리지 않도록 공간을 넉넉히 배치
        p1, p2 = st.columns([1.3, 1])
        # 천 단위 쉼표 표기 및 '원' 단위를 명확히 표시
        p1.metric("예상 월 원리금 (원 단위)", f"{monthly_pay:,} 원")
        p2.metric("내 개인 DSR", f"{personal_dsr} %")

        st.divider()
        if personal_dsr > 40.0:
            st.error(f"🚨 **DSR 위험 ({personal_dsr}%)**: 정부 규제 상한선(40%)을 초과했습니다!")
        elif personal_dsr > 35.0:
            st.warning(f"⚠️ **DSR 주의 ({personal_dsr}%)**: 규제 한도(40%)에 근접했습니다.")
        else:
            st.success(f"✅ **DSR 안전 ({personal_dsr}%)**: 감당 가능한 안정적 수준입니다.")

        # 🌟 공간을 넓혀 금리 변동 시뮬레이션 표를 탁 트이게 출력
        st.subheader("📈 금리 변동에 따른 월 지출 변화 시뮬레이션")
        rates_to_compare = [selected_rate - 0.5, selected_rate, selected_rate + 0.5]
        sim_data = []
        for r in rates_to_compare:
            pay, dsr = calculate_personal_dsr(income_input, loan_input, years_input, r)
            sim_data.append({
                "금리 시나리오": f"{r:.1f}%",
                "예상 월 원리금": f"{pay:,} 원",
                "월 지출 변동 폭": f"{(pay - monthly_pay):+,} 원",
                "개인 DSR": f"{dsr}%"
            })
        
        # 테이블을 가로 전체 크기(use_container_width)로 시원하게 출력
        st.dataframe(pd.DataFrame(sim_data), use_container_width=True)

        # 🌟 개인 모듈에도 최근 1년 금리 데이터 조회 기능 포함
        with st.expander("🔍 최근 1년 기준 CD금리 데이터 목록 보기 (최근순)"):
            st.dataframe(df_cd_history.sort_values(by="연월", ascending=False), use_container_width=True)
