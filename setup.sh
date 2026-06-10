#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# Wildfire Forecast ML — Setup Script (macOS / Linux)
# ──────────────────────────────────────────────────────────────────────────────

set -e

echo "=== Wildfire Forecast ML Setup ==="

# 1. Create conda environment
if command -v conda &> /dev/null; then
    echo "[1/4] สร้าง conda environment 'wildfire'..."
    conda create -n wildfire python=3.11 -y
    conda activate wildfire || source activate wildfire

    # Install GDAL/geopandas via conda-forge (แนะนำสำหรับ geospatial)
    conda install -c conda-forge geopandas fiona pyproj shapely rasterio -y
    pip install -r requirements.txt
else
    echo "[1/4] ไม่พบ conda — ใช้ pip..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 2. Copy .env.example → .env
if [ ! -f .env ]; then
    echo "[2/4] สร้างไฟล์ .env..."
    cp .env.example .env
    echo "  ⚠️  กรุณาเปิดไฟล์ .env แล้วใส่ GISTDA_KEY ของคุณ"
fi

# 3. สร้าง wildfire_output directory
mkdir -p wildfire_output

# 4. Done
echo ""
echo "✅ Setup เสร็จแล้ว!"
echo ""
echo "วิธีใช้งาน:"
echo "  1. เปิดไฟล์ .env แล้วใส่ GISTDA_KEY ของคุณ"
echo "  2. รัน: jupyter lab wildfire_spread_forecast_ML.ipynb"
echo "  หรือรัน script: python _run_notebook.py"
echo ""
