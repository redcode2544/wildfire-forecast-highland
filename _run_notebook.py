"""
Execute all code cells in the wildfire notebook sequentially.
Captures stdout/stderr per cell and prints a summary.
"""
import json, sys, io, traceback, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Force non-interactive matplotlib BEFORE any other imports so plt.show() is a no-op
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as _plt_module
_plt_module.show = lambda **kw: None   # silence all show() calls

NB_PATH = Path('D:/PuperAI69/wildfire_spread_forecast_ML.ipynb')
with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
code_cells = [(i, c) for i, c in enumerate(cells) if c['cell_type'] == 'code']

# Shared namespace across all cells (simulates a Jupyter kernel)
ns = {}

errors   = []
warnings = []

for cell_idx, (nb_idx, cell) in enumerate(code_cells):
    src = ''.join(cell['source']).strip()
    if not src:
        continue

    first_line = src.split('\n')[0][:70]
    print(f'\n{"="*60}')
    print(f'[{cell_idx+1}/{len(code_cells)}] Cell nb[{nb_idx}]: {first_line}')
    print('='*60)

    t0 = time.time()
    try:
        exec(compile(src, f'<cell {nb_idx}>', 'exec'), ns)
        elapsed = time.time() - t0
        print(f'  -> OK ({elapsed:.1f}s)')
    except Exception as e:
        elapsed = time.time() - t0
        tb = traceback.format_exc()
        print(f'  -> ERROR ({elapsed:.1f}s):')
        print(tb)
        errors.append({'cell': nb_idx, 'error': str(e), 'tb': tb})
        # Continue to next cell (some cells may be OK)

print('\n' + '='*60)
print('EXECUTION SUMMARY')
print('='*60)
print(f'  Code cells run: {len(code_cells)}')
print(f'  Errors: {len(errors)}')
if errors:
    for e in errors:
        print(f'    Cell nb[{e["cell"]}]: {e["error"][:100]}')
print()

# Print key output files
OUT_DIR = Path('D:/PuperAI69/wildfire_output')
if OUT_DIR.exists():
    files = sorted(OUT_DIR.iterdir())
    print('Output files:')
    for f in files:
        size_kb = f.stat().st_size / 1024
        print(f'  {f.name:45s} {size_kb:8.1f} KB')
