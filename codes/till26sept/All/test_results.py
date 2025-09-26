import os

print('Checking simulation_results directory:')
if os.path.exists('simulation_results'):
    runs = os.listdir('simulation_results')
    valid_runs = []
    for run in runs:
        if os.path.isdir(f'simulation_results/{run}'):
            valid_runs.append(run)
    
    print(f'Found {len(valid_runs)} simulation runs:')
    for run in valid_runs:
        files = os.listdir(f'simulation_results/{run}')
        csv_files = [f for f in files if f.endswith('.csv')]
        png_files = [f for f in files if f.endswith('.png')]
        print(f'  {run}: {len(csv_files)} CSV files, {len(png_files)} PNG files')
        
        # Check if summary file exists
        summary_path = f'simulation_results/{run}/clustering_summary.csv'
        if os.path.exists(summary_path):
            print(f'    ✓ Summary file available')
        else:
            print(f'    ✗ Summary file missing')
else:
    print('No simulation_results directory found')

print('\nTesting results manager import...')
try:
    # Test if results manager can be imported
    import results_manager
    
    # Reload the module to ensure we get the latest version
    import importlib
    importlib.reload(results_manager)
    
    print('✓ Results manager imported successfully')
    
    # Check if function exists
    if hasattr(results_manager, 'list_simulation_runs'):
        print('✓ list_simulation_runs function found')
        
        # Test listing function
        runs = results_manager.list_simulation_runs()
        if runs:
            print(f'✓ Found {len(runs)} runs via results manager')
        else:
            print('✗ No runs found via results manager')
    else:
        print('✗ list_simulation_runs function not found')
        print('Available functions:', [attr for attr in dir(results_manager) if not attr.startswith('_')])
        
except Exception as e:
    print(f'✗ Error with results manager: {e}')
    import traceback
    traceback.print_exc()

print('\nTest completed!')
