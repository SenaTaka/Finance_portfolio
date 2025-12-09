import pandas as pd
import numpy as np

def calculate_sharpe_scores(df, a=1.0, b=1.0):
    """
    Calculate scores based on Sharpe Ratio and Volatility.
    score = (Sharpe^a) / (Sigma^b)
    If Sharpe <= 0, score is 0.
    """
    scores = {}
    for _, row in df.iterrows():
        ticker = row['ticker']
        sharpe = row.get('sharpe')
        sigma = row.get('sigma')
        
        if pd.isna(sharpe) or pd.isna(sigma) or sharpe <= 0:
            scores[ticker] = 0.0
        else:
            if sigma <= 0:
                scores[ticker] = 0.0
            else:
                try:
                    scores[ticker] = (sharpe ** a) / (sigma ** b)
                except Exception:
                    scores[ticker] = 0.0
    return scores

def calculate_target_weights(scores):
    """
    Calculate target weights from scores.
    w_i = score_i / sum(scores)
    """
    total_score = sum(scores.values())
    weights = {}
    if total_score == 0:
        # If all scores are 0, return equal weights
        n = len(scores)
        if n > 0:
            return {t: 1.0/n for t in scores}
        return {}
        
    for ticker, score in scores.items():
        weights[ticker] = score / total_score
    return weights

def calculate_trade_plan(df, target_weights, total_value_jp, usd_jpy_rate):
    """
    Calculate trade plan.
    """
    trades = []
    
    for _, row in df.iterrows():
        ticker = row['ticker']
        current_val_jp = row.get('value_jp', 0)
        price = row.get('price', 0)
        currency = row.get('currency', 'USD')
        
        target_weight = target_weights.get(ticker, 0.0)
        target_val_jp = total_value_jp * target_weight
        
        diff_val_jp = target_val_jp - current_val_jp
        
        # Calculate price in JPY
        if currency == 'JPY' or ticker.endswith('.T'):
            price_jp = price
        else:
            price_jp = price * usd_jpy_rate
            
        if price_jp > 0:
            diff_shares = diff_val_jp / price_jp
        else:
            diff_shares = 0
            
        trades.append({
            'ticker': ticker,
            'name': row.get('name', ticker),
            'current_weight': row.get('ratio', 0), # ratio is in %
            'target_weight': target_weight * 100.0, # Convert to %
            'current_value_jp': current_val_jp,
            'target_value_jp': target_val_jp,
            'diff_value_jp': diff_val_jp,
            'diff_shares': diff_shares,
            'price_jp': price_jp
        })
        
    return pd.DataFrame(trades)
