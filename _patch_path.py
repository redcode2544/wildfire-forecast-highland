import json, sys
sys.stdout.reconfigure(encoding='utf-8')

nb_path = 'D:/PuperAI69/wildfire_spread_forecast_ML.ipynb'
with open(nb_path, encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][2]
src = ''.join(cell['source'])

old = "BASE_DIR      = Path('D:/PuperAI69')"
new = (
    "# ── ใช้ path ของโฟลเดอร์ที่ notebook อยู่ (รองรับทั้ง Windows/Mac/Linux) ──\n"
    "BASE_DIR      = Path(globals().get('__vsc_ipynb_file__', '') or __file__\n"
    "               if '__file__' in dir() else Path.cwd()).resolve().parent\n"
    "if not (BASE_DIR / 'zones_area.geojson').exists():\n"
    "    BASE_DIR = Path.cwd()  # fallback: current working directory"
)

# simpler & more reliable approach for Jupyter
new = "BASE_DIR      = Path.cwd()  # ใช้ directory ที่รัน notebook (cross-platform)"

src_new = src.replace(old, new)
nb['cells'][2]['source'] = [src_new]

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Done: BASE_DIR changed to Path.cwd()")
print("  รัน notebook จาก directory ของโปรเจกต์เสมอ:")
print("  cd ~/wildfire-forecast-highland && jupyter lab")
