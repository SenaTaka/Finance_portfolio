import pandas as pd
from unittest import mock

from portfolio_calculator import PortfolioCalculator


def test_risk_free_rate_normalizes_tnx_quote():
    """^TNX quotes are scaled by 10, so ensure we convert to percentage."""
    calculator = PortfolioCalculator("dummy.csv")

    mock_hist = pd.DataFrame({"Close": [42.5]}, index=[pd.Timestamp("2024-01-01")])
    mock_ticker = mock.Mock()
    mock_ticker.history.return_value = mock_hist

    with mock.patch("portfolio_calculator.yf.Ticker", return_value=mock_ticker):
        calculator.get_risk_free_rate()

    assert calculator.risk_free_rate == 4.25
