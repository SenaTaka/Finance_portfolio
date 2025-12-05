import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np


def calculate_portfolio(csv_file):
    """
    CSVファイルからティッカーと株数を読み込み、株価とポートフォリオの比率を計算する（日本株対応）
    
    Parameters:
    csv_file: CSVファイルのパス（列：ticker, shares）
    ※日本株は証券コードに .T を付ける（例: 7203.T でトヨタ）
    """
    # CSVファイルを読み込む
    df = pd.read_csv(csv_file)
    
    # 株価、PER、ボラティリティ（シグマ）、シャープレシオを取得
    prices = []
    pers = []
    sigmas = []
    sharpe_ratios = []
    company_names = []
    
    for ticker in df['ticker']:
        try:
            stock = yf.Ticker(ticker)
            
            # 会社名を取得
            info = stock.info
            name = info.get('longName', info.get('shortName', ticker))
            company_names.append(name)
            
            # 株価取得
            hist_1d = stock.history(period='1d')
            if len(hist_1d) > 0:
                price = hist_1d['Close'].iloc[-1]
            else:
                price = 0
            prices.append(price)
            
            # PERを取得
            per = info.get('trailingPE', None)
            # 日本株の場合、forwardPEも試す
            if per is None:
                per = info.get('forwardPE', None)
            pers.append(per)
            
            # ボラティリティ（シグマ）とシャープレシオを計算 - 過去1年のデータから
            hist = stock.history(period='1y')
            if len(hist) > 1:
                returns = hist['Close'].pct_change().dropna()
                # 日次リターンの標準偏差を年率化（252営業日）
                sigma = returns.std() * np.sqrt(252) * 100  # パーセント表示
                sigmas.append(sigma)
                
                # シャープレシオを計算（リスクフリーレート0.5%と仮定 - 日本国債利回り）
                mean_return = returns.mean() * 252 * 100  # 年率リターン（%）
                risk_free_rate = 0.5  # 0.5%
                if sigma > 0:
                    sharpe = (mean_return - risk_free_rate) / sigma
                    sharpe_ratios.append(sharpe)
                else:
                    sharpe_ratios.append(None)
                    sharpe = None
            else:
                sigmas.append(None)
                sharpe_ratios.append(None)
                sigma = None
                sharpe = None
            
            per_str = f"{per:.2f}" if per else "N/A"
            sigma_str = f"{sigma:.2f}%" if sigma else "N/A"
            sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
            
            # 日本円かドルかを判断（.Tで終わる場合は日本株）
            currency = "¥" if ticker.endswith('.T') else "$"
            print(f"{ticker} ({name}): {currency}{price:.2f}, PER: {per_str}, σ: {sigma_str}, Sharpe: {sharpe_str}")
        except Exception as e:
            print(f"{ticker}: エラー - {e}")
            company_names.append(ticker)
            prices.append(0)
            pers.append(None)
            sigmas.append(None)
            sharpe_ratios.append(None)
    
    # 会社名を2列目に挿入
    df.insert(1, 'name', company_names)
    df['price'] = prices
    df['PER'] = pers
    df['sigma'] = sigmas
    df['sharpe'] = sharpe_ratios
    
    # 評価額を計算
    df['value'] = df['shares'] * df['price']
    
    # ポートフォリオ全体の評価額
    total_value = df['value'].sum()
    
    # 比率を計算
    df['ratio'] = (df['value'] / total_value * 100).round(2)
    
    # 比率で降順ソート
    df = df.sort_values('ratio', ascending=False)
    
    # 結果を表示
    print("\n=== ポートフォリオ詳細 ===")
    print(df.to_string(index=False))
    
    # 通貨を判定（日本株とUS株の混在に対応）
    has_jp = df['ticker'].str.endswith('.T').any()
    has_us = (~df['ticker'].str.endswith('.T')).any()
    
    if has_jp and has_us:
        print(f"\n総評価額: ¥/$ {total_value:,.2f} (混在)")
    elif has_jp:
        print(f"\n総評価額: ¥{total_value:,.2f}")
    else:
        print(f"\n総評価額: ${total_value:,.2f}")
    
    # 結果をCSVに保存（日付と時刻を含む）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = csv_file.replace('.csv', f'_result_{timestamp}.csv')
    df.to_csv(output_file, index=False)
    print(f"\n結果を {output_file} に保存しました")
    
    return df


if __name__ == "__main__":
    # 使用例
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "portfolio_jp.csv"
    
    calculate_portfolio(csv_file)
