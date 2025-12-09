# Finance Portfolio Management System（ファイナンス・ポートフォリオ管理システム）

モダンポートフォリオ理論を使用した、包括的でモジュール化されたポートフォリオ管理システムです。ポートフォリオの評価、最適化、分析をサポートします。

> 📘 **English Documentation** | [README_NEW.md](README_NEW.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## ⚠️ 重要：新しいモジュール構造

このプロジェクトは、スケーラビリティとメンテナンス性の向上のため、モジュール構造にリファクタリングされました。詳細は[ARCHITECTURE_JP.md](ARCHITECTURE_JP.md)を、移行手順は[MIGRATION_GUIDE_JP.md](MIGRATION_GUIDE_JP.md)をご覧ください。

## 🌟 主な機能

- **ポートフォリオ評価**：複数のポートフォリオ（米国株、日本株）を追跡
- **リアルタイムデータ**：Yahoo Financeから最新の株価と指標を取得
- **スマートキャッシング**：TTLベースのキャッシングでAPI呼び出しを削減
- **リスク分析**：ボラティリティ、シャープレシオ、相関関係を計算
- **ポートフォリオ最適化**：モダンポートフォリオ理論に基づく最適化
- **シナリオ分析**：ストレステストとクラッシュシナリオモデリング
- **Web UI**：Streamlitベースのインタラクティブダッシュボード
- **モバイル対応**：すべてのデバイスに対応するレスポンシブデザイン

## 📁 プロジェクト構造

```
Finance_portfolio/
├── src/                          # メインソースコード（新規！）
│   ├── core/                     # ビジネスロジック
│   ├── data/                     # データアクセス層
│   ├── analysis/                 # 分析モジュール
│   ├── ui/                       # UIコンポーネント
│   └── utils/                    # ユーティリティ
├── tests/                        # テストファイル
├── data/                         # キャッシュ保存
├── output/                       # 結果出力
├── portfolio.csv                 # 米国ポートフォリオ入力
├── portfolio_jp.csv              # 日本ポートフォリオ入力
├── portfolio_app.py              # Streamlit Webアプリ
└── requirements.txt              # 依存関係
```

## 🚀 クイックスタート

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/SenaTaka/Finance_portfolio.git
cd Finance_portfolio

# 依存関係のインストール
pip install -r requirements.txt
```

### 基本的な使い方

```bash
# ポートフォリオ計算（新しいモジュール構造を使用）
python portfolio_calculator_new.py portfolio.csv

# または従来のエントリーポイントを使用（まだ動作します）
python portfolio_calculator.py portfolio.csv

# 強制リフレッシュ（キャッシュを無視）
python portfolio_calculator_new.py portfolio.csv --force-refresh

# Web UIの起動
streamlit run portfolio_app.py
```

## 📊 ポートフォリオ入力形式

以下のようなCSVファイルを作成してください：

```csv
ticker,shares
AAPL,10
GOOGL,5
7203.T,100
```

**注意事項：**
- 日本株の場合は、`.T`サフィックスを追加してください（例：トヨタ：`7203.T`）
- システムは通貨（USD/JPY）を自動的に検出します

## 🏗️ モジュール構造

### コアコンポーネント

1. **データ層**（`src/data/`）
   - `CacheManager`：TTLを使用したスマートキャッシング
   - `StockDataFetcher`：Yahoo Finance統合

2. **コア層**（`src/core/`）
   - `PortfolioCalculator`：メイン計算エンジン

3. **分析層**（`src/analysis/`）
   - `efficient_frontier.py`：モダンポートフォリオ理論
   - `sharpe_optimized.py`：シャープレシオ最適化
   - `crash_scenario_analysis.py`：ストレステスト

4. **UI層**（`src/ui/`）
   - `chart_utils.py`：再利用可能なチャート
   - `data_loader.py`：データロードユーティリティ

5. **ユーティリティ層**（`src/utils/`）
   - `config.py`：設定管理
   - `file_utils.py`：ファイル操作
   - `region_classifier.py`：地理的分類

### メリット

✅ **モジュール化**：理解と変更が容易
✅ **テスト可能**：コンポーネントを個別にテスト可能
✅ **拡張可能**：既存コードを壊さず新機能を追加
✅ **保守しやすい**：明確な関心の分離
✅ **スケーラブル**：大規模開発に対応

## 📈 詳細機能

### ポートフォリオ評価

- Yahoo Finance経由のリアルタイム株価
- 複数通貨対応（USD、JPY）
- 為替レート変換
- 配分比率計算

### リスク指標

- **ボラティリティ（σ）**：年率換算標準偏差
- **シャープレシオ**：リスク調整後リターン指標
- **相関マトリックス**：株価相関分析
- **ベータ**：市場感応度（シナリオ分析）

### ポートフォリオ最適化

- **効率的フロンティア**：リスク・リターンのトレードオフを可視化
- **最大シャープポートフォリオ**：最適なリスク調整後配分
- **最小ボラティリティポートフォリオ**：最低リスク配分
- **バックテスティング**：過去のパフォーマンス分析

### Webダッシュボード

- ポートフォリオ配分の可視化（円グラフ）
- セクターと地域分析
- リスク vs リターン散布図
- 相関ヒートマップ
- S&P 500とのパフォーマンス比較
- リバランス推奨
- モバイル最適化インターフェース

### キャッシングシステム

インテリジェントキャッシングでAPI呼び出しを削減：
- **メタデータ**：1週間キャッシュ
- **ボラティリティ/シャープ**：24時間キャッシュ
- **株価**：15分キャッシュ

## 🔧 設定

設定は`src/utils/config.py`に集約されています：

```python
from src.utils import Config

# 設定へのアクセス
print(Config.DATA_DIR)  # "data"
print(Config.CACHE_TTL_PRICE)  # 0.25時間（15分）

# 設定の変更
Config.DEFAULT_RISK_FREE_RATE = 3.5
```

## 📚 API使用例

### 新しい構造の使用

```python
# ポートフォリオ計算
from src.core import PortfolioCalculator

calculator = PortfolioCalculator("portfolio.csv")
calculator.run()

# データ取得
from src.data import StockDataFetcher

fetcher = StockDataFetcher()
price = fetcher.get_stock_price("AAPL")
history = fetcher.get_stock_history("AAPL", period="1y")

# 分析
from src.analysis import calculate_efficient_frontier

frontier_df = calculate_efficient_frontier(
    expected_returns, 
    cov_matrix, 
    n_points=50
)

# UIユーティリティ
from src.ui import chart_utils, DataLoader

loader = DataLoader()
df, files = loader.load_combined_latest()

fig = chart_utils.create_pie_chart(
    data=df,
    values_col="value_jp",
    names_col="ticker",
    title="ポートフォリオ配分"
)
```

## 💻 Web UI（Streamlit）の使い方

### UIの起動

```bash
streamlit run portfolio_app.py
```

### 機能

- **統合ビュー**：デフォルトで`portfolio.csv`（米国株）と`portfolio_jp.csv`（日本株）の最新結果を自動的に結合して、単一のポートフォリオとして表示
- **データ更新**：サイドバーの「Update Data」ボタンをクリックして、`portfolio.csv`と`portfolio_jp.csv`から最新情報を取得・再計算
  - **キャッシング**：通常の更新ではキャッシュを使用してAPI要求を削減
  - **完全リフレッシュオプション**：「Force full refresh」チェックボックスをオンにすると、キャッシュを無視してすべてのデータを取得
- **履歴表示（US/JP History）**：サイドバーで「US History」または「JP History」を選択して、過去の履歴ファイルを個別に表示・選択
- **高度な分析**：
  - **セクター分析**：円グラフでセクター配分を表示
  - **リスク/リターン分析**：ボラティリティ（リスク）とシャープレシオ（効率性）の散布図で株式の特性を比較
  - **相関マトリックス**：株価相関をヒートマップで表示し、分散効果を確認（個別ファイル表示時）
  - **シャープ最適化**：シャープレシオに基づくポートフォリオ最適化とリバランス提案。パラメータ（シャープ/ボラティリティ重視）調整可能
- ポートフォリオ配分比率（円グラフ）とシャープレシオ（棒グラフ）を表示

### 効率的フロンティア（モダンポートフォリオ理論）

モダンポートフォリオ理論（MPT）に基づく効率的フロンティアを表示し、最適なポートフォリオ配分提案を提供します。

#### 機能

- **効率的フロンティア可視化**：ポートフォリオのリスク（ボラティリティ）とリターンの関係をグラフで表示
  - ランダムに生成されたポートフォリオの分布
  - 効率的フロンティア曲線（赤線）
  - 各株式の個別リスク/リターン位置
  
- **最適ポートフォリオ提案**：
  - **最大シャープレシオポートフォリオ**：リスク調整後リターンが最高の配分
  - **最小ボラティリティポートフォリオ**：リスクが最低の配分
  - **均等ウェイトポートフォリオ**：全資産への均等配分
  - **現在のポートフォリオ**：現在の保有に基づく配分

- **リバランス推奨**：現在のポートフォリオから最適ポートフォリオへの移行に必要な具体的な取引量を提供

#### 使用方法

1. 「Update Data」ボタンをクリックしてデータを更新（価格履歴データが必要）
2. 「Efficient Frontier」セクションで各種ポートフォリオ提案を確認
3. 「Required Trades」で最適配分に向けた具体的な取引量を確認

#### 技術詳細

- 1年間の価格データから期待リターンと共分散行列を計算
- `scipy.optimize.minimize`を使用した平均-分散最適化
- リスクフリーレート：米国10年国債利回り（動的取得）

## 🧪 テスト

```bash
# すべてのテストを実行
python test_efficient_frontier.py
python test_cache.py
python test_risk_free_rate.py

# インポートのテスト
python -c "from src.core import PortfolioCalculator; print('✓ OK')"
```

## 📖 ドキュメント

- [ARCHITECTURE_JP.md](ARCHITECTURE_JP.md) - システムアーキテクチャの詳細
- [MIGRATION_GUIDE_JP.md](MIGRATION_GUIDE_JP.md) - 旧構造からの移行
- モジュールのdocstring - 各モジュールのAPIドキュメント

## 🔄 旧構造からの移行

旧構造は後方互換性のためまだサポートされています：

```python
# 旧インポート（まだ動作します）
from portfolio_calculator import PortfolioCalculator
from efficient_frontier import calculate_efficient_frontier

# 新インポート（推奨）
from src.core import PortfolioCalculator
from src.analysis import calculate_efficient_frontier
```

完全な移行手順については、[MIGRATION_GUIDE_JP.md](MIGRATION_GUIDE_JP.md)をご覧ください。

## 🛣️ ロードマップ

### フェーズ1：コアリファクタリング ✅
- [x] モジュール構造
- [x] 関心の分離
- [x] 設定管理
- [x] 後方互換性

### フェーズ2：UIリファクタリング（次回）
- [ ] portfolio_app.pyをページに分割
- [ ] コンポーネントベースUI
- [ ] 状態管理の改善

### フェーズ3：データベース統合
- [ ] JSONキャッシュをデータベースに置き換え
- [ ] 履歴追跡
- [ ] 複数ポートフォリオサポート

### フェーズ4：高度な機能
- [ ] 機械学習予測
- [ ] リアルタイム更新（WebSocket）
- [ ] ニュースとセンチメント分析

### フェーズ5：APIレイヤー
- [ ] REST API
- [ ] 認証
- [ ] レート制限

## 🤝 貢献

貢献する際は：

1. モジュール構造に従う
2. 新機能のテストを追加
3. ドキュメントを更新
4. 後方互換性を維持

## 📄 ライセンス

[ライセンスをここに追加]

## 👥 著者

[著者情報をここに追加]

## 🙏 謝辞

- Yahoo Finance API（yfinance経由）
- モダンポートフォリオ理論の原則
- Streamlitフレームワーク

## 📞 サポート

問題や質問がある場合：
1. [ARCHITECTURE_JP.md](ARCHITECTURE_JP.md)と[MIGRATION_GUIDE_JP.md](MIGRATION_GUIDE_JP.md)を確認
2. モジュールのdocstringを確認
3. GitHubでissueを開く

---

**注意**：このプロジェクトはモジュール構造にリファクタリングされました。すべての旧機能は後方互換性のために残されていますが、新しいコードは改善された構造と拡張性の恩恵を受けます。
