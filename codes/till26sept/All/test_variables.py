#!/usr/bin/env python3
"""
Quick test script to verify all variables are defined correctly in clustering.py
"""

import sys
import os

def test_variable_definitions():
    """Test that all critical variables are defined before use"""
    
    # Read the clustering.py file
    with open('clustering.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Variables that should be defined before use
    critical_vars = {
        'results_dir': False,
        'pl_db': False,
        'shadowing': False,
        'pl_1m_db': False,
        'N': False,
        'h_values': False,
        'h_db': False
    }
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Check for variable definitions
        if 'results_dir = ' in line and not line.startswith('#'):
            critical_vars['results_dir'] = True
            print(f"✓ Line {i}: results_dir defined")
            
        if 'pl_db = ' in line and not line.startswith('#'):
            critical_vars['pl_db'] = True
            print(f"✓ Line {i}: pl_db defined")
            
        if 'shadowing = ' in line and not line.startswith('#'):
            critical_vars['shadowing'] = True
            print(f"✓ Line {i}: shadowing defined")
            
        if 'pl_1m_db = ' in line and not line.startswith('#'):
            critical_vars['pl_1m_db'] = True
            print(f"✓ Line {i}: pl_1m_db defined")
            
        if 'N, radius = ' in line and not line.startswith('#'):
            critical_vars['N'] = True
            print(f"✓ Line {i}: N defined")
            
        if 'h_values = ' in line and not line.startswith('#'):
            critical_vars['h_values'] = True
            print(f"✓ Line {i}: h_values defined")
            
        if 'h_db = ' in line and not line.startswith('#'):
            critical_vars['h_db'] = True
            print(f"✓ Line {i}: h_db defined")
    
    print("\n" + "="*50)
    print("VARIABLE DEFINITION CHECK SUMMARY")
    print("="*50)
    
    all_defined = True
    for var, defined in critical_vars.items():
        status = "✓ DEFINED" if defined else "✗ MISSING"
        print(f"{var:15} : {status}")
        if not defined:
            all_defined = False
    
    print("="*50)
    if all_defined:
        print("✅ ALL CRITICAL VARIABLES ARE PROPERLY DEFINED!")
        return True
    else:
        print("❌ SOME VARIABLES ARE MISSING DEFINITIONS!")
        return False

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    success = test_variable_definitions()
    sys.exit(0 if success else 1)
