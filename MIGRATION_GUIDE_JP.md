# モジュール構造への移行ガイド

> 📘 **English Version** | [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

このガイドは、旧モノリシック構造から新しいモジュール構造への移行を支援します。

## 何が変わりましたか？

### ディレクトリ構造

**以前：**
```
Finance_portfolio/
├── portfolio_calculator.py
├── efficient_frontier.py
├── sharpe_optimized.py
├── crash_scenario_analysis.py
├── portfolio_app.py
└── get_stock_price.py
```

**現在：**
```
Finance_portfolio/
├── src/
│   ├── core/
│   │   └── portfolio_calculator.py
│   ├── data/
│   │   ├── cache_manager.py
│   │   └── stock_data_fetcher.py
│   ├── analysis/
│   │   ├── efficient_frontier.py
│   │   ├── sharpe_optimized.py
│   │   └── crash_scenario_analysis.py
│   ├── ui/
│   │   ├── chart_utils.py
│   │   └── data_loader.py
│   └── utils/
│       ├── config.py
│       ├── file_utils.py
│       └── region_classifier.py
├── portfolio_calculator.py （レガシー、まだ動作します）
├── portfolio_calculator_new.py （新しいエントリーポイント）
└── portfolio_app.py （次回リファクタリング予定）
```

## 移行手順

### 1. コマンドライン使用の場合

**旧方式（まだ動作します）：**
```bash
python portfolio_calculator.py portfolio.csv
python portfolio_calculator.py portfolio_jp.csv --force-refresh
```

**新方式（推奨）：**
```bash
python portfolio_calculator_new.py portfolio.csv
python portfolio_calculator_new.py portfolio_jp.csv --force-refresh
```

どちらも同じように動作します！旧スクリプトは後方互換性のために保持されています。

### 2. Pythonコードでのインポートの場合

**旧インポート：**
```python
from portfolio_calculator import PortfolioCalculator
from efficient_frontier import calculate_efficient_frontier
from sharpe_optimized import calculate_sharpe_scores
```

**新インポート：**
```python
from src.core import PortfolioCalculator
from src.analysis import calculate_efficient_frontier, calculate_sharpe_scores
from src.data import CacheManager, StockDataFetcher
from src.ui import DataLoader, chart_utils
from src.utils import Config, RegionClassifier
```

### 3. Streamlitアプリ（portfolio_app.py）の場合

Streamlitアプリは現在も旧インポートを使用しています。これは今後のフェーズで更新されます。

**現在（動作します）：**
```python
from portfolio_calculator import PortfolioCalculator
from efficient_frontier import calculate_efficient_frontier
```

**将来（新しいコードで推奨）：**
```python
from src.core import PortfolioCalculator
from src.analysis import calculate_efficient_frontier
```

## 後方互換性

### まだ動作するもの

✅ すべての既存コマンドラインスクリプト
✅ すべての既存Pythonインポート（旧モジュールはルートに残っています）
✅ すべてのCSV入力ファイル（portfolio.csv、portfolio_jp.csv）
✅ すべての出力形式（結果ファイル、相関マトリックス）
✅ すべてのキャッシュファイル（data/ticker_cache.json）
✅ すべての既存テスト

### 新しい機能

✨ メンテナンスが容易なモジュール構造
✨ 分離された関心事（データ、ビジネスロジック、UI、分析）
✨ 集中設定
✨ 再利用可能なUIコンポーネント
✨ テスト可能性の向上
✨ より明確なコード構成

## 使用例

### 例1：新しいポートフォリオ計算機の使用

```python
from src.core import PortfolioCalculator

# 計算機を作成
calculator = PortfolioCalculator(
    csv_file="portfolio.csv",
    force_refresh=False
)

# 計算を実行
calculator.run()
```

### 例2：キャッシュマネージャーの使用

```python
from src.data import CacheManager

# キャッシュを初期化
cache = CacheManager(cache_dir="data")

# データ更新が必要かチェック
if cache.needs_price_update("AAPL"):
    print("新しい価格データを取得する必要があります")

# キャッシュされたデータを取得
data = cache.get("AAPL")

# キャッシュを保存
cache.save()
```

### 例3：データフェッチャーの使用

```python
from src.data import StockDataFetcher

# フェッチャーを作成
fetcher = StockDataFetcher()

# リスクフリーレートを取得
rf_rate = fetcher.get_risk_free_rate()

# 株式情報を取得
info = fetcher.get_stock_info("AAPL")

# 価格履歴を取得
history = fetcher.get_stock_history("AAPL", period="1y")

# ボラティリティを計算
sigma, sharpe = fetcher.calculate_volatility_and_sharpe(history)
```

### 例4：設定の使用

```python
from src.utils import config

# 設定にアクセス
print(config.DATA_DIR)  # "data"
print(config.OUTPUT_DIR)  # "output"
print(config.DEFAULT_RISK_FREE_RATE)  # 4.0

# ディレクトリが存在することを確認
config.ensure_directories()
```

### 例5：地域分類器の使用

```python
from src.utils import RegionClassifier

# 国を分類
region = RegionClassifier.classify("Japan")  # "Asia"
region = RegionClassifier.classify("United States")  # "North America"

# すべての地域を取得
regions = RegionClassifier.get_all_regions()
```

### 例6：ファイルユーティリティの使用

```python
from src.utils import file_utils

# 最新の結果ファイルを取得
latest = file_utils.get_latest_result_file("portfolio_result_*.csv")

# タイムスタンプを抽出
timestamp = file_utils.extract_timestamp_from_filename(latest)

# 相関ファイルを検索
corr_file = file_utils.find_correlation_file(latest)

# すべての結果ファイルを取得
us_files, jp_files = file_utils.get_portfolio_files()
```

### 例7：UIコンポーネントの使用

```python
from src.ui import DataLoader, chart_utils

# データをロード
loader = DataLoader()
df, files = loader.load_combined_latest()

# チャートを作成
fig = chart_utils.create_pie_chart(
    data=df,
    values_col="value_jp",
    names_col="ticker",
    title="ポートフォリオ配分"
)

# モバイルレイアウトを適用
fig = chart_utils.apply_mobile_layout(fig)
```

## 移行のテスト

### 1. インポートのテスト

```bash
python3 -c "from src.core import PortfolioCalculator; print('✓ インポート成功')"
```

### 2. 計算のテスト

```bash
python portfolio_calculator_new.py portfolio.csv
```

### 3. テストの実行

```bash
python test_efficient_frontier.py
python test_cache.py
python test_risk_free_rate.py
```

## トラブルシューティング

### インポートエラー

次のようなエラーが表示される場合：
```
ModuleNotFoundError: No module named 'src'
```

解決方法：プロジェクトルートをPythonパスに追加：
```python
import sys
sys.path.insert(0, '/path/to/Finance_portfolio')
```

### キャッシュの問題

キャッシュの動作がおかしい場合：
```python
from src.data import CacheManager

cache = CacheManager()
cache.clear()  # すべてのキャッシュをクリア
cache.save()
```

### 設定の問題

設定が環境に合わない場合：
```python
from src.utils import Config

# 設定を変更
Config.DATA_DIR = "my_data"
Config.OUTPUT_DIR = "my_output"
```

## ロールバック計画

旧構造に戻す必要がある場合：

1. 旧モジュールはルートディレクトリにまだ存在します
2. 旧インポートとスクリプトを使用するだけです
3. すべての機能はそのまま残っています

## 次のステップ

1. **フェーズ1**：新しいコードで新しいインポートの使用を開始
2. **フェーズ2**：既存スクリプトを徐々に移行
3. **フェーズ3**：新しいモジュールを使用するようにportfolio_app.pyをリファクタリング
4. **フェーズ4**：完全に移行したらレガシーモジュールを削除

## 質問がありますか？

- 設計の詳細については`ARCHITECTURE_JP.md`を確認
- APIドキュメントについてはモジュールのdocstringを確認
- このガイドのサンプルコードを調査
- 使用パターンについては既存のテストを確認

## 移行のメリット

✨ **メンテナンスが容易**：明確なモジュール境界
✨ **テストが容易**：依存関係を簡単にモック化
✨ **拡張が容易**：既存コードに触れずに新機能を追加
✨ **パフォーマンスの向上**：最適化されたキャッシングとデータアクセス
✨ **よりスケーラブル**：大規模開発に対応
