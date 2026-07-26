# ecos_codes.py

ECOS_INDICATORS = {

    "cd91": {
    "STAT_CODE": "721Y001",
    "STAT_NAME": "1.3.2.2. 시장금리(월,분기,년)",
    "ITEM_CODE1": "2010000",
    "ITEM_NAME1": "CD91",   # 실제 ECOS 코드로 교체
    "CYCLE": "M"
    },

    "cpi": {
    "STAT_CODE": "901Y009",
    "STAT_NAME": "4.2.1. 소비자물가지수",
    "ITEM_CODE1": "0",
    "ITEM_NAME1": "소비자물가지수",   # 실제 ECOS 코드로 교체
    "CYCLE": "M"
    },

    "exchange": {
        "STAT_CODE": "731Y004",
        "STAT_NAME": "3.2.1.2. 주요국 통화의 대원화환율",
        "ITEM_CODE1": "0000001",
        "ITEM_NAME1": "원/미국달러(매매기준율)",
        "CYCLE": "M"
    },

    "m2": {
        "STAT_CODE": "161Y013",
        "STAT_NAME": "1.1.3.3.1. M2 기관별 구성내역(평잔)",
        "ITEM_CODE1": "BBJA00",
        "ITEM_NAME1": "M2(평잔)",
        "CYCLE": "M"
    },

    "household_credit": {
      "STAT_CODE": "151Y002",
        "STAT_NAME": "1.2.4.2.1. 예금취급기관 가계대출(업권별,월),
        "ITEM_CODE1": "1110000",
        "ITEM_NAME1": "예금취급기관",
        "CYCLE": "M"
    },

}
