import datetime
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 0. 한국은행 ECOS API 연동 및 데이터 수집
# ==========================================
# 🔑 요청하신 ECOS API 키가 설정되었습니다.
ECOS_API_KEY = "31YTTV1LTRTIOTYDW8B"


@st.cache_data(ttl=3600)
def fetch_ecos_history(stat_code, item_code, frequency="M"):
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

    # 예외 발생 시 백업용 시뮬레이션 데이터 (Pandas 최신 버전 호환 freq='ME')
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
# 1. 단기(1개월) ~ 중기(6개월) 구간별 예측 함수
# ==========================================
def predict_macro_timeline(cpi_rate, debt_growth, policy_index, base_cd):
    """당장 다음 달(1개월), 3개월, 6개월 후까지의 단계별 금리/DSR/연체율을 추정하는 함수"""
    timeline_data = []

    # 월별 추세 압력 계수 산출
    monthly_trend = ((cpi_rate - 2.0) * 0.05) + (debt_growth * 0.02)
    months_list = [0, 1, 3, 6]

    for m in months_list:
        if m == 0:
            rate = base_cd
            dsr = 38.5 + (rate * 1.0) - (policy_index * 1.5)
            default_rate = 0.35 + (rate * 0.1) - (policy_index * 0.2)
        else:
            rate = max(
                1.0, base_cd + (monthly_trend * m) - (policy_index * 0.02 * m)
            )
            dsr = (
                38.5
                + (rate * (1.0 + 0.04 * m))
                + (debt_growth * 0.06 * m)
                - (policy_index * (1.5 + 0.05 * m))
            )
            default_rate = (
                0.35
                + (rate * (0.1 + 0.01 * m))
                + (cpi_rate * 0.02 * m)
                - (policy_index * (0.2 + 0.01 * m))
            )

        default_rate = max(0.1, default_rate)

        timeline_data.append(
            {
                "시점": "현재" if m == 0 else f"{m}개월 후",
                "경과월": m,
                "예측금리": round(rate, 2),
                "국가DSR": round(dsr, 1),
                "연체율": round(default_rate, 2),
            }
        )

    return pd.DataFrame(timeline_data)


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
# 2. 메인 화면 구성 (1번/2번 모듈 순서 변경)
# ==========================================
st.set_page_config(
    page_title="ECOS 연동 가계부채 단기~중기 예측 진단", page_icon="🏦", layout="wide"
)

st.sidebar.title("📌 메뉴 선택")
app_mode = st.sidebar.radio(
    "모드를 선택하세요:",
    ["👤 1. 개인 맞춤 재무 리포트", "🌐 2. 국가 거시 리스크 예측"],
)

# 기본 거시 타임라인 예측 수행
df_t = predict_macro_timeline(real_cpi_rate, real_debt_growth, 1, real_cd_rate)

# ------------------------------------------
# 모듈 1: 개인 맞춤 재무 리포트 (순서 1번으로 변경)
# ------------------------------------------
if app_mode == "👤 1. 개인 맞춤 재무 리포트":
    st.title("👤 개인 맞춤형 대출 / 단계별(다음 달~6개월 후) 상환 스케줄")
    st.markdown(
        "거시 데이터 예측을 바탕으로 **당장 다음 달부터 6개월 후까지 내 통장에서 나갈 월 상환액 변화**를 타임라인으로 정밀 계산합니다."
    )
    st.divider()

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

        st.markdown("---")
        st.caption(f"💡 현재 ECOS 연동 CD(91일) 기준 금리: **{real_cd_rate}%**")

    with col2:
        st.subheader("📄 내 단계별(다음 달 ~ 6개월 후) 예상 상환 스케줄")

        # 시점별 개인 원리금 및 DSR 계산
        personal_schedule = []
        curr_p = 0

        for idx, row in df_t.iterrows():
            m_label = row["시점"]
            r = row["예측금리"]
            pay, dsr = calculate_personal_dsr(
                income_input, loan_input, years_input, r
            )

            if idx == 0:
                curr_p = pay
                diff_str = "-"
            else:
                diff = pay - curr_p
                diff_str = f"{diff:+,} 원"

            personal_schedule.append(
                {
                    "시점": m_label,
                    "예측 적용 금리": f"{r}%",
                    "예상 월 원리금": f"{pay:,} 원",
                    "현재 대비 월 지출 증가액": diff_str,
                    "내 개인 DSR": f"{dsr}%",
                }
            )

        df_pers_sched = pd.DataFrame(personal_schedule)

        # 다음 달 수치 강조
        m1_pay_info = personal_schedule[1]
        p1, p2 = st.columns([1.3, 1])
        p1.metric(
            "당장 다음 달 예상 원리금",
            m1_pay_info["예상 월 원리금"],
            delta=m1_pay_info["현재 대비 월 지출 증가액"],
        )
        p2.metric("다음 달 내 DSR", m1_pay_info["내 개인 DSR"])

        st.markdown("##### 🗓️ 단계별 월 상환액 변화 스케줄")
        st.dataframe(df_pers_sched, use_container_width=True)

        st.divider()
        m6_dsr_val = float(personal_schedule[-1]["내 개인 DSR"].replace("%", ""))
        if m6_dsr_val > 40.0:
            st.error(
                f"🚨 **[경고] 6개월 내 DSR({m6_dsr_val}%) 규제 상한 초과 예상!**\n\n"
                "👉 당장 다음 달부터 월 지출이 늘어나므로, **지금 즉시 고정금리 대환대출 신청이나 지출 축소 계획**을 세우셔야 합니다."
            )
        else:
            st.success("✅ **[안정] 6개월 내 DSR이 40% 이하로 안전하게 유지됩니다.**")

# ------------------------------------------
# 모듈 2: 국가 거시 리스크 예측 (순서 2번으로 변경)
# ------------------------------------------
elif app_mode == "🌐 2. 국가 거시 리스크 예측":
    st.title("🌐 국가 거시 리스크 단계별 예측 시뮬레이터")
    st.info(
        "💡 **당장 다음 달(1개월 후)**부터 **3개월 후, 6개월 후**까지 단계별 국가 거시 지표 변화 흐름을 시뮬레이션합니다."
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

    # 거시 시뮬레이션 데이터프레임 생성
    df_timeline = predict_macro_timeline(
        cpi_input, debt_growth_input, policy_input, base_cd_input
    )

    with col2:
        st.subheader("📊 시점별(다음 달 ~ 6개월 후) 국가 거시 지표 예측")

        m1_data = df_timeline[df_timeline["시점"] == "1개월 후"].iloc[0]
        m6_data = df_timeline[df_timeline["시점"] == "6개월 후"].iloc[0]

        m1, m2, m3 = st.columns(3)
        m1.metric(
            "다음 달(1M) 예상 금리",
            f"{m1_data['예측금리']}%",
            delta=f"{round(m1_data['예측금리'] - base_cd_input, 2)}%p",
        )
        m2.metric(
            "6개월 후(6M) 예상 금리",
            f"{m6_data['예측금리']}%",
            delta=f"{round(m6_data['예측금리'] - base_cd_input, 2)}%p",
        )
        m3.metric(
            "6개월 후 가계 연체율",
            f"{m6_data['연체율']}%",
            delta=f"{round(m6_data['연체율'] - df_timeline.iloc[0]['연체율'], 2)}%p",
        )

        st.markdown("##### 🗓️ 시점별 리스크 변화 종합 표")
        st.dataframe(df_timeline, use_container_width=True)

        st.divider()
        st.subheader("🚨 단계별 정부 후속 조치 예견")

        if m6_data["연체율"] >= 1.5:
            st.error(
                f"**[경고: 심각]** 6개월 내 연체율({m6_data['연체율']}%)이 위험 수준 도달 예견.\n\n"
                "👉 **다음 달~3개월 내**: 금융 당국의 **만기 연장 긴급 지침** 배포 예상\n"
                "👉 **6개월 내**: **전면 상환유예** 및 **안심전환대출** 시행 가능성 높음"
            )
        else:
            st.success(
                f"**[안정]** 6개월 내 연체율({m6_data['연체율']}%)이 관리 가능한 범주입니다."
            )

        st.divider()
        st.subheader("📈 최근 1년 CD금리 추이")
        st.line_chart(df_cd_history.set_index("연월"))
