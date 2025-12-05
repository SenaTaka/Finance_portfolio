import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np
import sys
import os
import requests
from bs4 import BeautifulSoup
import re

class PortfolioCalculator:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.usd_jpy = 1.0
        
    def get_exchange_rate(self):
        """USD/JPYレートを取得"""
        try:
            ticker = "JPY=X"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                self.usd_jpy = hist['Close'].iloc[-1]
                print(f"現在のUSD/JPYレート: {self.usd_jpy:.2f}円")
            else:
                print("為替データの取得に失敗しました。1ドル=100円として計算します。")
                self.usd_jpy = 100.0
        except Exception as e:
            print(f"為替レート取得エラー: {e}")
            self.usd_jpy = 100.0

    def get_japanese_name(self, ticker):
        """Yahoo!ファイナンス(日本)から日本語社名を取得"""
        try:
            url = f"https://finance.yahoo.co.jp/quote/{ticker}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.text
                # "トヨタ自動車(株)【7203】..." から社名を抽出
                match = re.search(r'^(.*?)【', title)
                if match:
                    return match.group(1).strip()
        except Exception:
            pass
        return None

    def get_ticker_data(self, ticker):
        """個別銘柄のデータを取得"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1y')
            
            if hist.empty:
                return None
                
            current_price = hist['Close'].iloc[-1]
            
            # PER
            info = stock.info
            per = info.get('trailingPE', None)
            currency = info.get('currency', 'USD')
            
            # 社名取得
            name = None
            # 日本株(.T)の場合は日本語名取得を試みる
            if ticker.endswith('.T'):
                name = self.get_japanese_name(ticker)
            
            # 取得できなかった場合、または日本株以外はyfinanceの情報を使用
            if not name:
                name = info.get('longName') or info.get('shortName') or ticker
            
            # Volatility & Sharpe
            sigma = None
            sharpe = None
            
            if len(hist) > 1:
                returns = hist['Close'].pct_change().dropna()
                sigma = returns.std() * np.sqrt(252) * 100
                
                mean_return = returns.mean() * 252 * 100
                risk_free_rate = 4.0
                if sigma > 0:
                sharpe = (mean_return - risk_free_rate) / sigma

            return {
                'price': current_price,
                'PER': per,
                'sigma': sigma,
                'sharpe': sharpe,
                'currency': currency,
                'name': name,
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'country': info.get('country'),
            }
        except Exception as e:
            print(f"{ticker}: データ取得エラー - {e}")
            return None

    def run(self):
        if not os.path.exists(self.csv_file):
            print(f"エラー: ファイル {self.csv_file} が見つかりません。")
            return

        print(f"ポートフォリオ計算を開始します: {self.csv_file}")
        df = pd.read_csv(self.csv_file)
        
        # 為替レート取得
        self.get_exchange_rate()
        
        results = []
        for index, row in df.iterrows():
            ticker = row['ticker']
            shares = row['shares']
            
            print(f"データ取得中: {ticker}...")
            data = self.get_ticker_data(ticker)
            
            if data:
                data['ticker'] = ticker
                data['shares'] = shares
                
                # 通貨に応じた計算
                price = data['price']
                currency = data.get('currency', 'USD')
                
                if currency == 'JPY':
                    # 日本円の場合
                    val_jp = price * shares
                    val_usd = val_jp / self.usd_jpy if self.usd_jpy > 0 else 0
                else:
                    # 米ドル（またはその他）の場合、とりあえずUSD扱いとして計算
                    # 必要なら他の通貨対応もここに追加
                    val_usd = price * shares
                    val_jp = val_usd * self.usd_jpy
                
                data['value'] = val_usd
                data['value_jp'] = int(val_jp)
                results.append(data)
            else:
                # エラー時の空データ
                results.append({
                    'ticker': ticker, 'shares': shares, 
                    'price': 0, 'PER': None, 'sigma': None, 'sharpe': None, 
                    'value': 0, 'value_jp': 0, 'currency': 'N/A', 'name': 'N/A'
                })

        result_df = pd.DataFrame(results)
        
        # 比率計算
        total_value = result_df['value'].sum()
        if total_value > 0:
            result_df['ratio'] = (result_df['value'] / total_value * 100).round(2)
        else:
            result_df['ratio'] = 0

        # ソート
        result_df = result_df.sort_values('ratio', ascending=False)
        
        # 表示
        pd.options.display.float_format = '{:.2f}'.format
        print("\n=== ポートフォリオ詳細 ===")
        # 表示用カラム選択
        display_cols = ['ticker', 'name', 'shares', 'price', 'value', 'value_jp', 'ratio', 'PER', 'sharpe']
        # 存在しないカラムは除外（念のため）
        display_cols = [c for c in display_cols if c in result_df.columns]
        print(result_df[display_cols].to_string(index=False))
        
        total_value_jp = result_df['value_jp'].sum()
        print(f"\n総評価額 (USD): ${total_value:,.2f}")
        print(f"総評価額 (JPY): ¥{total_value_jp:,.0f}")
        print(f"適用為替レート: 1ドル = {self.usd_jpy:.2f}円")

        # 保存
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.basename(self.csv_file)
        output_file = os.path.join(output_dir, base_name.replace('.csv', f'_result_{timestamp}.csv'))
        
        # メタデータとして為替レートも保存
        result_df['usd_jpy_rate'] = self.usd_jpy
        
        # カラム順序を整える
        cols = [
            'ticker', 'name', 'shares', 'currency', 'price', 'value', 'value_jp', 'ratio',
            'PER', 'sigma', 'sharpe', 'sector', 'industry', 'country', 'usd_jpy_rate'
        ]
        # 実際に存在するカラムのみ
        cols = [c for c in cols if c in result_df.columns]
        
        result_df[cols].to_csv(output_file, index=False)
        print(f"\n結果を {output_file} に保存しました")

if __name__ == "__main__":
    target_file = "portfolio.csv"
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    
    calculator = PortfolioCalculator(target_file)
    calculator.run()
