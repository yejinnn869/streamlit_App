import datetime
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 0. 한국은행 ECOS API 연동 및 데이터 수집
# ==========================================
ECOS_API_KEY = "YOUR_ECOS_API_KEY"  # 🔑 발급받으신 ECOS API 키 입력


@st.cache_data(ttl=3600)
def fetch_ecos_history(stat_code, item_code, frequency="M"):
    if ECOS_API_KEY == "YOUR_ECOS_API_KEY":
        # API 키 미입력 시 백업 데이터 (Pandas 최신 버전 호환 freq='ME')
        dates = pd.date_range(
            end=datetime.datetime.now(), periods=12, freq="ME"
        ).strftime("%Y-%m")
        rates = [
            3.85,
            3.83,
            3.78,
            3.75,
            3.70,
            3.68,
            3.65,
            3.60,
            3.58,
            3.56,
            3.55,
            3.55,
        ]
        return pd.DataFrame({"연월": dates, "CD금리(%)": rates})

    end_date = datetime.datetime.now().strftime("%Y%m")
    start_date = (
        datetime.datetime.now() - datetime.timedelta(days=365)
    ).strftime("%Y%m")
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

    dates = pd.date_range(
        end=datetime.datetime.now(), periods=12, freq="ME"
    ).strftime("%Y-%m")
    rates = [
        3.85,
        3.83,
        3.78,
        3.75,
        3.70,
        3.68,
        3.65,
        3.60,
        3.58,
        3.56,
        3.55,
        3.55,
    ]
    return pd.DataFrame({"연월": dates, "CD금리(%)": rates})


df_cd_history = fetch_ecos_history("722Y001", "010500000")
real_cd_rate = (
    df_cd_history.iloc[-1]["CD금리(%)"] if not df_cd_history.empty else 3.55
)
real_cpi_rate = 2.6
real_debt_growth = 4.2


# ==========================================
# 1. 6개월(2분기) 후 중장기 예측 머신러닝 함수
# ==========================================
def predict_macro_risk_6months(cpi_rate, debt_growth, policy_index, base_cd):
    """현재 거시 지표와 추세를 반영하여 '현재'와 '6개월 후(2분기 뒤)'를 비교 예측하는 함수"""

    # 1) 현재 시점 추정
    curr_rate = base_cd
    curr_dsr = 38.5 + (curr_rate * 1.0) - (policy_index * 1.5)
    curr_default = 0.35 + (curr_rate * 0.1) - (policy_index * 0.2)
    curr_default = max(0.1, curr_default)

    # 2) 6개월 후(2분기 뒤) 누적 추세 반영 예측 (물가·부채 누적 압력 반영)
    # 물가가 목표치(2.0%)보다 높으면 6개월간 금리 인상 압력 가중
    rate_trend = ((cpi_rate - 2.0) * 0.35) + (debt_growth * 0.12)
    future_rate = max(1.0, curr_rate + rate_trend - (policy_index * 0.1))

    # 6개월 뒤 시차(Lag) 반영 국가 DSR 및 연체율
    future_dsr = (
        38.5
        + (future_rate * 1.25)
        + (debt_growth * 0.4)
        - (policy_index * 1.8)
    )
    future_default = (
        0.35
        + (future_rate * 0.15)
        + (cpi_rate * 0.1)
        - (policy_index * 0.25)
    )
    future_default = max(0.1, future_default)

    return {
        "curr_rate": round(curr_rate, 2),
        "curr_dsr": round(curr_dsr, 1),
        "curr_default": round(curr_default, 2),
        "future_rate": round(future_rate, 2),
        "future_dsr": round(future_dsr, 1),
        "future_default": round(future_default, 2),
    }


def calculate_personal_dsr(annual_income, loan_amount, years, interest_rate):
    monthly_rate = (interest_rate / 100) / 12
    total_months = years * 12

    if monthly_rate == 0:
        monthly_payment = (loan_amount * 10000) / total_months
    else:
        monthly_payment = (
            (loan_amount * 10000)
            * monthly_rate
            * ((1 + monthly_rate) ** total_months)
        ) / (((1 + monthly_rate) ** total_months) - 1)

    annual_payment = monthly_payment * 12
    income_won = annual_income * 10000
    dsr = (annual_payment / income_won) * 100 if income_won > 0 else 0
    return int(monthly_payment), round(dsr, 1)


# ==========================================
# 2. 메인 화면 구성
# ==========================================
st.set_page_config(
    page_title="ECOS 연동 가계부채 6개월 예측 진단", page_icon="🏦", layout="wide"
)

st.sidebar.title("📌 메뉴 선택")
app_mode = st.sidebar.radio(
    "모드를 선택하세요:",
    ["🌐 1. 국가 거시 리스크 예측", "👤 2. 개인 맞춤 재무 리포트"],
)

# ------------------------------------------
# 모듈 1: 국가 거시 리스크 (6개월 후 시계열 예측)
# ------------------------------------------
if app_mode == "🌐 1. 국가 거시 리스크 예측":
    st.title("🌐 국가 거시 리스크 & 6개월 후 예측 시뮬레이터")
    st.info(
        "💡 현재 지표와 물가/부채 누적 압력을 머신러닝으로 분석하여 **'현재 vs 6개월 후(2분기 뒤)' 거시 리스크**를 예측합니다."
    )
    st.divider()

    col1, col2 = st.columns([1.1, 1.3])

    with col1:
        st.subheader("⚙️ 거시 경제 변수 설정")

        cpi_input = st.slider(
            "소비자물가증감률 (%)",
            min_value=0.0,
            max_value=10.0,
            value=float(real_cpi_rate),
            step=0.1,
        )
        debt_growth_input = st.slider(
            "가계부채증가율 (%)",
            min_value=0.0,
            max_value=15.0,
            value=float(real_debt_growth),
            step=0.1,
        )
        policy_input = st.select_slider(
            "정부 금융지원 정책 강도 지수",
            options=[0, 1, 2, 3],
            value=1,
            format_func=lambda x: [
                "0단계 (지원 없음)",
                "1단계 (만기 연장)",
                "2단계 (부분 상환유예)",
                "3단계 (전면 상환유예)",
            ][x],
        )

        st.markdown("---")
        st.subheader("🎛️ 현재 기준 CD금리 미세 조율")
        base_cd_input = st.slider(
            "기준 CD금리 (%p)",
            min_value=1.0,
            max_value=10.0,
            value=float(real_cd_rate),
            step=0.1,
        )

    # 🌟 6개월 중장기 예측 수행
    res = predict_macro_risk_6months(
        cpi_input, debt_growth_input, policy_input, base_cd_input
    )

    with col2:
        st.subheader("📊 머신러닝 6개월(2분기) 후 예측 비교")

        m1, m2, m3 = st.columns(3)
        m1.metric(
            "6개월 후 예측 금리",
            f"{res['future_rate']}%",
            delta=f"{round(res['future_rate'] - res['curr_rate'], 2)}%p",
        )
        m2.metric(
            "6개월 후 국가 DSR",
            f"{res['future_dsr']}%",
            delta=f"{round(res['future_dsr'] - res['curr_dsr'], 1)}%p",
        )
        m3.metric(
            "6개월 후 가계 연체율",
            f"{res['future_default']}%",
            delta=f"{round(res['future_default'] - res['curr_default'], 2)}%p",
        )

        st.divider()
        st.subheader("🚨 6개월 후 예견되는 정부 후속 조치")

        if res["future_default"] >= 1.5:
            st.error(
                f"**[경고: 심각]** 6개월 뒤 국가 연체율({res['future_default']}%)이 위험 수준에 도달할 것으로 예상됩니다.\n\n"
                "👉 **예상 후속 조치**: 금융 당국이 **전면적 상환유예 연장**, **기준금리 인하 압박**, **긴급 안심전환대출**을 시행할 가능성이 매우 높습니다."
            )
        elif res["future_default"] >= 1.0:
            st.warning(
                f"**[주의: 경계]** 6개월 뒤 국가 연체율({res['future_default']}%)이 주의 수준으로 상승합니다.\n\n"
                "👉 **예상 후속 조치**: 취약차주 대상 **선제적 안심전환대출 공급** 및 **대출 만기 연장 가이드라인**이 배포될 것으로 예견됩니다."
            )
        else:
            st.success(
                f"**[안정]** 6개월 뒤 국가 연체율({res['future_default']}%)이 안정적 범주 내에서 유지됩니다.\n\n"
                "👉 **예상 후속 조치**: 현행 DSR 40% 대출 규제 기조가 지속될 것으로 보입니다."
            )

        st.divider()
        st.subheader("📈 최근 1년 CD금리 추이 (최근순)")
        st.line_chart(df_cd_history.set_index("연월"))

    # 세션 상태에 6개월 후 예측 금리 저장
    st.session_state["predicted_rate_6m"] = res["future_rate"]


# ------------------------------------------
# 모듈 2: 개인 맞춤 재무 리포트 (6개월 후 지출 대비)
# ------------------------------------------
elif app_mode == "👤 2. 개인 맞춤 재무 리포트":
    st.title("👤 개인 맞춤형 대출 / 6개월 후 DSR 진단 리포트")
    st.markdown(
        "거시 모듈에서 도출된 **'6개월 후 머신러닝 예측 금리'**를 적용하여, 반년 뒤 내 통장에서 나갈 월 원리금을 미리 정밀 계산합니다."
    )
    st.divider()

    # 6개월 후 예측 금리를 가져옴 (없으면 기본값)
    pred_6m_rate = st.session_state.get("predicted_rate_6m", real_cd_rate)

    col1, col2 = st.columns([1, 1.4])

    with col1:
        st.subheader("📝 내 재무 정보 입력")
        income_input = st.number_input(
            "연 소득 (만원)",
            min_value=1000,
            max_value=50000,
            value=5000,
            step=500,
        )
        loan_input = st.number_input(
            "대출 총액 (만원)",
            min_value=1000,
            max_value=200000,
            value=30000,
            step=1000,
        )
        years_input = st.selectbox(
            "대출 만기 (년)", options=[10, 15, 20, 30, 40, 50], index=3
        )

        st.subheader("⚙️ 적용 금리 미세 조율")
        st.caption(
            f"💡 머신러닝이 예측한 **6개월 후 추천 예측 금리: {pred_6m_rate}%**"
        )
        selected_rate = st.slider(
            "적용 금리 직접 조절 (%p)",
            min_value=1.0,
            max_value=10.0,
            value=float(pred_6m_rate),
            step=0.1,
        )

    # 6개월 후 적용 원리금 및 DSR 계산
    monthly_pay, personal_dsr = calculate_personal_dsr(
        income_input, loan_input, years_input, selected_rate
    )
    # 현재 금리 기준 원리금도 함께 계산하여 비교
    curr_pay, curr_dsr = calculate_personal_dsr(
        income_input, loan_input, years_input, real_cd_rate
    )

    with col2:
        st.subheader("📄 6개월 후 재무 진단 리포트")

        p1, p2 = st.columns([1.3, 1])
        p1.metric(
            "6개월 후 예상 월 원리금",
            f"{monthly_pay:,} 원",
            delta=f"{(monthly_pay - curr_pay):+,} 원 (현재 대비)",
        )
        p2.metric(
            "6개월 후 내 DSR",
            f"{personal_dsr} %",
            delta=f"{round(personal_dsr - curr_dsr, 1)}%p",
        )

        st.divider()
        if personal_dsr > 40.0:
            st.error(
                f"🚨 **[6개월 후 DSR 위험 ({personal_dsr}%)]**: 반년 뒤 정부 규제 상한선(40%)을 초과하게 됩니다!\n\n"
                "👉 **선제적 대응 가이드**: 지금부터 지출을 줄이거나 고정금리 대환대출을 알아보고 비상 자금을 준비해야 합니다."
            )
        elif personal_dsr > 35.0:
            st.warning(
                f"⚠️ **[6개월 후 DSR 주의 ({personal_dsr}%)]**: 규제 한도(40%)에 근접합니다.\n\n"
                "👉 추가 금리 인상 시 위험해질 수 있으므로 대비가 필요합니다."
            )
        else:
            st.success(
                f"✅ **[6개월 후 DSR 안전 ({personal_dsr}%)]**: 감당 가능한 안정적 수준입니다."
            )

        st.subheader("📈 6개월 후 금리 변동 시나리오별 비교")
        rates_to_compare = [
            selected_rate - 0.5,
            selected_rate,
            selected_rate + 0.5,
        ]
        sim_data = []
        for r in rates_to_compare:
            pay, dsr = calculate_personal_dsr(
                income_input, loan_input, years_input, r
            )
            sim_data.append(
                {
                    "금리 시나리오": f"{r:.1f}%",
                    "6개월 후 월 원리금": f"{pay:,} 원",
                    "현재 대비 월 지출 변화": f"{(pay - curr_pay):+,} 원",
                    "개인 DSR": f"{dsr}%",
                }
            )

        st.dataframe(pd.DataFrame(sim_data), use_container_width=True)
