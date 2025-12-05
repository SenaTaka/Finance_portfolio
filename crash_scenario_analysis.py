import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np


def analyze_crash_scenario(csv_file, crash_scenarios=None):
    """
    Portfolio crash scenario analysis
    
    Parameters:
    csv_file: Portfolio CSV file
    crash_scenarios: List of crash scenarios (default: -10%, -20%, -30%, -50%)
    """
    
    if crash_scenarios is None:
        crash_scenarios = [-10, -20, -30, -50]
    
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    print("=" * 80)
    print("Portfolio Crash Scenario Analysis")
    print("=" * 80)
    
    # Get current stock prices and metrics
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
            
            # Company name
            name = info.get('longName', info.get('shortName', ticker))
            company_names.append(name)
            
            # Stock price
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
            
            # Beta (market correlation)
            beta = info.get('beta', None)
            betas.append(beta)
            
            # Calculate max drawdown and volatility from historical data
            hist = stock.history(period='1y')
            if len(hist) > 1:
                # Volatility
                returns = hist['Close'].pct_change().dropna()
                sigma = returns.std() * np.sqrt(252) * 100
                sigmas.append(sigma)
                
                # Max drawdown (past 1 year)
                cummax = hist['Close'].cummax()
                drawdown = (hist['Close'] - cummax) / cummax * 100
                max_dd = drawdown.min()
                max_drawdowns.append(max_dd)
            else:
                sigmas.append(None)
                max_drawdowns.append(None)
            
        except Exception as e:
            print(f"{ticker}: Error - {e}")
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
    
    # Current portfolio
    print(f"\n[Current Portfolio] Total: ¥{total_value:,.0f}" if df['ticker'].iloc[0].endswith('.T') else f"\n[Current Portfolio] Total: ${total_value:,.0f}")
    print(f"{'Ticker':<10} {'Name':<30} {'Ratio':>6} {'Beta':>6} {'σ':>8} {'1Y Max DD':>12}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        beta_str = f"{row['beta']:.2f}" if row['beta'] else "N/A"
        sigma_str = f"{row['sigma']:.1f}%" if row['sigma'] else "N/A"
        dd_str = f"{row['max_drawdown_1y']:.1f}%" if row['max_drawdown_1y'] else "N/A"
        name_short = row['name'][:28] if len(row['name']) > 28 else row['name']
        print(f"{row['ticker']:<10} {name_short:<30} {row['ratio']:>5.1f}% {beta_str:>6} {sigma_str:>8} {dd_str:>12}")
    
    # Portfolio weighted average Beta
    df_with_beta = df[df['beta'].notna()].copy()
    if len(df_with_beta) > 0:
        portfolio_beta = (df_with_beta['beta'] * df_with_beta['ratio']).sum() / df_with_beta['ratio'].sum()
    else:
        portfolio_beta = 1.0
    
    print(f"\nPortfolio Weighted Average Beta: {portfolio_beta:.2f}")
    
    # Crash scenario analysis
    print(f"\n{'=' * 80}")
    print("[Crash Scenario Analysis]")
    print(f"{'=' * 80}\n")
    
    scenarios_results = []
    
    for crash_pct in crash_scenarios:
        print(f"\n■ Scenario {crash_pct}%: Market drops {crash_pct}%")
        print("-" * 80)
        
        scenario_values = []
        
        for _, row in df.iterrows():
            beta = row['beta'] if row['beta'] else 1.0  # Assume 1.0 if no Beta
            sigma = row['sigma'] if row['sigma'] else 30.0  # Assume 30% if no σ
            
            # Expected drop based on Beta
            expected_drop = crash_pct * beta
            
            # Add volatility variation (±1σ)
            # Pessimistic scenario: expected drop - 0.5σ (potential for further decline)
            pessimistic_drop = expected_drop - (sigma * 0.5 / np.sqrt(252) * 100)
            
            # Calculate new price (pessimistic scenario)
            new_price = row['price'] * (1 + pessimistic_drop / 100)
            new_value = new_price * row['shares']
            scenario_values.append(new_value)
            
            print(f"{row['ticker']:<10} Beta={beta:.2f} → Expected drop {expected_drop:+.1f}% (Pessimistic {pessimistic_drop:+.1f}%) | "
                  f"¥{row['value']:>12,.0f} → ¥{new_value:>12,.0f} ({new_value - row['value']:+,.0f})" 
                  if row['ticker'].endswith('.T') else 
                  f"{row['ticker']:<10} Beta={beta:.2f} → Expected drop {expected_drop:+.1f}% (Pessimistic {pessimistic_drop:+.1f}%) | "
                  f"${row['value']:>12,.0f} → ${new_value:>12,.0f} ({new_value - row['value']:+,.0f})")
        
        total_new_value = sum(scenario_values)
        total_loss = total_new_value - total_value
        loss_pct = (total_loss / total_value * 100)
        
        print(f"\nPortfolio Total: ¥{total_value:,.0f} → ¥{total_new_value:,.0f}" if df['ticker'].iloc[0].endswith('.T') 
              else f"\nPortfolio Total: ${total_value:,.0f} → ${total_new_value:,.0f}")
        print(f"Loss: {total_loss:+,.0f} ({loss_pct:+.2f}%)")
        
        scenarios_results.append({
            'scenario': f"{crash_pct}%",
            'market_drop': crash_pct,
            'portfolio_drop': loss_pct,
            'loss_amount': total_loss,
            'new_value': total_new_value
        })
    
    # Summary display
    print(f"\n{'=' * 80}")
    print("[Scenario Summary]")
    print(f"{'=' * 80}")
    print(f"{'Market Drop':>10} {'Portfolio Drop':>18} {'Loss Amount':>18} {'Remaining Value':>18}")
    print("-" * 80)
    
    for s in scenarios_results:
        currency = "¥" if df['ticker'].iloc[0].endswith('.T') else "$"
        print(f"{s['scenario']:>10} {s['portfolio_drop']:>16.2f}% {currency}{s['loss_amount']:>16,.0f} {currency}{s['new_value']:>16,.0f}")
    
    # Save results to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = csv_file.replace('.csv', f'_crash_analysis_{timestamp}.csv')
    
    summary_df = pd.DataFrame(scenarios_results)
    summary_df.to_csv(output_file, index=False)
    print(f"\nAnalysis results saved to {output_file}")
    
    # Risk mitigation suggestions
    print(f"\n{'=' * 80}")
    print("[Risk Mitigation Suggestions]")
    print(f"{'=' * 80}")
    
    # Identify high Beta stocks
    high_beta = df[df['beta'] > 1.5].sort_values('ratio', ascending=False)
    if len(high_beta) > 0:
        print("\n⚠ High Beta Stocks (Beta > 1.5):")
        for _, row in high_beta.iterrows():
            print(f"  - {row['ticker']} ({row['name'][:30]}): Beta={row['beta']:.2f}, Ratio={row['ratio']:.1f}%")
        print("  → May experience larger declines during crashes. Consider reducing allocation.")
    
    # Highly concentrated stocks
    concentrated = df[df['ratio'] > 30].sort_values('ratio', ascending=False)
    if len(concentrated) > 0:
        print("\n⚠ Highly Concentrated Stocks (Ratio > 30%):")
        for _, row in concentrated.iterrows():
            print(f"  - {row['ticker']} ({row['name'][:30]}): {row['ratio']:.1f}%")
        print("  → Reduce risk through diversification")
    
    # Defensive suggestions
    print("\n✓ Defensive Strategy Suggestions:")
    print("  1. Maintain 10-20% cash allocation (funds for buying during crashes)")
    print("  2. Include low Beta stocks (Beta < 0.8) or bond ETFs")
    print("  3. Add gold (e.g., GLDM) or defensive sectors (consumer staples, utilities)")
    print("  4. Hedge with put options or inverse ETFs (advanced)")
    print("  5. Consider gradually taking profits on high Beta, high allocation stocks")
    
    return df, scenarios_results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "portfolio.csv"
    
    analyze_crash_scenario(csv_file)
