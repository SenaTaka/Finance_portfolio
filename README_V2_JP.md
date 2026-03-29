# Finance Portfolio マネジメントシステム v2.0

> **Version 2.0** - 完全なエンタープライズポートフォリオ管理プラットフォーム

機械学習予測、リアルタイム更新、センチメント分析を備えた包括的なデータベースバックエンドポートフォリオ管理システム。

---

## 🌟 Version 2.0の新機能

### 追加された主要機能

1. **💾 データベースバックエンド** - JSONキャッシュを置き換えるSQLiteデータベース
2. **📊 ポートフォリオ履歴** - 時間経過に伴う自動価値追跡
3. **📁 複数ポートフォリオ** - 無制限のポートフォリオを管理
4. **🤖 ML予測** - AIによる株価予測
5. **⚡ リアルタイム更新** - WebSocket価格ストリーミング
6. **📰 ニュースとセンチメント** - マーケットセンチメント分析

---

## �� クイックスタート

### インストール

\`\`\`bash
# リポジトリのクローン
git clone https://github.com/SenaTaka/Finance_portfolio.git
cd Finance_portfolio

# 依存関係のインストール
pip install -r requirements.txt

# データベースの初期化
python db_manager.py init
\`\`\`

### 最初のポートフォリオをインポート

\`\`\`bash
# CSVからインポート
python db_manager.py import portfolio.csv --name "My Portfolio"

# UIを起動
streamlit run portfolio_app_db.py
\`\`\`

---

## 📚 コア機能

### 1. データベース管理

**JSONキャッシュをSQLiteデータベースに置き換え：**

\`\`\`bash
# データベースを初期化
python db_manager.py init

# 既存のJSONキャッシュを移行
python db_manager.py migrate

# ポートフォリオをリスト
python db_manager.py list

# ポートフォリオ詳細を表示
python db_manager.py show 1

# キャッシュ統計
python db_manager.py cache
\`\`\`

### 2. ポートフォリオ管理

**複数のポートフォリオを作成および管理：**

\`\`\`python
from src.database import PortfolioManager

mgr = PortfolioManager()

# ポートフォリオを作成
portfolio = mgr.create_portfolio("Tech Stocks", "High growth tech companies")

# 保有を追加
holdings = [
    {'ticker': 'AAPL', 'shares': 10},
    {'ticker': 'GOOGL', 'shares': 5}
]
mgr.set_holdings(portfolio.id, holdings)

# 保有を取得
df = mgr.get_holdings(portfolio.id)

# 履歴を取得
history = mgr.get_history(portfolio.id, days=30)
\`\`\`

### 3. 機械学習予測

**AIを活用した株価予測：**

\`\`\`python
from src.ml import StockPredictor, PortfolioPredictor

# 個別銘柄の予測
predictor = StockPredictor("AAPL")
prediction = predictor.predict()
print(f"Predicted price: ${prediction['next_day']:.2f}")

# ポートフォリオ全体の予測
portfolio_pred = PortfolioPredictor(portfolio_id=1)
results = portfolio_pred.predict_all()
\`\`\`

### 4. リアルタイム更新

**WebSocketを介したライブ価格ストリーミング：**

\`\`\`bash
# リアルタイムサーバーを起動
python realtime_server.py --port 8765

# Python APIを使用
from src.realtime import RealTimePriceUpdater

updater = RealTimePriceUpdater()
prices = updater.get_latest_prices(['AAPL', 'GOOGL'])
\`\`\`

### 5. ニュースとセンチメント分析

**マーケットニュースとAIセンチメントスコアリング：**

\`\`\`python
from src.news import NewsFetcher, SentimentAnalyzer

# ニュースを取得
fetcher = NewsFetcher()
articles = fetcher.fetch_news("AAPL", num_articles=10)

# センチメントを分析
analyzer = SentimentAnalyzer()
sentiment = analyzer.analyze_sentiment(articles)
print(f"Overall sentiment: {sentiment['label']}")
\`\`\`

---

## 📖 ドキュメント

- [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) - データベース移行
- [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) - 高度な機能
- [FEATURE_IMPLEMENTATION_SUMMARY.md](FEATURE_IMPLEMENTATION_SUMMARY.md) - 完全な機能ドキュメント

---

## 🧪 テスト

\`\`\`bash
# すべてのテストを実行
python test_database.py
python test_ml.py
python test_news.py
python test_ui_advanced_features.py
\`\`\`

---

## 🌟 主な改善点

Version 2.0は以下を提供します：

✅ **エンタープライズ対応** - 本番環境でのデータベースバックエンド
✅ **高度な分析** - ML予測とセンチメント分析
✅ **リアルタイムデータ** - ライブ価格更新
✅ **複数ポートフォリオ** - 無制限のポートフォリオ管理
✅ **履歴追跡** - 時間経過のパフォーマンス
✅ **スケーラブル** - 大規模展開に対応

---

**注意**：Version 2.0はVersion 1.0から大幅にアップグレードされています。移行手順については[DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md)を参照してください。
