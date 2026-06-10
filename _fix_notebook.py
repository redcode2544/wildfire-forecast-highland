"""
Fix wildfire notebook:
1. Cell [4]  - Filter burnscar to only files overlapping operational zones
2. Cell [6]  - Tag hotspots by proximity to zones, filter for CA
3. Cell [22] - Use near-zone hotspots for CA spread
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = Path('D:/PuperAI69/wildfire_spread_forecast_ML.ipynb')
with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']

# ─────────────────────────────────────────────────────────────────────────────
# FIX 1 — Cell [4]: filter burnscar by zone overlap
# ─────────────────────────────────────────────────────────────────────────────
OLD_BURN_LOAD = """\
# ── Burned Area ────────────────────────────────────────────
print('\\n📂 โหลด Burned Area Shapefiles...')
burnscar_list = []
for shp in sorted(BURNSCAR_DIR.glob('*.shp')):
    gdf = gpd.read_file(shp).to_crs('EPSG:4326')
    gdf['source'] = shp.stem
    burnscar_list.append(gdf)
    burn_date = pd.to_datetime(gdf['BURNDate'].iloc[0]).strftime('%Y-%m-%d')
    area_km2  = gdf.to_crs('EPSG:32647').geometry.area.sum() / 1e6
    print(f'  ✔ {shp.name}: {len(gdf):,} polygons | {burn_date} | {area_km2:.1f} km²')

burnscar_all = pd.concat(burnscar_list, ignore_index=True)"""

NEW_BURN_LOAD = """\
# ── Burned Area ────────────────────────────────────────────
# กรองเฉพาะไฟล์ที่ครอบคลุมพื้นที่ดำเนินงานจริง (ไม่ใช่กรุงเทพ/ภาคกลาง)
print('\\n📂 โหลด Burned Area Shapefiles...')
zones_bbox = box(*zones_ops.total_bounds)      # bounding box ของ zones
zones_hull_geom = zones_ops.geometry.unary_union.convex_hull  # สำหรับคำนวณระยะทาง

burnscar_list = []
for shp in sorted(BURNSCAR_DIR.glob('*.shp')):
    gdf = gpd.read_file(shp).to_crs('EPSG:4326')
    gdf['source'] = shp.stem
    burn_date = pd.to_datetime(gdf['BURNDate'].iloc[0]).strftime('%Y-%m-%d')
    area_km2  = gdf.to_crs('EPSG:32647').geometry.area.sum() / 1e6

    # ตรวจ overlap: bounding box ของ burnscar ต้อง intersect กับ zones bbox
    burn_bbox = box(*gdf.total_bounds)
    if not burn_bbox.intersects(zones_bbox):
        print(f'  ❌ ตัดออก: {shp.name} | {burn_date} | ไม่ overlap กับ zones (ผิดพื้นที่)')
        continue

    burnscar_list.append(gdf)
    print(f'  ✅ {shp.name}: {len(gdf):,} polygons | {burn_date} | {area_km2:.1f} km²')

if not burnscar_list:
    print('  ⚠️  ไม่มี burnscar ที่ถูกต้อง → ระบบจะใช้ synthetic training')

burnscar_all = pd.concat(burnscar_list, ignore_index=True) if burnscar_list else pd.DataFrame()"""

src4 = ''.join(cells[4]['source'])
if OLD_BURN_LOAD in src4:
    cells[4]['source'] = [src4.replace(OLD_BURN_LOAD, NEW_BURN_LOAD)]
    print('[Fix 1] Cell [4] burnscar filter — OK')
else:
    print('[Fix 1] Cell [4] — pattern NOT FOUND, skipping')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 2 — Cell [6]: tag hotspots by proximity to zones
# ─────────────────────────────────────────────────────────────────────────────
OLD_HOTSPOT_FOOTER = """\
if not hp_today.empty:
    print(f'  ✔ Hotspot วันนี้: {len(hp_today):,} จุด')
    print(f'  FRP: min={hp_today["frp"].min():.1f}  max={hp_today["frp"].max():.1f}  mean={hp_today["frp"].mean():.1f} MW')
    print('  จังหวัดที่พบ (Top 10):')
    print(hp_today['province'].value_counts().head(10).to_string())
    hp_today.to_file(OUT_DIR / 'hotspot_today.geojson', driver='GeoJSON')
else:"""

NEW_HOTSPOT_FOOTER = """\
if not hp_today.empty:
    print(f'  ✔ Hotspot วันนี้: {len(hp_today):,} จุด')
    print(f'  FRP: min={hp_today["frp"].min():.1f}  max={hp_today["frp"].max():.1f}  mean={hp_today["frp"].mean():.1f} MW')
    print('  จังหวัดที่พบ (Top 10):')
    print(hp_today['province'].value_counts().head(10).to_string())

    # ── กรอง hotspot ตามระยะห่างจาก zones (สำหรับ CA simulation) ──────────────
    HOTSPOT_ZONE_DIST_KM = 80.0  # km — hotspot ไกลกว่านี้จากทุก zone ไม่นำมาคำนวณ CA
    hp_today['dist_zone_km'] = hp_today.geometry.apply(
        lambda g: zones_hull_geom.exterior.distance(g) * 111
        if not zones_hull_geom.contains(g) else 0.0
    )
    hp_today['near_zone'] = hp_today['dist_zone_km'] <= HOTSPOT_ZONE_DIST_KM
    n_near = hp_today['near_zone'].sum()
    n_far  = (~hp_today['near_zone']).sum()
    print(f'\\n  ใกล้ zone (<{HOTSPOT_ZONE_DIST_KM:.0f}km): {n_near} จุด  |  ไกล zone: {n_far} จุด')
    hp_today.to_file(OUT_DIR / 'hotspot_today.geojson', driver='GeoJSON')
else:"""

src6 = ''.join(cells[6]['source'])
if OLD_HOTSPOT_FOOTER in src6:
    cells[6]['source'] = [src6.replace(OLD_HOTSPOT_FOOTER, NEW_HOTSPOT_FOOTER)]
    print('[Fix 2] Cell [6] hotspot distance tag — OK')
else:
    print('[Fix 2] Cell [6] — pattern NOT FOUND, skipping')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3 — Cell [22]: use near-zone hotspots for CA, fallback to demo northern
# ─────────────────────────────────────────────────────────────────────────────
OLD_CA_CALL = """\
print(f"🔄 Running Cellular Automaton (24 steps, wind={ws_fc:.1f}m/s @ {wd_fc:.0f}°)...")
prob_ca = cellular_automaton_spread(
    hotspot_df  = hp_today,
    lon_arr     = lon_arr,
    lat_arr     = lat_arr,
    elev_grid   = elev_fine,
    slope_grid  = slope_fine,
    aspect_grid = aspect_fine,
    wind_speed  = ws_fc,
    wind_dir    = wd_fc,
    steps       = 24,
    dt_hr       = 1.0
)
print(f"  ✔ CA probability: max={prob_ca.max():.3f}  mean={prob_ca.mean():.4f}")"""

NEW_CA_CALL = """\
# ── เลือก hotspot ที่ใช้ใน CA: เฉพาะจุดที่ใกล้ zone ──────────────────────────
if 'near_zone' in hp_today.columns:
    hp_for_ca = hp_today[hp_today['near_zone']].copy()
    print(f"  ใช้ {len(hp_for_ca)}/{len(hp_today)} hotspot (ใกล้ zone <80km) สำหรับ CA")
else:
    hp_for_ca = hp_today.copy()

if hp_for_ca.empty:
    print("  ⚠️  ไม่มี hotspot ใกล้ zone → ใช้ demo hotspots พื้นที่ภาคเหนือ")
    demo_pts = [
        (18.79, 98.98, 25.0, 'เชียงใหม่'),
        (18.50, 98.50, 18.0, 'แม่ฮ่องสอน'),
        (19.10, 99.20, 20.0, 'เชียงราย'),
    ]
    hp_for_ca = gpd.GeoDataFrame([{
        'longitude': lon, 'latitude': lat, 'frp': frp, 'province': pv,
        'geometry': Point(lon, lat)
    } for lat, lon, frp, pv in demo_pts], crs='EPSG:4326')

print(f"🔄 Running Cellular Automaton (24 steps, wind={ws_fc:.1f}m/s @ {wd_fc:.0f}°)...")
prob_ca = cellular_automaton_spread(
    hotspot_df  = hp_for_ca,
    lon_arr     = lon_arr,
    lat_arr     = lat_arr,
    elev_grid   = elev_fine,
    slope_grid  = slope_fine,
    aspect_grid = aspect_fine,
    wind_speed  = ws_fc,
    wind_dir    = wd_fc,
    steps       = 24,
    dt_hr       = 1.0
)
print(f"  ✔ CA probability: max={prob_ca.max():.3f}  mean={prob_ca.mean():.4f}")"""

src22 = ''.join(cells[22]['source'])
if OLD_CA_CALL in src22:
    cells[22]['source'] = [src22.replace(OLD_CA_CALL, NEW_CA_CALL)]
    print('[Fix 3] Cell [22] CA near-zone filter — OK')
else:
    print('[Fix 3] Cell [22] — pattern NOT FOUND, skipping')

# ─────────────────────────────────────────────────────────────────────────────
# Write notebook back
# ─────────────────────────────────────────────────────────────────────────────
with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('\n✅ Notebook saved:', NB_PATH)
