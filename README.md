# Wildfire Spread Forecast ML

ระบบพยากรณ์การแพร่กระจายไฟป่าสำหรับพื้นที่สูง **55 โครงการ** ในภาคเหนือของไทย

ใช้ข้อมูล hotspot VIIRS (GISTDA), ลม (Open-Meteo), terrain (OpenTopoData) และ Burned Area (Sentinel-2) ร่วมกับ Random Forest + Cellular Automaton (CA) simulation

## โครงสร้างไฟล์

```
wildfire_spread_forecast_ML.ipynb   ← Notebook หลัก (33 cells)
zones_area.geojson                  ← ขอบเขต 55 โครงการ (453 โพลีกอน)
Burned_Area_Sentinel-2/             ← ข้อมูล Burned Area จาก Sentinel-2 (shapefiles)
wildfire_output/                    ← ผลลัพธ์จาก notebook
_run_notebook.py                    ← Script รัน notebook แบบ headless
requirements.txt                    ← Python packages ที่ต้องการ
setup.sh                            ← Script setup สำหรับ macOS/Linux
```

## ติดตั้ง (macOS / Linux)

```bash
git clone https://github.com/YOUR_USERNAME/PuperAI69.git
cd PuperAI69
bash setup.sh
```

## ตั้งค่า API Key

```bash
cp .env.example .env
# เปิด .env แล้วใส่ GISTDA_KEY ของคุณ
```

## รันระบบ

```bash
# วิธีที่ 1: Jupyter Lab (แนะนำ)
jupyter lab wildfire_spread_forecast_ML.ipynb

# วิธีที่ 2: Command line (headless)
python _run_notebook.py
```

## ผลลัพธ์

| ไฟล์ | รายละเอียด |
|------|-----------|
| `wildfire_output/wildfire_forecast_map.html` | แผนที่ interactive แสดง risk ทุกโซน |
| `wildfire_output/zone_risk_ranking.csv` | ตารางความเสี่ยงของทุกโครงการ |
| `wildfire_output/forecast_report.txt` | รายงานสรุป |
| `wildfire_output/*.png` | กราฟวิเคราะห์ต่างๆ |

## Model Performance

- **Algorithm**: Random Forest + CalibratedClassifierCV + CA Simulation
- **Features**: 22 (hotspot proximity, terrain, wind, seasonal, drought)
- **Leave-one-out AUC**: 0.760 ± 0.179
- **Brier Score**: 0.135

## Data Sources

| ข้อมูล | แหล่ง | ลิขสิทธิ์ |
|-------|-------|---------|
| VIIRS Hotspot | GISTDA API | ต้องมี API Key |
| ลม/อุณหภูมิ | Open-Meteo | ฟรี |
| Elevation | OpenTopoData (SRTM) | ฟรี |
| Burned Area | Sentinel-2 / GISTDA | ข้อมูลที่รวบรวมมา |

## หมายเหตุ

- ฤดูไฟ: **มกราคม – พฤษภาคม** (peak กุมภาพันธ์–เมษายน)
- ช่วงนอกฤดูไฟ (มิ.ย.–ธ.ค.) ระบบจะแสดงความเสี่ยงต่ำเป็นปกติ
- ไฟล์ `.tif` (ภาพถ่ายดาวเทียม) ไม่ได้รวมใน repo เพราะขนาดใหญ่เกิน 100MB
