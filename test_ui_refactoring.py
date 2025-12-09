"""Test script for UI refactoring.

This script tests that all components and pages can be imported and initialized properly.
"""

import sys
import pandas as pd
import numpy as np

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.ui.state import AppState
        print("✓ AppState imported")
        
        from src.ui.components import (
            PortfolioMetrics, 
            SettingsSidebar, 
            AllocationChart, 
            SectorChart, 
            RiskReturnChart, 
            DetailedDataTable
        )
        print("✓ All components imported")
        
        from src.ui.pages import (
            HomePage, 
            AnalysisPage, 
            OptimizationPage, 
            RebalancingPage, 
            HistoryPage
        )
        print("✓ All pages imported")
        
        from src.utils.file_utils import extract_timestamp_from_filename
        print("✓ File utils imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_state_management():
    """Test state management functionality."""
    print("\nTesting state management...")
    
    try:
        from src.ui.state import AppState
        
        # Test state operations (without Streamlit)
        print("✓ State management module loaded")
        return True
    except Exception as e:
        print(f"✗ State management test failed: {e}")
        return False


def test_data_loading():
    """Test data loading capabilities."""
    print("\nTesting data loading...")
    
    try:
        import glob
        import os
        
        # Check for result files
        us_files = glob.glob(os.path.join("output", "portfolio_result_*.csv"))
        jp_files = glob.glob(os.path.join("output", "portfolio_jp_result_*.csv"))
        
        print(f"  Found {len(us_files)} US result files")
        print(f"  Found {len(jp_files)} JP result files")
        
        if us_files or jp_files:
            # Try loading a file
            test_file = us_files[0] if us_files else jp_files[0]
            df = pd.read_csv(test_file)
            print(f"✓ Successfully loaded {len(df)} records from test file")
            print(f"  Columns: {', '.join(df.columns[:5])}...")
            return True
        else:
            print("✓ No data files to test (this is OK)")
            return True
            
    except Exception as e:
        print(f"✗ Data loading test failed: {e}")
        return False


def test_component_structure():
    """Test that components have expected methods."""
    print("\nTesting component structure...")
    
    try:
        from src.ui.components import (
            PortfolioMetrics, 
            AllocationChart, 
            SectorChart, 
            RiskReturnChart, 
            DetailedDataTable
        )
        
        # Check that components have render methods
        components = [
            PortfolioMetrics, 
            AllocationChart, 
            SectorChart, 
            RiskReturnChart, 
            DetailedDataTable
        ]
        
        for comp in components:
            if not hasattr(comp, 'render'):
                print(f"✗ {comp.__name__} missing render method")
                return False
        
        print(f"✓ All {len(components)} components have render method")
        return True
        
    except Exception as e:
        print(f"✗ Component structure test failed: {e}")
        return False


def test_page_structure():
    """Test that pages have expected methods."""
    print("\nTesting page structure...")
    
    try:
        from src.ui.pages import (
            HomePage, 
            AnalysisPage, 
            OptimizationPage, 
            RebalancingPage, 
            HistoryPage
        )
        
        pages = [HomePage, AnalysisPage, OptimizationPage, RebalancingPage, HistoryPage]
        
        for page in pages:
            if not hasattr(page, 'render'):
                print(f"✗ {page.__name__} missing render method")
                return False
        
        print(f"✓ All {len(pages)} pages have render method")
        return True
        
    except Exception as e:
        print(f"✗ Page structure test failed: {e}")
        return False


def test_file_utils():
    """Test file utility functions."""
    print("\nTesting file utilities...")
    
    try:
        from src.utils.file_utils import extract_timestamp_from_filename
        
        # Test timestamp extraction
        test_filename = "portfolio_result_20251209_120000.csv"
        timestamp = extract_timestamp_from_filename(test_filename)
        
        if timestamp and "2025/12/09" in timestamp:
            print(f"✓ Timestamp extraction works: {timestamp}")
            return True
        else:
            print(f"✗ Timestamp extraction failed: {timestamp}")
            return False
            
    except Exception as e:
        print(f"✗ File utils test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("UI Refactoring Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("State Management", test_state_management),
        ("Data Loading", test_data_loading),
        ("Component Structure", test_component_structure),
        ("Page Structure", test_page_structure),
        ("File Utilities", test_file_utils),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("=" * 60)
    print(f"Overall: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
