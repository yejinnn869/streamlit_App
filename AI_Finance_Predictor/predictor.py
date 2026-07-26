# predictor.py

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

from ecos_api import load_all_data


# ======================================
# 데이터 불러오기
# ======================================

def load_dataset():
    """
    ECOS API에서 전체 데이터를 불러온다.
    """

    df = load_all_data(
        start_date="201001",
        end_date="203001"
    )

    return df


# ======================================
# 머신러닝 데이터셋 생성
# ======================================

def make_dataset(df):
    """
    입력 변수(X)와 목표 변수(y)를 생성
    """

    df = df.copy()

    df = df.dropna()

    X = df[
        [
            "cpi",
            "exchange",
            "m2",
            "household_loan"
        ]
    ]

    y = df["cd91"]

    return X, y


# ======================================
# RandomForest
# ======================================

def randomforest_model():

    model = RandomForestRegressor(

        n_estimators=300,

        max_depth=10,

        random_state=42

    )

    return model


# ======================================
# XGBoost
# ======================================

def xgboost_model():

    model = XGBRegressor(

        n_estimators=300,

        learning_rate=0.03,

        max_depth=5,

        random_state=42

    )

    return model


# ======================================
# LightGBM
# ======================================

def lightgbm_model():

    model = LGBMRegressor(

        n_estimators=300,

        learning_rate=0.03,

        random_state=42

    )

    return model


# ======================================
# 모델 학습
# ======================================

def train_models(X, y):

    X_train, X_test, y_train, y_test = train_test_split(

        X,

        y,

        test_size=0.2,

        shuffle=False

    )

    rf = randomforest_model()

    xgb = xgboost_model()

    lgbm = lightgbm_model()

    rf.fit(X_train, y_train)

    xgb.fit(X_train, y_train)

    lgbm.fit(X_train, y_train)

    return (
        rf,
        xgb,
        lgbm,
        X_test,
        y_test
    )
