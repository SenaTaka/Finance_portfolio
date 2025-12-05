import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np


def analyze_crash_scenario(csv_file, crash_scenarios=None):
    """
    ポートフォリオの暴落シナリオ分析
    
    Parameters:
    csv_file: ポートフォリオCSVファイル
    crash_scenarios: 暴落シナリオのリスト（デフォルト: -10%, -20%, -30%, -50%）
    """
    
    if crash_scenarios is None:
        crash_scenarios = [-10, -20, -30, -50]
    
    # CSVファイルを読み込む
    df = pd.read_csv(csv_file)
    
    print("=" * 80)
    print("ポートフォリオ暴落シナリオ分析")
    print("=" * 80)
    
    # 現在の株価と指標を取得
    prices = []
    pers = []
    betas = []
    sigmas = []
    max_drawdowns = []
    company_names = []
    
    for ticker in df['ticker']:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 会社名
            name = info.get('longName', info.get('shortName', ticker))
            company_names.append(name)
            
            # 株価
            hist_1d = stock.history(period='1d')
            if len(hist_1d) > 0:
                price = hist_1d['Close'].iloc[-1]
            else:
                price = 0
            prices.append(price)
            
            # PER
            per = info.get('trailingPE', None)
            if per is None:
                per = info.get('forwardPE', None)
            pers.append(per)
            
            # Beta（市場との相関）
            beta = info.get('beta', None)
            betas.append(beta)
            
            # 過去のデータから最大ドローダウンとボラティリティを計算
            hist = stock.history(period='1y')
            if len(hist) > 1:
                # ボラティリティ
                returns = hist['Close'].pct_change().dropna()
                sigma = returns.std() * np.sqrt(252) * 100
                sigmas.append(sigma)
                
                # 最大ドローダウン（過去1年）
                cummax = hist['Close'].cummax()
                drawdown = (hist['Close'] - cummax) / cummax * 100
                max_dd = drawdown.min()
                max_drawdowns.append(max_dd)
            else:
                sigmas.append(None)
                max_drawdowns.append(None)
            
        except Exception as e:
            print(f"{ticker}: エラー - {e}")
            company_names.append(ticker)
            prices.append(0)
            pers.append(None)
            betas.append(None)
            sigmas.append(None)
            max_drawdowns.append(None)
    
    df['name'] = company_names
    df['price'] = prices
    df['PER'] = pers
    df['beta'] = betas
    df['sigma'] = sigmas
    df['max_drawdown_1y'] = max_drawdowns
    df['value'] = df['shares'] * df['price']
    
    total_value = df['value'].sum()
    df['ratio'] = (df['value'] / total_value * 100).round(2)
    
    # 現在のポートフォリオ
    print(f"\n【現在のポートフォリオ】総額: ¥{total_value:,.0f}" if df['ticker'].iloc[0].endswith('.T') else f"\n【現在のポートフォリオ】総額: ${total_value:,.0f}")
    print(f"{'Ticker':<10} {'Name':<30} {'比率':>6} {'Beta':>6} {'σ':>8} {'過去1年最大DD':>12}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        beta_str = f"{row['beta']:.2f}" if row['beta'] else "N/A"
        sigma_str = f"{row['sigma']:.1f}%" if row['sigma'] else "N/A"
        dd_str = f"{row['max_drawdown_1y']:.1f}%" if row['max_drawdown_1y'] else "N/A"
        name_short = row['name'][:28] if len(row['name']) > 28 else row['name']
        print(f"{row['ticker']:<10} {name_short:<30} {row['ratio']:>5.1f}% {beta_str:>6} {sigma_str:>8} {dd_str:>12}")
    
    # ポートフォリオ全体のBeta加重平均
    df_with_beta = df[df['beta'].notna()].copy()
    if len(df_with_beta) > 0:
        portfolio_beta = (df_with_beta['beta'] * df_with_beta['ratio']).sum() / df_with_beta['ratio'].sum()
    else:
        portfolio_beta = 1.0
    
    print(f"\nポートフォリオ加重平均Beta: {portfolio_beta:.2f}")
    
    # 暴落シナリオ分析
    print(f"\n{'=' * 80}")
    print("【暴落シナリオ分析】")
    print(f"{'=' * 80}\n")
    
    scenarios_results = []
    
    for crash_pct in crash_scenarios:
        print(f"\n■ シナリオ{crash_pct}%: 市場全体が{crash_pct}%下落")
        print("-" * 80)
        
        scenario_values = []
        
        for _, row in df.iterrows():
            beta = row['beta'] if row['beta'] else 1.0  # Betaがない場合は1.0と仮定
            sigma = row['sigma'] if row['sigma'] else 30.0  # σがない場合は30%と仮定
            
            # Beta基準の予想下落率
            expected_drop = crash_pct * beta
            
            # ボラティリティによる変動幅を加える（±1σ）
            # 悲観シナリオ: 期待下落率 - 0.5σ（さらに下がる可能性）
            pessimistic_drop = expected_drop - (sigma * 0.5 / np.sqrt(252) * 100)
            
            # 新価格を計算（悲観シナリオ）
            new_price = row['price'] * (1 + pessimistic_drop / 100)
            new_value = new_price * row['shares']
            scenario_values.append(new_value)
            
            print(f"{row['ticker']:<10} Beta={beta:.2f} → 予想下落 {expected_drop:+.1f}% (悲観 {pessimistic_drop:+.1f}%) | "
                  f"¥{row['value']:>12,.0f} → ¥{new_value:>12,.0f} ({new_value - row['value']:+,.0f})" 
                  if row['ticker'].endswith('.T') else 
                  f"{row['ticker']:<10} Beta={beta:.2f} → 予想下落 {expected_drop:+.1f}% (悲観 {pessimistic_drop:+.1f}%) | "
                  f"${row['value']:>12,.0f} → ${new_value:>12,.0f} ({new_value - row['value']:+,.0f})")
        
        total_new_value = sum(scenario_values)
        total_loss = total_new_value - total_value
        loss_pct = (total_loss / total_value * 100)
        
        print(f"\nポートフォリオ総額: ¥{total_value:,.0f} → ¥{total_new_value:,.0f}" if df['ticker'].iloc[0].endswith('.T') 
              else f"\nポートフォリオ総額: ${total_value:,.0f} → ${total_new_value:,.0f}")
        print(f"損失: {total_loss:+,.0f} ({loss_pct:+.2f}%)")
        
        scenarios_results.append({
            'scenario': f"{crash_pct}%",
            'market_drop': crash_pct,
            'portfolio_drop': loss_pct,
            'loss_amount': total_loss,
            'new_value': total_new_value
        })
    
    # サマリー表示
    print(f"\n{'=' * 80}")
    print("【シナリオサマリー】")
    print(f"{'=' * 80}")
    print(f"{'市場下落':>10} {'ポートフォリオ下落':>18} {'損失額':>18} {'残存価値':>18}")
    print("-" * 80)
    
    for s in scenarios_results:
        currency = "¥" if df['ticker'].iloc[0].endswith('.T') else "$"
        print(f"{s['scenario']:>10} {s['portfolio_drop']:>16.2f}% {currency}{s['loss_amount']:>16,.0f} {currency}{s['new_value']:>16,.0f}")
    
    # 結果をCSVに保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = csv_file.replace('.csv', f'_crash_analysis_{timestamp}.csv')
    
    summary_df = pd.DataFrame(scenarios_results)
    summary_df.to_csv(output_file, index=False)
    print(f"\n分析結果を {output_file} に保存しました")
    
    # リスク軽減の提案
    print(f"\n{'=' * 80}")
    print("【リスク軽減の提案】")
    print(f"{'=' * 80}")
    
    # 高Beta銘柄を特定
    high_beta = df[df['beta'] > 1.5].sort_values('ratio', ascending=False)
    if len(high_beta) > 0:
        print("\n⚠ 高Beta銘柄（Beta > 1.5）:")
        for _, row in high_beta.iterrows():
            print(f"  - {row['ticker']} ({row['name'][:30]}): Beta={row['beta']:.2f}, 比率={row['ratio']:.1f}%")
        print("  → 暴落時の下落が大きい可能性。比率を下げることを検討")
    
    # 集中度が高い銘柄
    concentrated = df[df['ratio'] > 30].sort_values('ratio', ascending=False)
    if len(concentrated) > 0:
        print("\n⚠ 集中度が高い銘柄（比率 > 30%）:")
        for _, row in concentrated.iterrows():
            print(f"  - {row['ticker']} ({row['name'][:30]}): {row['ratio']:.1f}%")
        print("  → 分散投資でリスクを軽減")
    
    # 防衛的な提案
    print("\n✓ 防衛的戦略の提案:")
    print("  1. 現金比率を10-20%確保（暴落時の買い増し資金）")
    print("  2. 低Beta銘柄（Beta < 0.8）や債券ETFを組み入れる")
    print("  3. ゴールド（GLDM等）やディフェンシブセクター（生活必需品、公共事業）を追加")
    print("  4. プットオプションやインバースETFでヘッジ（上級者向け）")
    print("  5. 高Beta・高比率の銘柄は段階的に利確を検討")
    
    return df, scenarios_results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "portfolio.csv"
    
    analyze_crash_scenario(csv_file)
