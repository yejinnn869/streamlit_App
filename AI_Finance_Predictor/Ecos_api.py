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
