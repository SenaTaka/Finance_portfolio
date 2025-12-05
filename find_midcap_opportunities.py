import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time


def get_midcap_opportunities(min_rank=500, max_rank=2000, min_sharpe=0, max_per=3000):
    """
    時価総額ランキング500-2000位の銘柄から投資機会を探す
    
    Parameters:
    min_rank: 最小ランク（デフォルト500）
    max_rank: 最大ランク（デフォルト2000）
    min_sharpe: 最小シャープレシオ（デフォルト1.0）
    max_per: 最大PER（デフォルト30）
    """
    
    print("ミッドキャップ銘柄を取得中...")
    
    # Russell 2000（小型株指数）のETFから銘柄を取得
    # または、S&P MidCap 400のETFを使用
    etfs = ['IJH', 'MDY', 'VO']  # iShares S&P MidCap, SPDR MidCap, Vanguard MidCap
    
    all_tickers = []
    for etf_ticker in etfs:
        try:
            etf = yf.Ticker(etf_ticker)
            # ETFの保有銘柄を取得（yfinanceの制限により直接取得できない場合がある）
            print(f"{etf_ticker} から銘柄を取得中...")
        except Exception as e:
            print(f"{etf_ticker} のエラー: {e}")
    
    # 代替アプローチ: 手動で選定したミッドキャップ銘柄リスト
    # 時価総額500-2000位の代表的な銘柄（2024年現在の推定）
    candidate_tickers = [
        # テクノロジー・ソフトウェア
        'BILL', 'PATH', 'FROG', 'CPNG', 'GTLB', 'KVUE', 
        # ヘルスケア・バイオ
        'EXAS', 'HOLX', 'TECH', 'PODD', 'INCY',
        # 金融
        'ALLY', 'SYF', 'NYCB', 'WAL', 'EWBC',
        # 消費財
        'CHEF', 'WING', 'TXRH', 'CBRL', 'PLAY',
        # 工業・製造
        'BLDR', 'BECN', 'UFPI', 'MLI', 'TREX',
        # エネルギー・素材
        'AR', 'SM', 'CTRA', 'OVV', 'PR',
        # 不動産
        'REXR', 'FR', 'STAG', 'NSA', 'CUBE',
        # 通信・メディア
        'CABO', 'TRIP', 'MSGS', 'IMAX', 'FUBO',
        # 小売
        'FIVE', 'OLLI', 'BBWI', 'ANF', 'URBN',
        # その他有望株
        'RKLB', 'IONQ', 'PLTR', 'SOFI', 'UPST', 'COIN'
    ]
    
    print(f"\n{len(candidate_tickers)} 銘柄を分析中...\n")
    
    results = []
    
    for ticker in candidate_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 時価総額を取得
            market_cap = info.get('marketCap', 0)
            if market_cap == 0:
                continue
            
            # 株価取得
            hist_1d = stock.history(period='1d')
            if len(hist_1d) == 0:
                continue
            price = hist_1d['Close'].iloc[-1]
            
            # 会社名
            name = info.get('longName', info.get('shortName', ticker))
            
            # ウェブサイト
            website = info.get('website', '')
            
            # PER
            per = info.get('trailingPE', None)
            
            # ボラティリティとシャープレシオを計算
            hist = stock.history(period='1y')
            if len(hist) < 100:  # データが少なすぎる場合はスキップ
                continue
            
            returns = hist['Close'].pct_change().dropna()
            sigma = returns.std() * np.sqrt(252) * 100
            mean_return = returns.mean() * 252 * 100
            risk_free_rate = 4.0
            
            if sigma > 0:
                sharpe = (mean_return - risk_free_rate) / sigma
            else:
                sharpe = None
            
            # フィルタリング条件
            if sharpe and sharpe >= min_sharpe:
                if per is None or (per > 0 and per <= max_per):
                    results.append({
                        'ticker': ticker,
                        'name': name,
                        'price': price,
                        'market_cap': market_cap,
                        'PER': per,
                        'sigma': sigma,
                        'sharpe': sharpe,
                        'annual_return': mean_return,
                        'website': website
                    })
                    per_display = f"{per:.2f}" if per else 'N/A'
                    print(f"✓ {ticker} ({name[:30]}): ${price:.2f}, Cap: ${market_cap/1e9:.2f}B, PER: {per_display}, Sharpe: {sharpe:.2f}")
            
            time.sleep(0.1)  # API制限対策
            
        except Exception as e:
            print(f"✗ {ticker}: エラー - {e}")
            continue
    
    if not results:
        print("\n条件に合う銘柄が見つかりませんでした")
        return None
    
    # DataFrameに変換
    df = pd.DataFrame(results)
    df = df.sort_values('sharpe', ascending=False)
    
    print(f"\n\n=== 投資機会候補 (Sharpe >= {min_sharpe}, PER <= {max_per}) ===")
    print(df.to_string(index=False))
    
    # CSVに保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'midcap_opportunities_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n結果を {output_file} に保存しました")
    
    return df


if __name__ == "__main__":
    import sys
    
    # コマンドライン引数で条件を指定可能
    min_sharpe = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    max_per = float(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"検索条件: シャープレシオ >= {min_sharpe}, PER <= {max_per}\n")
    
    df = get_midcap_opportunities(min_sharpe=min_sharpe, max_per=max_per)
