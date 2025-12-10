"""UI Constants and Configuration.

This module contains constants used across the UI components and pages.
"""

# S&P 500 ticker symbols (try ^SPX first, fallback to ^GSPC)
SP500_TICKERS = ["^SPX", "^GSPC"]

# Treasury rate ticker for risk-free rate
TREASURY_TICKER = "^TNX"

# Default risk-free rate (as fallback)
DEFAULT_RISK_FREE_RATE = 0.04  # 4%

# Advanced Features Configuration
# ML Predictions
ML_MODEL_TYPE = 'random_forest'  # Options: 'random_forest', 'gradient_boosting'
ML_MIN_HISTORY_DAYS = 100  # Minimum days of history required for ML predictions

# Real-time Updates
REALTIME_REFRESH_INTERVAL_MS = 60000  # Auto-refresh interval in milliseconds (60 seconds)
REALTIME_REFRESH_INTERVAL_SEC = 60  # Same in seconds for display

# News & Sentiment
SENTIMENT_USE_TEXTBLOB = False  # Use TextBlob for sentiment (requires installation)

# Mobile-friendly layout CSS
MOBILE_CSS = """
<style>
/* Mobile responsive CSS */
@media (max-width: 768px) {
    .stButton > button {
        min-height: 48px;
        font-size: 16px;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    .stDataFrame {
        overflow-x: auto;
    }
    
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        padding: 10px 16px;
    }
    
    .stSlider > div > div {
        padding: 10px 0;
    }
    
    .stSelectbox > div > div {
        min-height: 44px;
    }
    
    .js-plotly-plot {
        margin-bottom: 20px;
    }
}

@media (hover: none) and (pointer: coarse) {
    .stButton > button {
        min-height: 48px;
        min-width: 48px;
    }
    
    .stSidebar .stNumberInput input,
    .stSidebar .stTextInput input {
        font-size: 16px;
        min-height: 44px;
    }
}

[data-testid="stAppViewContainer"] {
    touch-action: pan-x pan-y;
}
</style>
"""

# UI Text (for potential i18n)
UI_TEXT = {
    'en': {
        'app_title': 'Sena Investment',
        'navigation': 'Navigation',
        'home': '🏠 Home',
        'analysis': '📊 Analysis',
        'optimization': '🎯 Optimization',
        'rebalancing': '⚖️ Rebalancing',
        'history': '📈 History',
        'ml_predictions': '🤖 ML Predictions',
        'news_sentiment': '📰 News & Sentiment',
    },
    'jp': {
        'app_title': 'Sena Investment',
        'navigation': 'ナビゲーション',
        'home': '🏠 ホーム',
        'analysis': '📊 分析',
        'optimization': '🎯 最適化',
        'rebalancing': '⚖️ リバランス',
        'history': '📈 履歴',
        'ml_predictions': '🤖 機械学習予測',
        'news_sentiment': '📰 ニュース・センチメント',
        'backtest_period': '表示期間を選択',
        'backtest_period_help': 'バックテストに使用する期間を選択します',
        'current_portfolio': '現在のポートフォリオ',
        'equal_weight': '等金額ベンチマーク',
        'cumulative_return': '累積リターン',
        'cumulative_return_multiplier': '累積リターン (倍率)',
        'date': '日付',
        'backtest_failed': 'のバックテストに失敗しました',
        'insufficient_data': '選択した期間では十分な価格データがありません。',
    }
}

# Default language
DEFAULT_LANGUAGE = 'en'
