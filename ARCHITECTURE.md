# Architecture Documentation

> 📘 **日本語版** | [ARCHITECTURE_JP.md](ARCHITECTURE_JP.md)

## Overview

This document describes the modular architecture of the Finance Portfolio Management System. The system has been refactored to support large-scale development with improved extensibility and maintainability.

## Architecture Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Modularity**: Components are loosely coupled and highly cohesive
3. **Extensibility**: Easy to add new features without modifying existing code
4. **Testability**: Components can be tested independently
5. **Maintainability**: Clear structure makes code easier to understand and modify

## Directory Structure

```
Finance_portfolio/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   └── portfolio_calculator.py
│   ├── data/                     # Data access layer
│   │   ├── __init__.py
│   │   ├── cache_manager.py
│   │   └── stock_data_fetcher.py
│   ├── analysis/                 # Analysis modules
│   │   ├── __init__.py
│   │   ├── efficient_frontier.py
│   │   ├── sharpe_optimized.py
│   │   └── crash_scenario_analysis.py
│   ├── ui/                       # User interface components
│   │   ├── __init__.py
│   │   ├── chart_utils.py
│   │   └── data_loader.py
│   └── utils/                    # Utility modules
│       ├── __init__.py
│       ├── config.py
│       ├── file_utils.py
│       └── region_classifier.py
├── tests/                        # Test files
├── data/                         # Data directory (cache, etc.)
├── output/                       # Output directory (results)
├── portfolio.csv                 # US portfolio input
├── portfolio_jp.csv              # Japan portfolio input
├── portfolio_app.py              # Streamlit UI (legacy, to be refactored)
└── portfolio_calculator.py       # Legacy entry point
```

## Module Descriptions

### Core Layer (`src/core/`)

**Purpose**: Contains the core business logic for portfolio calculations.

- `portfolio_calculator.py`: Main portfolio calculation engine
  - Orchestrates data fetching, calculations, and result saving
  - Uses data layer for fetching and caching
  - Produces portfolio valuation and metrics

### Data Access Layer (`src/data/`)

**Purpose**: Handles all external data access and caching.

- `cache_manager.py`: Manages caching of stock data
  - TTL-based cache expiration
  - Separate TTL for metadata, volatility, and price data
  - JSON file-based storage
  
- `stock_data_fetcher.py`: Fetches stock data from external sources
  - Yahoo Finance integration
  - Exchange rate fetching
  - Stock metadata, price, and historical data
  - Volatility and Sharpe ratio calculations

### Analysis Layer (`src/analysis/`)

**Purpose**: Provides analytical functions for portfolio optimization.

- `efficient_frontier.py`: Modern Portfolio Theory calculations
  - Efficient frontier calculation
  - Portfolio optimization (max Sharpe, min volatility)
  - Random portfolio generation
  - Backtesting capabilities
  
- `sharpe_optimized.py`: Sharpe ratio-based optimization
  - Score calculation based on Sharpe and volatility
  - Target weight calculation
  - Trade plan generation
  
- `crash_scenario_analysis.py`: Stress testing and scenario analysis
  - Portfolio crash scenario modeling
  - Beta-based impact analysis
  - Risk mitigation suggestions

### UI Layer (`src/ui/`)

**Purpose**: User interface components and utilities.

- `chart_utils.py`: Reusable chart creation utilities
  - Mobile-friendly chart layouts
  - Standard chart types (pie, bar, scatter, line, heatmap)
  - Consistent styling
  
- `data_loader.py`: Data loading utilities for UI
  - Combined portfolio loading
  - File selection and loading
  - Correlation matrix loading

### Utilities Layer (`src/utils/`)

**Purpose**: Common utilities and configuration.

- `config.py`: Central configuration management
  - Directory paths
  - Cache settings
  - Default values
  - UI settings
  
- `file_utils.py`: File operation utilities
  - Timestamp extraction from filenames
  - File pattern matching
  - Directory management
  
- `region_classifier.py`: Geographic classification
  - Country to region mapping
  - Region definitions

## Design Patterns Used

### 1. Separation of Concerns
Each layer has a distinct responsibility:
- Data layer: External data access
- Core layer: Business logic
- Analysis layer: Calculations and algorithms
- UI layer: User interface
- Utils layer: Common functionality

### 2. Dependency Injection
Components receive dependencies through constructor injection, making them easier to test and modify.

### 3. Configuration Management
Centralized configuration in `config.py` makes it easy to modify behavior without changing code.

### 4. Strategy Pattern
Different analysis strategies (efficient frontier, Sharpe optimization, scenario analysis) are implemented as separate modules.

## Extensibility

### Adding New Analysis Modules

1. Create a new file in `src/analysis/`
2. Implement your analysis functions
3. Add exports to `src/analysis/__init__.py`
4. Import and use in UI or other components

Example:
```python
# src/analysis/my_new_analysis.py
def analyze_something(data):
    # Your analysis logic
    pass
```

### Adding New Data Sources

1. Create a new fetcher class in `src/data/`
2. Follow the interface pattern of `StockDataFetcher`
3. Add to `src/data/__init__.py`

### Adding New UI Components

1. Create new chart types in `src/ui/chart_utils.py`
2. Create new pages or sections using existing utilities
3. Follow mobile-friendly design patterns

## Migration Guide

### For Existing Code

The old modules remain for backward compatibility:
- `portfolio_calculator.py` (legacy entry point)
- `efficient_frontier.py` (in root)
- `sharpe_optimized.py` (in root)

New code should use:
```python
from src.core.portfolio_calculator import PortfolioCalculator
from src.analysis import efficient_frontier, sharpe_optimized
from src.ui import chart_utils, DataLoader
```

### Backward Compatibility

A new entry point `portfolio_calculator_new.py` demonstrates the new architecture while maintaining the same CLI interface:

```bash
# Old way (still works)
python portfolio_calculator.py portfolio.csv

# New way (recommended)
python portfolio_calculator_new.py portfolio.csv
```

## Testing Strategy

### Unit Tests
Each module should have corresponding unit tests in `tests/`:
- Test modules independently
- Mock external dependencies
- Focus on business logic

### Integration Tests
Test interactions between modules:
- Data fetching and caching
- Portfolio calculation pipeline
- UI data loading

### End-to-End Tests
Test complete workflows:
- Portfolio update and calculation
- UI rendering and interaction

## Performance Considerations

1. **Caching**: Reduces API calls with TTL-based caching
2. **Lazy Loading**: Data fetched only when needed
3. **Batch Operations**: Multiple stocks processed efficiently
4. **Correlation Matrix**: Computed once and cached

## Future Enhancements

### Phase 1: Complete UI Refactoring
- Split `portfolio_app.py` into modular pages
- Create reusable UI components
- Improve state management

### Phase 2: Database Integration
- Replace JSON cache with database
- Add historical tracking
- Support multiple portfolios

### Phase 3: Real-time Updates
- WebSocket integration
- Live price updates
- Real-time notifications

### Phase 4: Advanced Analytics
- Machine learning predictions
- Sentiment analysis
- News integration

### Phase 5: API Layer
- REST API for programmatic access
- Authentication and authorization
- Rate limiting

## Contributing

When adding new features:

1. Follow the modular architecture
2. Add appropriate documentation
3. Write unit tests
4. Update this architecture document
5. Maintain backward compatibility when possible

## Questions and Support

For questions about the architecture:
1. Review this document
2. Check module docstrings
3. Examine existing code patterns
4. Refer to inline comments
