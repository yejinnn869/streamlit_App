# ecos_api.py

import requests
import pandas as pd
import streamlit as st

from config import ECOS_API_KEY, ECOS_BASE_URL

# ===========================
# ECOS API 호출
# ===========================

@st.cache_data(ttl=60 * 60)
def call_ecos(stat_code, item_code, start, end, cycle="M"):
    """
    ECOS API 호출

    Parameters
    ----------
    stat_code : 통계표 코드
    item_code : 항목 코드
    start : 시작기간
    end : 종료기간
    cycle : M,Q,A
    """

    if ECOS_API_KEY == "":
        st.error("ECOS API Key가 등록되지 않았습니다.")
        st.stop()

    url = (
        f"{ECOS_BASE_URL}/StatisticSearch/"
        f"{ECOS_API_KEY}/json/kr/"
        f"1/1000/"
        f"{stat_code}/"
        f"{cycle}/"
        f"{start}/"
        f"{end}/"
        f"{item_code}"
    )

    response = requests.get(url, timeout=20)

    if response.status_code != 200:
        raise Exception("ECOS API 호출 실패")

    data = response.json()

    if "StatisticSearch" not in data:
        raise Exception("조회된 데이터가 없습니다.")

    rows = data["StatisticSearch"]["row"]

    df = pd.DataFrame(rows)

    return df


#날짜 변환
def preprocess(df):

    df = df.copy()

    df["TIME"] = pd.to_datetime(df["TIME"])

    df["DATA_VALUE"] = pd.to_numeric(
        df["DATA_VALUE"],
        errors="coerce"
    )

    df = df.sort_values("TIME")

    df = df.reset_index(drop=True)

    return df

#최신 데이터 날짜
def latest_date(df):

    if len(df) == 0:
        return None

    return df["TIME"].max()

#특정 컬럼명 변경
def rename_column(df, new_name):

    df = df.rename(
        columns={
            "DATA_VALUE": new_name
        }
    )

    return df[
        [
            "TIME",
            new_name
        ]
    ]

#여러 데이터 병합
def merge_dataframes(dataframes):

    merged = dataframes[0]

    for df in dataframes[1:]:

        merged = pd.merge(

            merged,

            df,

            on="TIME",

            how="inner"

        )

    return merged

#결측치 제거
def clean(df):

    df = df.dropna()

    df = df.reset_index(drop=True)

    return df

#ecos 연결 테스트
def test_connection():

    try:

        url = (
            f"{ECOS_BASE_URL}/StatisticTableList/"
            f"{ECOS_API_KEY}/json/kr/1/5"
        )

        response = requests.get(url, timeout=10)

        return response.status_code == 200

    except Exception:

        return False

#api연결 상태
def api_status():

    if test_connection():

        return "🟢 정상"

    return "🔴 연결 실패"

#데이터 정보
def dataset_info(df):

    return {

        "rows": len(df),

        "start": df["TIME"].min(),

        "end": df["TIME"].max()

    }
