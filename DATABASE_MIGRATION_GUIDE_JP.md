# データベース移行ガイド

## 概要

このガイドでは、JSONベースのキャッシュシステムから新しいSQLiteデータベースバックエンドへの移行方法について説明します。

## 新機能

### 追加された機能

1. **データベースバックエンド**：SQLiteデータベースがJSONファイルキャッシュを置き換え
2. **複数ポートフォリオサポート**：1つのデータベースで複数のポートフォリオを管理
3. **履歴追跡**：時間経過に伴うポートフォリオ価値の自動追跡
4. **パフォーマンス向上**：より高速なクエリと並行アクセス
5. **データ整合性**：ACIDトランザクションと参照整合性

### データベーススキーマ

新しいシステムは以下のテーブルを使用します：

- `ticker_cache`：キャッシュされたティッカーデータ（価格、ボラティリティ、メタデータ）を保存
- `portfolios`：ポートフォリオの定義
- `portfolio_holdings`：各ポートフォリオの現在の保有
- `portfolio_history`：ポートフォリオ価値の履歴スナップショット

## 移行手順

### オプション1：自動移行（推奨）

`data/ticker_cache.json`に既存のJSONキャッシュファイルがある場合：

```bash
python -m src.database.migrate_json_to_db
```

これにより：
1. `data/portfolio.db`に新しいデータベースが作成されます
2. JSONキャッシュからすべてのティッカーデータがインポートされます
3. `data/ticker_cache.json.backup`にJSONファイルのバックアップが作成されます

### オプション2：クリーンスタート

既存のキャッシュがない場合、または新しく始めたい場合：

```bash
# データベースを初期化（初回使用時に自動的に実行されます）
python -c "from src.database import init_db; init_db()"
```

### オプション3：CSVからポートフォリオをインポート

既存のポートフォリオCSVファイルをインポート：

```bash
# 新しいデータベースバックエンド計算機を使用
python portfolio_calculator_db.py portfolio.csv --name "US Portfolio"
python portfolio_calculator_db.py portfolio_jp.csv --name "JP Portfolio"
```

またはPython APIを使用：

```python
from src.database import PortfolioManager

mgr = PortfolioManager()
mgr.import_from_csv("portfolio.csv", "US Portfolio")
mgr.import_from_csv("portfolio_jp.csv", "JP Portfolio")
mgr.close()
```

## 使用方法

### 新しい計算機の使用

新しい計算機は古いものと同じように動作します：

```bash
# 基本的な使用方法
python portfolio_calculator_db.py portfolio.csv

# オプション付き
python portfolio_calculator_db.py portfolio.csv --force-refresh --name "My Portfolio"
```

### 新しいUIの使用

マルチポートフォリオUIを起動：

```bash
streamlit run portfolio_app_db.py
```

機能：
- 複数のポートフォリオから選択
- CSVからポートフォリオをインポート
- 新しいポートフォリオを作成
- 履歴パフォーマンスを表示
- 複数のポートフォリオを比較

### プログラマティックアクセス

```python
from src.database import (
    DatabaseCacheManager,
    PortfolioManager,
    init_db
)

# データベースを初期化
init_db()

# キャッシュを操作
cache_mgr = DatabaseCacheManager()
ticker_data = cache_mgr.get_ticker("AAPL")
cache_mgr.close()

# ポートフォリオを操作
portfolio_mgr = PortfolioManager()

# ポートフォリオを作成
portfolio = portfolio_mgr.create_portfolio("My Portfolio")

# 保有を追加
holdings = [
    {'ticker': 'AAPL', 'shares': 10},
    {'ticker': 'GOOGL', 'shares': 5}
]
portfolio_mgr.set_holdings(portfolio.id, holdings)

# 履歴を取得
history = portfolio_mgr.get_history(portfolio.id, days=30)
print(history)

portfolio_mgr.close()
```

## 後方互換性

古い`portfolio_calculator.py`はJSONキャッシュで引き続き動作します。両方のシステムを使用できます：

- 旧システム：`python portfolio_calculator.py portfolio.csv`
- 新システム：`python portfolio_calculator_db.py portfolio.csv`

ただし、より良い機能のためにデータベースシステムへの移行をお勧めします。

## データベースの場所

- データベースファイル：`data/portfolio.db`
- バックアップ推奨：バックアップのためにこのファイルを定期的にコピー

## トラブルシューティング

### データベースロックエラー

「database is locked」エラーが表示される場合：
1. データベースを使用しているすべてのアプリを閉じる
2. 古い接続を確認：`lsof data/portfolio.db`
3. アプリケーションを再起動

### 移行の失敗

移行が失敗した場合：
1. バックアップファイルが存在することを確認：`data/ticker_cache.json.backup`
2. エラーメッセージを確認
3. 手動移行または新規開始を試す

### データが表示されない

移行後：
1. データベースが存在することを確認：`ls -l data/portfolio.db`
2. データがインポートされたことを確認：
   ```python
   from src.database import get_session, TickerCache
   session = get_session()
   count = session.query(TickerCache).count()
   print(f"Tickers in database: {count}")
   ```

## パフォーマンスのヒント

1. **force_refreshを控えめに使用**：必要な場合のみ`--force-refresh`を使用
2. **定期的な更新**：キャッシュをウォームに保つためにデータを定期的に更新
3. **データベースをバキューム**：定期的にデータベースで`VACUUM`を実行
   ```bash
   sqlite3 data/portfolio.db "VACUUM;"
   ```

## 高度な機能

### 履歴追跡

ポートフォリオの値は自動的に追跡されます。履歴を表示：

```python
from src.database import PortfolioManager

mgr = PortfolioManager()
history = mgr.get_history(portfolio_id=1, days=365)
print(history)
```

### 複数のポートフォリオ

複数のポートフォリオを簡単に管理：

```python
mgr = PortfolioManager()

# すべてのポートフォリオをリスト
portfolios = mgr.list_portfolios()

# ポートフォリオを比較
for p in portfolios:
    holdings = mgr.get_holdings(p.id)
    print(f"{p.name}: {len(holdings)} holdings")
```

## 今後の機能強化

データベースバックエンドにより将来の機能が可能に：
- 機械学習予測（フェーズ4）
- WebSocket経由のリアルタイム更新（フェーズ5）
- ニュースとセンチメント分析（フェーズ6）
- ユーザー認証とマルチユーザーサポート
- クラウドデータベースサポート

## サポート

問題や質問がある場合：
1. テストファイルを確認：`test_database.py`
2. 実装を確認：`src/database/`
3. GitHubのissueを開く

## データベーススキーマリファレンス

### ticker_cache
- `ticker`（文字列）：株式ティッカーシンボル
- `price`（浮動小数点）：現在の価格
- `price_updated`（日時）：最終価格更新
- `name`、`sector`、`industry`、`country`：メタデータ
- `sigma`、`sharpe`：リスク指標
- `history`：過去の価格（JSON）

### portfolios
- `id`：主キー
- `name`：ポートフォリオ名
- `description`：説明
- `is_active`：アクティブステータス

### portfolio_holdings
- `portfolio_id`：portfoliosへの外部キー
- `ticker`：株式ティッカー
- `shares`：株式数

### portfolio_history
- `portfolio_id`：portfoliosへの外部キー
- `total_value_usd`、`total_value_jpy`：ポートフォリオ価値
- `snapshot_date`：タイムスタンプ
- `holdings_snapshot`：詳細な保有（JSON）
