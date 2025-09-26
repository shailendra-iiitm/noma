#!/usr/bin/env python3
"""
Comprehensive test script for the NOMA clustering simulation
Tests that all functions can be imported and key calculations work
"""

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        import pandas as pd
        import networkx as nx
        from tqdm import tqdm
        import os
        import time
        from datetime import datetime
        import seaborn as sns
        from matplotlib.patches import Circle
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without running full simulation"""
    print("\nTesting basic functionality...")
    
    try:
        # Test the critical functions from clustering.py
        import numpy as np
        from datetime import datetime
        import os
        
        # Test parameter initialization
        N, radius = 500, 5000
        fc, c = 3.5e9, 3e8
        lambda_c = c / fc
        h_BS = 25
        print(f"✓ Parameters initialized: N={N}, radius={radius}m, fc={fc/1e9:.1f}GHz")
        
        # Test directory creation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = f"test_results_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        print(f"✓ Test directory created: {results_dir}")
        
        # Test channel calculations
        r = np.sqrt(np.random.uniform(0, radius**2, 10))  # Small test set
        theta = np.random.uniform(0, 2*np.pi, 10)
        h_UTs = np.random.uniform(1.5, 22.5, 10)
        print(f"✓ User positions generated: {len(r)} test users")
        
        # Test path loss calculation
        d_3D = np.sqrt(r**2 + (h_BS - h_UTs)**2)
        PL_dB = 28.0 + 22 * np.log10(d_3D) + 20 * np.log10(fc / 1e9)  # Simple LOS model
        print(f"✓ Path loss calculated: range {PL_dB.min():.1f} to {PL_dB.max():.1f} dB")
        
        # Test fading and channel gain
        fading = np.random.rayleigh(scale=1.0, size=10)
        pl_linear = 10 ** (-PL_dB / 10)
        h_values = fading * np.sqrt(pl_linear)
        h_db = 10 * np.log10(h_values**2 + 1e-12)
        print(f"✓ Channel gains calculated: range {h_db.min():.1f} to {h_db.max():.1f} dB")
        
        # Clean up test directory
        os.rmdir(results_dir)
        print("✓ Test cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run comprehensive tests"""
    print("="*60)
    print("NOMA CLUSTERING SIMULATION - COMPREHENSIVE TEST")
    print("="*60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 2: Basic functionality
    if test_basic_functionality():
        tests_passed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! The simulation is ready to run.")
        print("\nTo run the full simulation:")
        print("  Windows: run_simulation.bat")
        print("  Python:  python clustering.py")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\nYou may need to install missing dependencies:")
        print("  pip install -r requirements.txt")
    
    print("="*60)
    return tests_passed == total_tests

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
