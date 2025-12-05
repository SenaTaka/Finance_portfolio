"""
Efficient Frontier Module for Modern Portfolio Theory

This module calculates the efficient frontier and provides portfolio optimization
suggestions based on Modern Portfolio Theory (MPT).
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, Iterable, Union


def calculate_portfolio_metrics(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.04
) -> dict:
    """
    Calculate portfolio return, volatility, and Sharpe ratio.
    
    Args:
        weights: Array of portfolio weights
        expected_returns: Array of expected returns for each asset
        cov_matrix: Covariance matrix of asset returns
        risk_free_rate: Risk-free rate (default 4%)
        
    Returns:
        Dictionary with portfolio metrics
    """
    portfolio_return = np.sum(expected_returns * weights)
    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    # Return 0 for Sharpe ratio when volatility is zero (edge case with single risk-free asset)
    # This avoids division by zero while indicating no risk-adjusted return advantage
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
    
    return {
        'return': portfolio_return,
        'volatility': portfolio_volatility,
        'sharpe': sharpe_ratio
    }


def _negative_sharpe_ratio(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float
) -> float:
    """Calculate negative Sharpe ratio for minimization."""
    metrics = calculate_portfolio_metrics(weights, expected_returns, cov_matrix, risk_free_rate)
    return -metrics['sharpe']


def _portfolio_volatility(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray
) -> float:
    """Calculate portfolio volatility."""
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))


def find_optimal_portfolio(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.04,
    allow_short: bool = False
) -> dict:
    """
    Find the portfolio with maximum Sharpe ratio (tangency portfolio).
    
    Args:
        expected_returns: Array of expected returns for each asset
        cov_matrix: Covariance matrix of asset returns
        risk_free_rate: Risk-free rate (default 4%)
        allow_short: Allow short selling (default False)
        
    Returns:
        Dictionary with optimal weights and portfolio metrics
    """
    n_assets = len(expected_returns)
    init_weights = np.array([1.0 / n_assets] * n_assets)
    
    # Constraints: weights sum to 1
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
    
    # Bounds: no short selling unless allowed
    if allow_short:
        bounds = tuple((-1.0, 1.0) for _ in range(n_assets))
    else:
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))
    
    result = minimize(
        _negative_sharpe_ratio,
        init_weights,
        args=(expected_returns, cov_matrix, risk_free_rate),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000}
    )
    
    optimal_weights = result.x
    metrics = calculate_portfolio_metrics(optimal_weights, expected_returns, cov_matrix, risk_free_rate)
    
    return {
        'weights': optimal_weights,
        'return': metrics['return'],
        'volatility': metrics['volatility'],
        'sharpe': metrics['sharpe'],
        'success': result.success
    }


def find_min_volatility_portfolio(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    allow_short: bool = False
) -> dict:
    """
    Find the minimum volatility portfolio.
    
    Args:
        expected_returns: Array of expected returns for each asset
        cov_matrix: Covariance matrix of asset returns
        allow_short: Allow short selling (default False)
        
    Returns:
        Dictionary with optimal weights and portfolio metrics
    """
    n_assets = len(expected_returns)
    init_weights = np.array([1.0 / n_assets] * n_assets)
    
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
    
    if allow_short:
        bounds = tuple((-1.0, 1.0) for _ in range(n_assets))
    else:
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))
    
    result = minimize(
        _portfolio_volatility,
        init_weights,
        args=(expected_returns, cov_matrix),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000}
    )
    
    optimal_weights = result.x
    metrics = calculate_portfolio_metrics(optimal_weights, expected_returns, cov_matrix)
    
    return {
        'weights': optimal_weights,
        'return': metrics['return'],
        'volatility': metrics['volatility'],
        'sharpe': metrics['sharpe'],
        'success': result.success
    }


def calculate_efficient_frontier(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    n_points: int = 50,
    risk_free_rate: float = 0.04,
    allow_short: bool = False
) -> pd.DataFrame:
    """
    Calculate the efficient frontier.
    
    Args:
        expected_returns: Array of expected returns for each asset
        cov_matrix: Covariance matrix of asset returns
        n_points: Number of points on the frontier
        risk_free_rate: Risk-free rate (default 4%)
        allow_short: Allow short selling (default False)
        
    Returns:
        DataFrame with efficient frontier points (volatility, return, sharpe, weights)
    """
    n_assets = len(expected_returns)
    
    # Find the range of possible returns
    if allow_short:
        min_return = min(expected_returns) * 0.5
        max_return = max(expected_returns) * 1.5
    else:
        min_return = min(expected_returns)
        max_return = max(expected_returns)
    
    target_returns = np.linspace(min_return, max_return, n_points)
    
    frontier_volatilities = []
    frontier_returns = []
    frontier_sharpes = []
    frontier_weights = []
    
    for target_return in target_returns:
        try:
            init_weights = np.array([1.0 / n_assets] * n_assets)
            
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
                {'type': 'eq', 'fun': lambda w, tr=target_return: np.sum(expected_returns * w) - tr}
            ]
            
            if allow_short:
                bounds = tuple((-1.0, 1.0) for _ in range(n_assets))
            else:
                bounds = tuple((0.0, 1.0) for _ in range(n_assets))
            
            result = minimize(
                _portfolio_volatility,
                init_weights,
                args=(expected_returns, cov_matrix),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if result.success:
                vol = _portfolio_volatility(result.x, expected_returns, cov_matrix)
                sharpe = (target_return - risk_free_rate) / vol if vol > 0 else 0
                
                frontier_volatilities.append(vol)
                frontier_returns.append(target_return)
                frontier_sharpes.append(sharpe)
                frontier_weights.append(result.x.tolist())
        except Exception:
            continue
    
    if not frontier_volatilities:
        return pd.DataFrame()
    
    return pd.DataFrame({
        'volatility': frontier_volatilities,
        'return': frontier_returns,
        'sharpe': frontier_sharpes,
        'weights': frontier_weights
    })


def generate_random_portfolios(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    n_portfolios: int = 1000,
    risk_free_rate: float = 0.04
) -> pd.DataFrame:
    """
    Generate random portfolios for visualization.
    
    Args:
        expected_returns: Array of expected returns for each asset
        cov_matrix: Covariance matrix of asset returns
        n_portfolios: Number of random portfolios to generate
        risk_free_rate: Risk-free rate (default 4%)
        
    Returns:
        DataFrame with random portfolio metrics
    """
    n_assets = len(expected_returns)
    
    returns_list = []
    volatilities_list = []
    sharpes_list = []
    weights_list = []
    
    for _ in range(n_portfolios):
        weights = np.random.random(n_assets)
        weights = weights / np.sum(weights)
        
        metrics = calculate_portfolio_metrics(weights, expected_returns, cov_matrix, risk_free_rate)
        
        returns_list.append(metrics['return'])
        volatilities_list.append(metrics['volatility'])
        sharpes_list.append(metrics['sharpe'])
        weights_list.append(weights.tolist())
    
    return pd.DataFrame({
        'volatility': volatilities_list,
        'return': returns_list,
        'sharpe': sharpes_list,
        'weights': weights_list
    })


def get_portfolio_suggestions(
    tickers: list,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    current_weights: np.ndarray = None,
    risk_free_rate: float = 0.04
) -> dict:
    """
    Generate portfolio suggestions based on Modern Portfolio Theory.
    
    Args:
        tickers: List of ticker symbols
        expected_returns: Array of expected returns for each asset
        cov_matrix: Covariance matrix of asset returns
        current_weights: Current portfolio weights (optional)
        risk_free_rate: Risk-free rate (default 4%)
        
    Returns:
        Dictionary with various portfolio suggestions
    """
    suggestions = {}
    
    # 1. Maximum Sharpe Ratio Portfolio
    max_sharpe = find_optimal_portfolio(
        expected_returns, cov_matrix, risk_free_rate, allow_short=False
    )
    suggestions['max_sharpe'] = {
        'name': 'Maximum Sharpe Ratio Portfolio',
        'name_jp': '最大シャープレシオ・ポートフォリオ',
        'description': 'Portfolio with the highest risk-adjusted return',
        'description_jp': 'リスク調整済みリターンが最も高いポートフォリオ',
        'weights': dict(zip(tickers, max_sharpe['weights'])),
        'expected_return': max_sharpe['return'] * 100,
        'volatility': max_sharpe['volatility'] * 100,
        'sharpe': max_sharpe['sharpe']
    }
    
    # 2. Minimum Volatility Portfolio
    min_vol = find_min_volatility_portfolio(expected_returns, cov_matrix, allow_short=False)
    suggestions['min_volatility'] = {
        'name': 'Minimum Volatility Portfolio',
        'name_jp': '最小ボラティリティ・ポートフォリオ',
        'description': 'Portfolio with the lowest risk',
        'description_jp': 'リスクが最も低いポートフォリオ',
        'weights': dict(zip(tickers, min_vol['weights'])),
        'expected_return': min_vol['return'] * 100,
        'volatility': min_vol['volatility'] * 100,
        'sharpe': min_vol['sharpe']
    }
    
    # 3. Calculate current portfolio metrics if provided
    if current_weights is not None:
        current_metrics = calculate_portfolio_metrics(
            current_weights, expected_returns, cov_matrix, risk_free_rate
        )
        suggestions['current'] = {
            'name': 'Current Portfolio',
            'name_jp': '現在のポートフォリオ',
            'description': 'Your current portfolio allocation',
            'description_jp': '現在のポートフォリオ配分',
            'weights': dict(zip(tickers, current_weights)),
            'expected_return': current_metrics['return'] * 100,
            'volatility': current_metrics['volatility'] * 100,
            'sharpe': current_metrics['sharpe']
        }
    
    # 4. Equal Weight Portfolio
    n_assets = len(tickers)
    equal_weights = np.array([1.0 / n_assets] * n_assets)
    equal_metrics = calculate_portfolio_metrics(
        equal_weights, expected_returns, cov_matrix, risk_free_rate
    )
    suggestions['equal_weight'] = {
        'name': 'Equal Weight Portfolio',
        'name_jp': '均等加重ポートフォリオ',
        'description': 'Simple equal allocation to all assets',
        'description_jp': 'すべての資産に均等に配分',
        'weights': dict(zip(tickers, equal_weights)),
        'expected_return': equal_metrics['return'] * 100,
        'volatility': equal_metrics['volatility'] * 100,
        'sharpe': equal_metrics['sharpe']
    }
    
    return suggestions


def prepare_data_for_frontier(
    price_history: pd.DataFrame,
    annual_trading_days: int = 252
) -> tuple:
    """
    Prepare expected returns and covariance matrix from price history.
    
    Args:
        price_history: DataFrame with price history (columns are tickers)
        annual_trading_days: Number of trading days per year
        
    Returns:
        Tuple of (expected_returns, cov_matrix, tickers)
        
    Note:
        This uses simple linear scaling for annualization, which assumes
        returns are independently and identically distributed (i.i.d.).
        This is a common approximation in practice but may not be fully
        accurate for all market conditions.
    """
    # Calculate daily returns
    returns = price_history.pct_change().dropna()
    
    if returns.empty or len(returns) < 2:
        raise ValueError("Insufficient price history for calculation")
    
    # Annualized expected returns (linear scaling of daily mean)
    expected_returns = returns.mean() * annual_trading_days

    # Annualized covariance matrix (linear scaling assuming i.i.d. returns)
    cov_matrix = returns.cov() * annual_trading_days

    return expected_returns.values, cov_matrix.values, list(price_history.columns)


def backtest_portfolio(
    weights: Union[Dict[str, float], Iterable[float], np.ndarray],
    price_df: pd.DataFrame,
    benchmark_weights: Union[Dict[str, float], Iterable[float], np.ndarray] | None = None,
    annual_trading_days: int = 252,
) -> dict:
    """Backtest a portfolio using historical price data.

    Args:
        weights: Portfolio weights as a dict keyed by ticker or an array-like aligned
            with ``price_df`` columns.
        price_df: Price history DataFrame (columns: tickers, index: Datetime).
        benchmark_weights: Optional weights for a benchmark portfolio. If omitted,
            an equal-weight benchmark is used.
        annual_trading_days: Number of trading days per year for annualization.

    Returns:
        Dictionary containing daily returns, cumulative returns, and key metrics.

    Raises:
        ValueError: If price data is insufficient or weights are invalid.
    """

    if price_df is None or price_df.empty:
        raise ValueError("Price history is required for backtesting")

    price_df = price_df.sort_index()

    if len(price_df) < 20:
        raise ValueError("At least 20 price points are required for backtesting")

    returns = price_df.pct_change().dropna(how="all")
    if returns.empty:
        raise ValueError("Unable to calculate returns from provided price history")

    tickers = list(price_df.columns)

    def _normalize_weights(raw_weights) -> np.ndarray:
        if isinstance(raw_weights, dict):
            weight_array = np.array([raw_weights.get(t, np.nan) for t in tickers], dtype=float)
        else:
            weight_array = np.asarray(list(raw_weights), dtype=float)

        if weight_array.shape[0] != len(tickers):
            raise ValueError("Weights length must match number of tickers")

        if np.isnan(weight_array).any():
            raise ValueError("Weights contain missing values")

        weight_sum = weight_array.sum()
        if weight_sum <= 0:
            raise ValueError("Weights must sum to a positive value")

        return weight_array / weight_sum

    normalized_weights = _normalize_weights(weights)
    benchmark_weights = _normalize_weights(benchmark_weights) if benchmark_weights is not None else None

    # Equal weight benchmark if none provided
    if benchmark_weights is None:
        benchmark_weights = np.array([1.0 / len(tickers)] * len(tickers))

    portfolio_returns = (returns * normalized_weights).sum(axis=1)
    benchmark_returns = (returns * benchmark_weights).sum(axis=1)

    cumulative = (1 + portfolio_returns).cumprod()
    benchmark_cumulative = (1 + benchmark_returns).cumprod()

    def _calc_metrics(series: pd.Series) -> dict:
        total_return = series.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (annual_trading_days / len(series)) - 1
        volatility = series.pct_change().std() * np.sqrt(annual_trading_days)
        running_max = series.cummax()
        drawdown = (series / running_max) - 1
        max_drawdown = drawdown.min()
        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "max_drawdown": max_drawdown,
        }

    return {
        "daily_returns": portfolio_returns,
        "cumulative_returns": cumulative,
        "benchmark_cumulative": benchmark_cumulative,
        "metrics": _calc_metrics(cumulative),
        "benchmark_metrics": _calc_metrics(benchmark_cumulative),
    }
