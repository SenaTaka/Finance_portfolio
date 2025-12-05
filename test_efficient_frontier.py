"""Tests for the efficient frontier module."""
import unittest
import numpy as np
import pandas as pd

from efficient_frontier import (
    calculate_portfolio_metrics,
    find_optimal_portfolio,
    find_min_volatility_portfolio,
    calculate_efficient_frontier,
    generate_random_portfolios,
    get_portfolio_suggestions,
    prepare_data_for_frontier,
)


class TestPortfolioMetrics(unittest.TestCase):
    """Test portfolio metrics calculation."""

    def setUp(self):
        """Set up test data."""
        # Simple 2-asset case
        self.expected_returns = np.array([0.10, 0.15])  # 10% and 15% annual returns
        self.cov_matrix = np.array([
            [0.04, 0.01],  # 20% vol, 5% covariance
            [0.01, 0.09]   # 30% vol
        ])
        self.risk_free_rate = 0.04

    def test_equal_weights_portfolio_return(self):
        """Test portfolio return calculation with equal weights."""
        weights = np.array([0.5, 0.5])
        metrics = calculate_portfolio_metrics(
            weights, self.expected_returns, self.cov_matrix, self.risk_free_rate
        )
        expected_return = 0.5 * 0.10 + 0.5 * 0.15
        self.assertAlmostEqual(metrics['return'], expected_return, places=6)

    def test_single_asset_portfolio(self):
        """Test portfolio with 100% in one asset."""
        weights = np.array([1.0, 0.0])
        metrics = calculate_portfolio_metrics(
            weights, self.expected_returns, self.cov_matrix, self.risk_free_rate
        )
        self.assertAlmostEqual(metrics['return'], 0.10, places=6)
        self.assertAlmostEqual(metrics['volatility'], 0.20, places=6)

    def test_sharpe_ratio_positive(self):
        """Test that Sharpe ratio is calculated correctly."""
        weights = np.array([0.5, 0.5])
        metrics = calculate_portfolio_metrics(
            weights, self.expected_returns, self.cov_matrix, self.risk_free_rate
        )
        # Expected return = 12.5%, risk-free = 4%
        # Sharpe = (0.125 - 0.04) / volatility
        self.assertGreater(metrics['sharpe'], 0)


class TestOptimalPortfolio(unittest.TestCase):
    """Test optimal portfolio finding."""

    def setUp(self):
        """Set up test data."""
        self.expected_returns = np.array([0.08, 0.12, 0.16])
        self.cov_matrix = np.array([
            [0.0225, 0.0045, 0.0090],
            [0.0045, 0.0400, 0.0120],
            [0.0090, 0.0120, 0.0900]
        ])
        self.risk_free_rate = 0.04

    def test_optimal_portfolio_weights_sum_to_one(self):
        """Test that optimal portfolio weights sum to 1."""
        result = find_optimal_portfolio(
            self.expected_returns, self.cov_matrix, self.risk_free_rate
        )
        self.assertAlmostEqual(np.sum(result['weights']), 1.0, places=5)

    def test_optimal_portfolio_no_short_selling(self):
        """Test that weights are non-negative when short selling is disabled."""
        result = find_optimal_portfolio(
            self.expected_returns, self.cov_matrix, self.risk_free_rate, allow_short=False
        )
        self.assertTrue(all(w >= -1e-6 for w in result['weights']))

    def test_optimal_portfolio_success(self):
        """Test that optimization converges successfully."""
        result = find_optimal_portfolio(
            self.expected_returns, self.cov_matrix, self.risk_free_rate
        )
        self.assertTrue(result['success'])


class TestMinVolatilityPortfolio(unittest.TestCase):
    """Test minimum volatility portfolio finding."""

    def setUp(self):
        """Set up test data."""
        self.expected_returns = np.array([0.08, 0.12, 0.16])
        self.cov_matrix = np.array([
            [0.0225, 0.0045, 0.0090],
            [0.0045, 0.0400, 0.0120],
            [0.0090, 0.0120, 0.0900]
        ])

    def test_min_volatility_weights_sum_to_one(self):
        """Test that min volatility portfolio weights sum to 1."""
        result = find_min_volatility_portfolio(
            self.expected_returns, self.cov_matrix
        )
        self.assertAlmostEqual(np.sum(result['weights']), 1.0, places=5)

    def test_min_volatility_lower_than_individual_assets(self):
        """Test that min volatility is lower than or equal to lowest individual asset volatility."""
        result = find_min_volatility_portfolio(
            self.expected_returns, self.cov_matrix
        )
        individual_vols = [np.sqrt(self.cov_matrix[i, i]) for i in range(len(self.expected_returns))]
        min_individual_vol = min(individual_vols)
        # Min vol portfolio should be at most as risky as the least risky individual asset
        # (can be lower due to diversification)
        self.assertLessEqual(result['volatility'], min_individual_vol + 0.01)


class TestEfficientFrontier(unittest.TestCase):
    """Test efficient frontier calculation."""

    def setUp(self):
        """Set up test data."""
        self.expected_returns = np.array([0.08, 0.12, 0.16])
        self.cov_matrix = np.array([
            [0.0225, 0.0045, 0.0090],
            [0.0045, 0.0400, 0.0120],
            [0.0090, 0.0120, 0.0900]
        ])

    def test_frontier_returns_dataframe(self):
        """Test that efficient frontier returns a DataFrame."""
        frontier = calculate_efficient_frontier(
            self.expected_returns, self.cov_matrix, n_points=10
        )
        self.assertIsInstance(frontier, pd.DataFrame)

    def test_frontier_has_required_columns(self):
        """Test that frontier DataFrame has required columns."""
        frontier = calculate_efficient_frontier(
            self.expected_returns, self.cov_matrix, n_points=10
        )
        if not frontier.empty:
            required_cols = ['volatility', 'return', 'sharpe', 'weights']
            for col in required_cols:
                self.assertIn(col, frontier.columns)

    def test_frontier_volatility_increases_with_return(self):
        """Test that higher returns generally require higher volatility on the frontier."""
        frontier = calculate_efficient_frontier(
            self.expected_returns, self.cov_matrix, n_points=20
        )
        if len(frontier) > 5:
            # Sort by return and check if volatility generally increases
            sorted_frontier = frontier.sort_values('return')
            first_half = sorted_frontier.head(len(sorted_frontier)//2)
            second_half = sorted_frontier.tail(len(sorted_frontier)//2)
            self.assertLess(first_half['volatility'].mean(), second_half['volatility'].mean())


class TestRandomPortfolios(unittest.TestCase):
    """Test random portfolio generation."""

    def setUp(self):
        """Set up test data."""
        self.expected_returns = np.array([0.08, 0.12])
        self.cov_matrix = np.array([
            [0.04, 0.01],
            [0.01, 0.09]
        ])

    def test_generates_correct_number(self):
        """Test that correct number of portfolios is generated."""
        n = 100
        random_portfolios = generate_random_portfolios(
            self.expected_returns, self.cov_matrix, n_portfolios=n
        )
        self.assertEqual(len(random_portfolios), n)

    def test_all_weights_sum_to_one(self):
        """Test that all generated portfolio weights sum to 1."""
        random_portfolios = generate_random_portfolios(
            self.expected_returns, self.cov_matrix, n_portfolios=50
        )
        for weights in random_portfolios['weights']:
            self.assertAlmostEqual(sum(weights), 1.0, places=5)


class TestPortfolioSuggestions(unittest.TestCase):
    """Test portfolio suggestion generation."""

    def setUp(self):
        """Set up test data."""
        self.tickers = ['AAPL', 'GOOGL', 'MSFT']
        self.expected_returns = np.array([0.10, 0.15, 0.12])
        self.cov_matrix = np.array([
            [0.04, 0.01, 0.015],
            [0.01, 0.09, 0.02],
            [0.015, 0.02, 0.0625]
        ])
        self.current_weights = np.array([0.4, 0.3, 0.3])

    def test_suggestions_contain_required_keys(self):
        """Test that suggestions contain all required portfolio types."""
        suggestions = get_portfolio_suggestions(
            self.tickers, self.expected_returns, self.cov_matrix, self.current_weights
        )
        required_keys = ['max_sharpe', 'min_volatility', 'current', 'equal_weight']
        for key in required_keys:
            self.assertIn(key, suggestions)

    def test_suggestions_have_correct_tickers(self):
        """Test that suggestions weights have correct tickers."""
        suggestions = get_portfolio_suggestions(
            self.tickers, self.expected_returns, self.cov_matrix
        )
        for key, sug in suggestions.items():
            if key != 'current':  # current won't exist if no current_weights
                for ticker in self.tickers:
                    self.assertIn(ticker, sug['weights'])

    def test_max_sharpe_has_higher_sharpe_than_equal_weight(self):
        """Test that max Sharpe portfolio has higher Sharpe than equal weight."""
        suggestions = get_portfolio_suggestions(
            self.tickers, self.expected_returns, self.cov_matrix
        )
        self.assertGreaterEqual(
            suggestions['max_sharpe']['sharpe'],
            suggestions['equal_weight']['sharpe'] - 0.01  # Allow small tolerance
        )


class TestPrepareDataForFrontier(unittest.TestCase):
    """Test data preparation function."""

    def test_prepare_data_returns_correct_types(self):
        """Test that prepare_data_for_frontier returns correct types."""
        # Create sample price history
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        price_history = pd.DataFrame({
            'AAPL': np.random.randn(100).cumsum() + 100,
            'GOOGL': np.random.randn(100).cumsum() + 150
        }, index=dates)
        
        expected_returns, cov_matrix, tickers = prepare_data_for_frontier(price_history)
        
        self.assertIsInstance(expected_returns, np.ndarray)
        self.assertIsInstance(cov_matrix, np.ndarray)
        self.assertIsInstance(tickers, list)

    def test_prepare_data_correct_dimensions(self):
        """Test that prepare_data_for_frontier returns correct dimensions."""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        n_assets = 3
        price_history = pd.DataFrame({
            f'ASSET{i}': np.random.randn(100).cumsum() + 100
            for i in range(n_assets)
        }, index=dates)
        
        expected_returns, cov_matrix, tickers = prepare_data_for_frontier(price_history)
        
        self.assertEqual(len(expected_returns), n_assets)
        self.assertEqual(cov_matrix.shape, (n_assets, n_assets))
        self.assertEqual(len(tickers), n_assets)

    def test_prepare_data_raises_on_insufficient_data(self):
        """Test that prepare_data_for_frontier raises error on insufficient data."""
        dates = pd.date_range(start='2023-01-01', periods=1, freq='D')
        price_history = pd.DataFrame({
            'AAPL': [100]
        }, index=dates)
        
        with self.assertRaises(ValueError):
            prepare_data_for_frontier(price_history)


if __name__ == "__main__":
    unittest.main()
