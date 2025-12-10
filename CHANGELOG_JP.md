# 変更履歴

このファイルには、このプロジェクトのすべての注目すべき変更が記録されます。

フォーマットは[Keep a Changelog](https://keepachangelog.com/en/1.0.0/)に基づいており、
このプロジェクトは[セマンティックバージョニング](https://semver.org/spec/v2.0.0.html)に準拠しています。

## [2.0.0] - 2024-12-09

### 追加 - 主要機能（全6フェーズ）

#### フェーズ1：データベース統合
- JSONキャッシュを置き換えるSQLiteデータベースバックエンド
- TTLサポート付きの効率的なキャッシング用`DatabaseCacheManager`
- ポートフォリオCRUD操作用`PortfolioManager`
- データベースモデル：`TickerCache`、`Portfolio`、`PortfolioHolding`、`PortfolioHistory`
- JSONからデータベースへの移行用移行スクリプト`migrate_json_to_db.py`
- データベース管理用CLIツール`db_manager.py`
- データベースバックエンド付き`portfolio_calculator_db.py`
- `DATABASE_MIGRATION_GUIDE.md`での包括的な移行ドキュメント

#### フェーズ2：履歴追跡
- 時間経過に伴うポートフォリオ価値の自動追跡
- 時系列データ付き`PortfolioHistory`モデル
- 期間フィルタリング付き履歴クエリメソッド
- UIでの視覚的な履歴トレンド

#### フェーズ3：複数ポートフォリオサポート
- ユーザーごとの無制限のポートフォリオのサポート
- ポートフォリオ比較機能
- マルチポートフォリオUI `portfolio_app_db.py`
- UI経由でCSVからポートフォリオをインポート
- 並列ポートフォリオ価値比較

#### フェーズ4：機械学習予測
- Random ForestとGradient Boostingを使用した株価予測
- 15以上のテクニカル指標を使用した特徴量エンジニアリング：
  - 移動平均（SMA、EMA）
  - MACD（移動平均収束拡散）
  - RSI（相対力指数）
  - ボリンジャーバンド
  - ボラティリティとモメンタム指標
- 個別銘柄用`StockPredictor`クラス
- ポートフォリオレベルの予測用`PortfolioPredictor`
- 翌日および複数日の価格予測
- モデルの永続化（保存/読み込み）
- 特徴量の重要度分析

#### フェーズ5：リアルタイム更新（WebSocket）
- リアルタイム価格ストリーミング用WebSocketサーバー
- サブスクリプションベースのアーキテクチャ
- クライアント接続管理用`PriceStreamServer`
- 継続的な価格更新用`RealTimePriceUpdater`
- CLIサーバー`realtime_server.py`
- 設定可能な更新間隔
- マルチクライアントサポート

#### フェーズ6：ニュースとセンチメント分析
- Yahoo Financeからのニュース取得
- 記事取得用`NewsFetcher`
- 複数の方法を持つ`SentimentAnalyzer`：
  - TextBlobベースのNLPセンチメント分析
  - キーワードベースのセンチメント分析（フォールバック）
- 記事レベルおよびティッカーレベルのセンチメントスコアリング
- センチメント予測の信頼度スコアリング
- ポートフォリオニュースフィード集約

### 追加 - インフラストラクチャ
- 包括的なテストスイート：
  - `test_database.py` - データベース操作
  - `test_ml.py` - 機械学習予測
  - `test_news.py` - ニュースとセンチメント分析
- ドキュメント：
  - `DATABASE_MIGRATION_GUIDE.md` - 移行手順
  - `FEATURE_IMPLEMENTATION_SUMMARY.md` - 完全な機能ドキュメント
- セマンティックバージョニング付きバージョンファイル`VERSION`

### 変更
- 新しい依存関係で`requirements.txt`を更新：
  - sqlalchemy>=1.4.0
  - alembic>=1.7.0
  - scikit-learn>=1.0.0
  - websockets>=10.0
  - textblob>=0.15.0
- 安定性のためすべての依存関係にバージョン制約を追加

### 修正
- `cache_manager.py`の例外処理がスタックトレースを保持するように修正
- WebSocketブロードキャストが閉じられた接続をフィルタリングするように修正
- すべてのモジュールでエラー処理を改善

### 非推奨
- JSONキャッシュシステム（後方互換性のためまだサポート）
- 単一ポートフォリオUI `portfolio_app.py`（代わりに`portfolio_app_db.py`を使用）

### セキュリティ
- より良いセキュリティのためにデータベース接続プーリングを追加
- データ漏洩を防ぐための適切なエラー処理を実装
- すべてのAPIエンドポイントに入力検証を追加

## [1.0.0] - 以前のリリース

### 初期機能
- JSONキャッシュ付き基本ポートフォリオ計算機
- Yahoo Finance統合
- リスク指標計算（シャープレシオ、ボラティリティ）
- 効率的フロンティア分析
- Streamlit UI
- ポートフォリオリバランス提案

---

移行手順については、[DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md)を参照してください。

完全な機能ドキュメントについては、[FEATURE_IMPLEMENTATION_SUMMARY.md](FEATURE_IMPLEMENTATION_SUMMARY.md)を参照してください。
