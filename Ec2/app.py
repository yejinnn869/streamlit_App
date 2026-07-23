import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ==========================================
# 1. 페이지 기본 설정 및 헤더
# ==========================================
st.set_page_config(
    page_title="행동경제학 기반 환율-주가 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("📊 환율 변동과 기업 주가의 '합리적 무시' 실증 분석")
st.caption("야후 파이낸스(yfinance) 기반 거시경제-행동경제학 융합 탐구 대시보드")

# 이론적 배경 설명 상자
with st.expander("💡 행동경제학: '합리적 무시(Rational Inattention)' & '시차 효과'란?", expanded=True):
    st.write("""
    * **합리적 무시(Rational Inattention):** 인간은 정보 처리 비용 때문에 환율 변동이 자신만의 **임계값(Threshold)** 이하일 때는 변화를 감지하지 않거나 무시하며, 임계값을 초과할 때 비로소 민감하게 반응합니다.
    * **시차 효과(Time Lag):** 오늘 발생한 환율 변동이 시장 참가자들의 심리와 기업 실적 기대치에 반영되어 **실제 주가 움직임으로 나타나기까지 1~3일의 시차**가 존재할 수 있습니다.
    """)

# ==========================================
# 2. 사이드바 (사용자 조작 컨트롤 패널)
# ==========================================
st.sidebar.header("⚙️ 분석 설정 패널")

# 2-1. 분석 대상 기업 선택 (대표 기업 추가)
company_dict = {
    "삼성전자 (수출 중심 - 반도체/IT)": "005930.KS",
    "현대차 (수출 중심 - 자동차)": "005380.KS",
    "CJ제일제당 (내수/수입 - 식품/원재료)": "097950.KS",
    "농심 (내수/수입 - 식품/유통)": "004370.KS"
}
selected_company_name = st.sidebar.selectbox("1. 분석 기업 선택", list(company_dict.keys()))
selected_code = company_dict[selected_company_name]

# 2-2. 분석 기간 선택
today = datetime.date.today()
default_start = today - datetime.timedelta(days=365) # 기본값: 최근 1년
start_date = st.sidebar.date_input("2. 분석 시작일", default_start)
end_date = st.sidebar.date_input("3. 분석 종료일", today)

# 2-3. 행동경제학 변수 설정
st.sidebar.subheader("3. 행동경제학 변수 설정")

# [기능 1] 시차(Lag) 설정
lag_days = st.sidebar.selectbox(
    "⏱️ 환율 변동 시차(Lag) 설정",
    options=[0, 1, 2, 3],
    index=0,
    format_func=lambda x: f"당일 반응 (0일 시차)" if x == 0 else f"{x}일 후 주가 반응 ({x}일 시차)",
    help="오늘의 환율 변동이 N일 뒤 주가 변동에 미치는 영향을 분석합니다."
)

# 임계값 슬라이더
threshold = st.sidebar.slider(
    "💡 환율 인지 임계값 (%)",
    min_value=0.0,
    max_value=3.0,
    value=1.0,
    step=0.1,
    help="환율의 일간 변동률이 이 기준 이하이면 '무시 구간', 초과하면 '반응 구간'으로 분류합니다."
)

# ==========================================
# 3. 데이터 수집 및 전처리 (yfinance 사용)
# ==========================================
@st.cache_data(ttl=3600)
def load_data(stock_code, start, end):
    try:
        # 환율 데이터 (USD/KRW)
        fx = yf.Ticker("KRW=X")
        df_fx = fx.history(start=start, end=end)[['Close']].rename(columns={'Close': 'FX_Price'})
        
        # 주가 데이터
        stock = yf.Ticker(stock_code)
        df_stock = stock.history(start=start, end=end)[['Close']].rename(columns={'Close': 'Stock_Price'})
        
        # 타임존 제거
        df_fx.index = df_fx.index.tz_localize(None)
        df_stock.index = df_stock.index.tz_localize(None)
        
        # 병합
        df = pd.merge(df_fx, df_stock, left_index=True, right_index=True, how='inner')
        
        # 변동률 (%) 계산
        df['FX_Change'] = df['FX_Price'].pct_change().abs() * 100 # 환율 절댓값 변동률
        df['Stock_Change'] = df['Stock_Price'].pct_change() * 100 # 당일 주가 변동률
        
        return df.dropna()
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 데이터 로딩
with st.spinner('금융 데이터를 수집하는 중입니다...'):
    data = load_data(selected_code, start_date, end_date)

if data.empty:
    st.warning("선택한 기간의 데이터가 없거나 불러오지 못했습니다. 날짜 범위를 변경해보세요.")
    st.stop()

# [기능 1 적용] 시차(Lag) 반영 데이터 생성
# 오늘의 환율 변동(t)과 N일 뒤의 주가 변동(t+N)을 같은 행으로 맞춤
if lag_days > 0:
    data['Target_Stock_Change'] = data['Stock_Change'].shift(-lag_days)
    data = data.dropna() # Shift로 인해 생기는 마지막 N개 NaN 행 제거
else:
    data['Target_Stock_Change'] = data['Stock_Change']

# 임계값 기준 구간 분류
data['Group'] = data['FX_Change'].apply(
    lambda x: '반응 구간 (임계값 초과)' if x > threshold else '무시 구간 (임계값 이하)'
)

# ==========================================
# 4. 시각화 및 데이터 분석 리포트
# ==========================================

# --- [파트 1] 시계열 추이 비교 차트 ---
st.subheader("1. 원/달러 환율 추이 vs 기업 주가 추이")

fig1 = make_subplots(specs=[[{"secondary_y": True}]])

fig1.add_trace(
    go.Scatter(x=data.index, y=data['Stock_Price'], name=selected_company_name, line=dict(color='#2b5c8f', width=2)),
    secondary_y=False
)
fig1.add_trace(
    go.Scatter(x=data.index, y=data['FX_Price'], name="원/달러 환율 (KRW)", line=dict(color='#e67e22', width=2, dash='dot')),
    secondary_y=True
)

fig1.update_layout(
    height=400,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig1.update_yaxes(title_text="주가 (원)", secondary_y=False)
fig1.update_yaxes(title_text="환율 (원)", secondary_y=True)

st.plotly_chart(fig1, use_container_width=True)

st.divider()

# --- [파트 2] 합리적 무시 & 시차 효과 실증 분석 ---
lag_text = "당일" if lag_days == 0 else f"{lag_days}일 후"
st.subheader(f"2. '합리적 무시' 및 시차 효과 분석 (환율 변동 {lag_text} 주가 반응)")

group_ignored = data[data['Group'] == '무시 구간 (임계값 이하)']
group_reacted = data[data['Group'] == '반응 구간 (임계값 초과)']

avg_vol_ignored = group_ignored['Target_Stock_Change'].abs().mean() if len(group_ignored) > 0 else 0
avg_vol_reacted = group_reacted['Target_Stock_Change'].abs().mean() if len(group_reacted) > 0 else 0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="무시 구간 평균 주가 변동폭",
        value=f"{avg_vol_ignored:.2f}%",
        delta=f"환율 변동 {threshold}% 이하 (총 {len(group_ignored)}일)",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="반응 구간 평균 주가 변동폭",
        value=f"{avg_vol_reacted:.2f}%",
        delta=f"환율 변동 {threshold}% 초과 (총 {len(group_reacted)}일)",
        delta_color="inverse"
    )

with col3:
    if avg_vol_ignored > 0:
        ratio = avg_vol_reacted / avg_vol_ignored
        st.metric(
            label="반응 민감도 증가율",
            value=f"{ratio:.1f} 배",
            help="임계값을 넘어섰을 때 주가 변동성이 몇 배 커지는지 나타냅니다."
        )
    else:
        st.metric(label="반응 민감도 증가율", value="계산 불가")

# --- [파트 3] 산점도 시각화 ---
fig2 = px.scatter(
    data,
    x='FX_Change',
    y='Target_Stock_Change',
    color='Group',
    color_discrete_map={
        '무시 구간 (임계값 이하)': '#95a5a6',
        '반응 구간 (임계값 초과)': '#e74c3c'
    },
    labels={
        'FX_Change': '환율 일간 변동률 (%)', 
        'Target_Stock_Change': f'주가 변동률 (% / {lag_text})'
    },
    title=f"환율 변동률 대비 {lag_text} 주가 변동 분포 (임계값: {threshold}%)"
)

fig2.add_vline(x=threshold, line_width=2, line_dash="dash", line_color="red")

st.plotly_chart(fig2, use_container_width=True)

# 종합 인사이트 요약 상자
st.info(f"""
📌 **실증 분석 결과 요약 ({lag_text} 반영 기준)**
* 환율 인지 임계값 **({threshold}%)** 이하에서는 {lag_text} 주가 변동폭이 평균 **{avg_vol_ignored:.2f}%**였습니다.
* 그러나 환율 변동률이 임계값을 초과하는 **반응 구간**에 진입하면 {lag_text} 주가 변동폭이 평균 **{avg_vol_reacted:.2f}%**로 크게 달라졌습니다.
* *(Tip: 사이드바의 **'시차(Lag) 설정'**을 바꿔가며 0일, 1일, 2일 후 중 어느 시점에 반응 민감도 증가율이 가장 커지는지 비교해 보세요!)*
""")

st.divider()

# ==========================================
# [기능 3] 분석 결과 CSV 데이터 다운로드
# ==========================================
st.subheader("3. 📥 분석 데이터 내보내기 (Export)")

# 다운로드용 데이터프레임 정리 (한글 컬럼명 변환)
export_df = data[['FX_Price', 'Stock_Price', 'FX_Change', 'Target_Stock_Change', 'Group']].copy()
export_df.columns = ['원/달러 환율(원)', f'{selected_company_name} 주가(원)', '환율 일간 변동률(%)', f'주가 변동률(%, {lag_text})', '구간 분류']

# 엑셀 깨짐 방지를 위해 utf-8-sig 인코딩 적용
csv_data = export_df.to_csv(index=True).encode('utf-8-sig')

st.download_button(
    label="📄 분석 결과 데이터셋 (CSV) 다운로드",
    data=csv_data,
    file_name=f"FX_Stock_Lag{lag_days}_{selected_code}_{start_date}_{end_date}.csv",
    mime="text/csv",
    help="현재 설정된 조건으로 분석된 일자별 데이터를 CSV 파일로 저장합니다."
)
