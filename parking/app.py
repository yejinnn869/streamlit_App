import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="서울시 공영주차장",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 서울시 공영주차장 안내")
st.write("서울시 공영주차장 위치와 정보를 확인하세요.")

# -----------------------
# CSV 업로드
# -----------------------
uploaded_file = st.file_uploader(
    "서울시 공영주차장 CSV를 업로드하세요.",
    type=["csv"]
)

if uploaded_file is None:
    st.info("CSV 파일을 업로드하면 지도가 표시됩니다.")
    st.stop()

# 인코딩 자동 처리
try:
    df = pd.read_csv(uploaded_file, encoding="cp949")
except:
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file, encoding="utf-8")

# -----------------------
# 데이터 전처리
# -----------------------
df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

df = df.dropna(subset=["위도", "경도"])

# 무료 여부
df["무료"] = df["유무료구분명"] == "무료"

# -----------------------
# 사이드바
# -----------------------
st.sidebar.header("검색")

only_free = st.sidebar.checkbox("무료 주차장만 보기")

if only_free:
    df = df[df["무료"]]

parking = st.sidebar.selectbox(
    "주차장 선택",
    ["전체 보기"] + sorted(df["주차장명"].tolist())
)

# -----------------------
# 지도 생성
# -----------------------
if len(df) == 0:
    st.error("표시할 주차장이 없습니다.")
    st.stop()

center = [df["위도"].mean(), df["경도"].mean()]

m = folium.Map(location=center, zoom_start=11)

# -----------------------
# 전체 보기
# -----------------------
if parking == "전체 보기":

    for _, row in df.iterrows():

        color = "green" if row["무료"] else "blue"

        popup = f"""
        <b>{row['주차장명']}</b><br>
        {row['주소']}<br>
        {row['유무료구분명']}<br>
        기본요금 : {row['기본 주차 요금']}원
        """

        folium.Marker(
            [row["위도"], row["경도"]],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(m)

# -----------------------
# 선택 보기
# -----------------------
else:

    row = df[df["주차장명"] == parking].iloc[0]

    m = folium.Map(
        location=[row["위도"], row["경도"]],
        zoom_start=16
    )

    color = "green" if row["무료"] else "blue"

    folium.Marker(
        [row["위도"], row["경도"]],
        popup=row["주차장명"],
        icon=folium.Icon(color=color)
    ).add_to(m)

    st.subheader(row["주차장명"])

    c1, c2 = st.columns(2)

    with c1:
        st.write("📍 주소")
        st.write(row["주소"])

        st.write("☎ 전화번호")
        st.write(row["전화번호"])

        st.write("🚗 주차면수")
        st.write(int(row["총 주차면"]))

        st.write("🏷️ 주차장 종류")
        st.write(row["주차장 종류명"])

    with c2:
        st.write("💰 기본요금")
        st.write(f"{row['기본 주차 요금']}원")

        st.write("⏱ 기본시간")
        st.write(f"{row['기본 주차 시간(분 단위)']}분")

        st.write("🕒 평일 운영")
        st.write(
            f"{row['평일 운영 시작시각(HHMM)']} ~ {row['평일 운영 종료시각(HHMM)']}"
        )

        st.write("💵 유무료")
        st.write(row["유무료구분명"])

# -----------------------
# 지도 출력
# -----------------------
st_folium(
    m,
    width=1200,
    height=700
)
