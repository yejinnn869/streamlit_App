# ecos_api.py

import requests
import pandas as pd
import streamlit as st

from config import ECOS_API_KEY, ECOS_BASE_URL


@st.cache_data(ttl=3600)
def get_ecos_data(
    stat_code: str,
    item_code1: str,
    start_date: str,
    end_date: str,
    cycle: str = "M"
):
    """
    ECOS 데이터 조회

    Parameters
    ----------
    stat_code : 통계표 코드
    item_code1 : 항목 코드
    start_date : 시작(예: 201801)
    end_date : 종료(예: 202512)
    cycle : M(월), Q(분기), A(연)

    Returns
    -------
    pandas.DataFrame
    """

    if not ECOS_API_KEY:
        st.error("ECOS API KEY가 등록되어 있지 않습니다.")
        st.stop()

    url = (
        f"{ECOS_BASE_URL}/StatisticSearch/"
        f"{ECOS_API_KEY}/json/kr/"
        f"1/1000/"
        f"{stat_code}/"
        f"{cycle}/"
        f"{start_date}/"
        f"{end_date}/"
        f"{item_code1}"
    )

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()

        if "StatisticSearch" not in data:
            return pd.DataFrame()

        rows = data["StatisticSearch"]["row"]

        df = pd.DataFrame(rows)

        if df.empty:
            return df

        df["TIME"] = pd.to_datetime(df["TIME"], format="%Y%m")
        df["DATA_VALUE"] = pd.to_numeric(
            df["DATA_VALUE"],
            errors="coerce"
        )

        df = df[["TIME", "DATA_VALUE"]]

        return df.sort_values("TIME").reset_index(drop=True)

    except Exception as e:
        st.error(f"ECOS API 오류 : {e}")
        return pd.DataFrame()


def rename_series(df: pd.DataFrame, column_name: str):
    """DATA_VALUE 컬럼 이름 변경"""

    df = df.copy()

    df.rename(
        columns={
            "DATA_VALUE": column_name
        },
        inplace=True
    )

    return df


def merge_dataframes(dataframes):
    """여러 데이터프레임 병합"""

    if not dataframes:
        return pd.DataFrame()

    merged = dataframes[0]

    for df in dataframes[1:]:

        merged = pd.merge(
            merged,
            df,
            on="TIME",
            how="inner"
        )

    return merged


def get_latest_date(df):
    """최신 데이터 날짜"""

    if df.empty:
        return None

    return df["TIME"].max().strftime("%Y-%m")


def test_api():
    """ECOS API 연결 확인"""

    if not ECOS_API_KEY:
        return False

    url = (
        f"{ECOS_BASE_URL}/StatisticTableList/"
        f"{ECOS_API_KEY}/json/kr/1/5"
    )

    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200

    except:
        return False
