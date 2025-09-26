import os
from datetime import datetime

# Test directory creation
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
results_dir = f'simulation_results/{timestamp}'
os.makedirs(results_dir, exist_ok=True)
print(f'Created directory: {results_dir}')
print('Directory structure works correctly!')

# Test file creation
test_file = f'{results_dir}/test.txt'
with open(test_file, 'w') as f:
    f.write('Test file for directory structure validation\n')
print(f'Created test file: {test_file}')

# List the structure
print('\nDirectory structure:')
for root, dirs, files in os.walk('simulation_results'):
    level = root.replace('simulation_results', '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')
