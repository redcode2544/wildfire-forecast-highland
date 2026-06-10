"""
Accuracy improvements for wildfire_spread_forecast_ML.ipynb

Changes:
  1. Cell [4]  - Filter T47PPS (centroid lat < 16.5°) from training
  2. Cell [16] - Add month_sin/cos, precip_3day, humidity_norm features
  3. Cell [16] - Pass target_date in prediction call
  4. Cell [18] - Pass target_date to build_grid_features during training
  5. Cell [19] - Better RF: max_depth=8, calibration, 500 trees
  6. Cell [22] - CA: humidity/precip-based fuel moisture factor
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = Path('D:/PuperAI69/wildfire_spread_forecast_ML.ipynb')
with open(NB_PATH, encoding='utf-8') as f:
    nb = json.load(f)
cells = nb['cells']

# ─────────────────────────────────────────────────────────────────────────────
# FIX 1 — Cell [4]: filter burnscar where centroid lat < 16.5° (T47PPS)
# ─────────────────────────────────────────────────────────────────────────────
OLD_BURN_OK = """\
    burnscar_list.append(gdf)
    print(f'  ✅ {shp.name}: {len(gdf):,} polygons | {burn_date} | {area_km2:.1f} km²')"""

NEW_BURN_OK = """\
    # ตรวจ centroid lat: ต้อง >= 16.5° (พื้นที่สูงแท้จริง)
    centroid_lat = gdf.geometry.centroid.y.mean()
    if centroid_lat < 16.5:
        print(f'  ❌ ตัดออก: {shp.name} | centroid lat={centroid_lat:.1f}° < 16.5° (ไม่ใช่พื้นที่สูง)')
        continue

    burnscar_list.append(gdf)
    print(f'  ✅ {shp.name}: {len(gdf):,} polygons | {burn_date} | {area_km2:.1f} km² | centroid lat={centroid_lat:.1f}°')"""

src = ''.join(cells[4]['source'])
if OLD_BURN_OK in src:
    cells[4]['source'] = [src.replace(OLD_BURN_OK, NEW_BURN_OK)]
    print('[Fix 1] Cell[4] centroid lat filter — OK')
else:
    print('[Fix 1] Cell[4] — pattern NOT FOUND')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 2a — Cell [16]: add new features inside build_grid_features
# ─────────────────────────────────────────────────────────────────────────────
OLD_FWI_LINE = "    fwi = simplified_fwi(temp, humidity, wind_speed, precip)"

NEW_FWI_BLOCK = """\
    fwi = simplified_fwi(temp, humidity, wind_speed, precip)

    # ── Seasonal features (fire season: Jan-May peak) ──────────
    if target_date is not None:
        try:
            _m = target_date.month if hasattr(target_date, 'month') else int(str(target_date)[5:7])
        except Exception:
            _m = 3  # default March
    else:
        _m = 3  # default to peak fire season
    month_sin = float(np.sin(2 * np.pi * _m / 12))
    month_cos = float(np.cos(2 * np.pi * _m / 12))

    # ── Recent precipitation (drought indicator, last 3 days) ──
    precip_3day = precip * 3.0  # default: assume consistent
    try:
        if target_date is not None and 'wind_hist_daily' in globals():
            import datetime as _dt
            _d3 = (pd.Timestamp(target_date) - pd.Timedelta(days=3)).date()
            _recent = wind_hist_daily[
                (wind_hist_daily['date'] >= _d3) &
                (wind_hist_daily['date'] < pd.Timestamp(target_date).date()) &
                np.isclose(wind_hist_daily['lat'], WIND_POINTS[0][0])
            ]
            if not _recent.empty:
                precip_3day = float(_recent['precip_sum'].sum())
    except Exception:
        pass

    # humidity_norm: normalised dryness [0=wet, 1=dry]
    humidity_norm = float(np.clip(1.0 - (humidity - 20) / 80, 0.0, 1.0))"""

src = ''.join(cells[16]['source'])
if OLD_FWI_LINE in src:
    cells[16]['source'] = [src.replace(OLD_FWI_LINE, NEW_FWI_BLOCK)]
    print('[Fix 2a] Cell[16] seasonal/drought features — OK')
else:
    print('[Fix 2a] Cell[16] fwi line — pattern NOT FOUND')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 2b — Cell [16]: add new cols to df_feat + update prediction call
# ─────────────────────────────────────────────────────────────────────────────
OLD_DF_FEAT_END = '''\
        # interaction
        "frp_wind":     frp_max * np.clip(w_align, 0, 1),  # FRP × downwind factor
        "frp_slope":    frp_max * slope_factor,
    })

    return df_feat


# ── สร้าง features สำหรับ prediction (hotspots วันนี้) ─────
print("⚙️  สร้าง Feature Matrix สำหรับพยากรณ์...")
today_fc_daily = wind_fc_daily if not wind_fc_daily.empty else pd.DataFrame()

feats_pred = build_grid_features(
    hp_df      = hp_today,
    wind_daily_df = today_fc_daily,
    target_date   = None
)'''

NEW_DF_FEAT_END = '''\
        # interaction
        "frp_wind":     frp_max * np.clip(w_align, 0, 1),  # FRP × downwind factor
        "frp_slope":    frp_max * slope_factor,
        # new: seasonal + drought
        "month_sin":    np.full(len(cell_lats), month_sin),
        "month_cos":    np.full(len(cell_lats), month_cos),
        "precip_3day":  np.full(len(cell_lats), precip_3day),
        "humidity_norm":np.full(len(cell_lats), humidity_norm),
    })

    return df_feat


# ── สร้าง features สำหรับ prediction (hotspots วันนี้) ─────
print("⚙️  สร้าง Feature Matrix สำหรับพยากรณ์...")
today_fc_daily = wind_fc_daily if not wind_fc_daily.empty else pd.DataFrame()

feats_pred = build_grid_features(
    hp_df      = hp_today,
    wind_daily_df = today_fc_daily,
    target_date   = date.today()
)'''

src = ''.join(cells[16]['source'])
if OLD_DF_FEAT_END in src:
    cells[16]['source'] = [src.replace(OLD_DF_FEAT_END, NEW_DF_FEAT_END)]
    print('[Fix 2b] Cell[16] df_feat + target_date today — OK')
else:
    print('[Fix 2b] Cell[16] df_feat end — pattern NOT FOUND')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3 — Cell [18]: pass target_date=d1 to build_grid_features in training
# ─────────────────────────────────────────────────────────────────────────────
OLD_TRAIN_FEAT = """\
    feat_day = build_grid_features(
        hp_df         = gpd.GeoDataFrame(hp_bd,
                         geometry=gpd.points_from_xy(hp_bd["longitude"], hp_bd["latitude"]),
                         crs="EPSG:4326") if hp_bd is not None and not hp_bd.empty else None,
        wind_daily_df = wind_day if wind_day is not None else pd.DataFrame(),
        target_date   = None
    )"""

NEW_TRAIN_FEAT = """\
    feat_day = build_grid_features(
        hp_df         = gpd.GeoDataFrame(hp_bd,
                         geometry=gpd.points_from_xy(hp_bd["longitude"], hp_bd["latitude"]),
                         crs="EPSG:4326") if hp_bd is not None and not hp_bd.empty else None,
        wind_daily_df = wind_day if wind_day is not None else pd.DataFrame(),
        target_date   = d1   # pass date so month_sin/cos and precip_3day are correct
    )"""

src = ''.join(cells[18]['source'])
if OLD_TRAIN_FEAT in src:
    cells[18]['source'] = [src.replace(OLD_TRAIN_FEAT, NEW_TRAIN_FEAT)]
    print('[Fix 3] Cell[18] target_date=d1 — OK')
else:
    print('[Fix 3] Cell[18] — pattern NOT FOUND')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 4 — Cell [19]: better RF + calibration + updated FEATURE_COLS
# ─────────────────────────────────────────────────────────────────────────────
OLD_FEAT_COLS = """\
FEATURE_COLS = [
    "dist_min_km", "frp_max", "frp_sum", "n_hotspot", "wind_align",
    "elevation", "slope", "aspect", "slope_factor", "terrain_wind_align",
    "wind_speed", "wind_gust", "temp", "humidity", "precip", "fwi",
    "frp_wind", "frp_slope"
]"""

NEW_FEAT_COLS = """\
FEATURE_COLS = [
    "dist_min_km", "frp_max", "frp_sum", "n_hotspot", "wind_align",
    "elevation", "slope", "aspect", "slope_factor", "terrain_wind_align",
    "wind_speed", "wind_gust", "temp", "humidity", "precip", "fwi",
    "frp_wind", "frp_slope",
    # new features
    "month_sin", "month_cos", "precip_3day", "humidity_norm",
]"""

OLD_RF_MODEL = """\
# ── Model ──────────────────────────────────────────────────
model = RandomForestClassifier(
    n_estimators  = 300,
    max_depth     = 12,
    min_samples_leaf = 10,
    class_weight  = "balanced",
    random_state  = 42,
    n_jobs        = -1
)

# ── Cross Validation ──────────────────────────────────────
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
print(f"\\n   CV AUC-ROC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# ── Fit full model ─────────────────────────────────────────
model.fit(X, y)
print(f"\\n✅ Model trained! Trees: {model.n_estimators}")"""

NEW_RF_MODEL = """\
from sklearn.calibration import CalibratedClassifierCV

# ── Base RF (tuned for generalization, not just CV fit) ────
_rf_base = RandomForestClassifier(
    n_estimators     = 500,    # more trees → lower variance
    max_depth        = 8,      # shallower → less overfit (was 12)
    min_samples_leaf = 20,     # larger leaf → smoother probabilities
    min_samples_split= 50,
    max_features     = 'sqrt',
    class_weight     = "balanced",
    random_state     = 42,
    n_jobs           = -1
)

# ── Calibration (isotonic regression corrects RF probability bias) ──
model = CalibratedClassifierCV(_rf_base, cv=5, method='isotonic')

# ── Cross Validation (on base RF for speed) ───────────────
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(_rf_base, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
print(f"\\n   CV AUC-ROC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# ── Fit calibrated model (includes training + calibration) ─
model.fit(X, y)
print(f"\\n✅ Model trained + calibrated! (isotonic regression)")"""

src = ''.join(cells[19]['source'])
changed = False
if OLD_FEAT_COLS in src:
    src = src.replace(OLD_FEAT_COLS, NEW_FEAT_COLS)
    changed = True
    print('[Fix 4a] Cell[19] FEATURE_COLS — OK')
else:
    print('[Fix 4a] Cell[19] FEATURE_COLS — NOT FOUND')

if OLD_RF_MODEL in src:
    src = src.replace(OLD_RF_MODEL, NEW_RF_MODEL)
    changed = True
    print('[Fix 4b] Cell[19] RF model tuning + calibration — OK')
else:
    print('[Fix 4b] Cell[19] RF model — NOT FOUND')

if changed:
    cells[19]['source'] = [src]

# ─────────────────────────────────────────────────────────────────────────────
# FIX 5 — Cell [22]: CA humidity/precip fuel moisture factor
# ─────────────────────────────────────────────────────────────────────────────
OLD_CA_WIND = """\
# ── Get wind forecast for next 24h ───────────────────────
if not wind_fc.empty:
    fc_next = wind_fc[
        (wind_fc["time"] >= datetime.now()) &
        (wind_fc["time"] <= datetime.now() + timedelta(hours=24)) &
        np.isclose(wind_fc["lat"], WIND_POINTS[0][0])
    ]
    if not fc_next.empty:
        ws_fc  = fc_next["wind_speed_10m"].mean()
        wd_fc  = fc_next["wind_direction_10m"].mean()
    else:
        ws_fc, wd_fc = 4.0, 315.0
else:
    ws_fc, wd_fc = 4.0, 315.0"""

NEW_CA_WIND = """\
# ── Get wind forecast for next 24h ───────────────────────
if not wind_fc.empty:
    fc_next = wind_fc[
        (wind_fc["time"] >= datetime.now()) &
        (wind_fc["time"] <= datetime.now() + timedelta(hours=24)) &
        np.isclose(wind_fc["lat"], WIND_POINTS[0][0])
    ]
    if not fc_next.empty:
        ws_fc      = fc_next["wind_speed_10m"].mean()
        wd_fc      = fc_next["wind_direction_10m"].mean()
        ca_humidity= fc_next["relative_humidity_2m"].mean() if "relative_humidity_2m" in fc_next else 60.0
        ca_precip  = fc_next["precipitation"].mean() if "precipitation" in fc_next else 0.0
    else:
        ws_fc, wd_fc, ca_humidity, ca_precip = 4.0, 315.0, 60.0, 0.0
else:
    ws_fc, wd_fc, ca_humidity, ca_precip = 4.0, 315.0, 60.0, 0.0"""

OLD_CA_CALL2 = """\
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
)"""

NEW_CA_CALL2 = """\
# Fuel moisture factor: dry (low humidity, no rain) → spreads faster
_fuel_moisture = float(np.clip(1.0 - (ca_humidity - 20) / 80, 0.0, 1.0))
_rain_suppress = float(np.clip(1.0 - ca_precip / 15.0, 0.1, 1.0))
_ca_base_rate  = 0.20 * _fuel_moisture * _rain_suppress   # adjusted base spread rate
print(f"  Fuel moisture factor: {_fuel_moisture:.2f}  Rain suppression: {_rain_suppress:.2f}  CA base rate: {_ca_base_rate:.3f}")

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
    dt_hr       = _ca_base_rate / 0.15  # scale dt to match adjusted base rate
)"""

src = ''.join(cells[22]['source'])
changed22 = False
if OLD_CA_WIND in src:
    src = src.replace(OLD_CA_WIND, NEW_CA_WIND)
    changed22 = True
    print('[Fix 5a] Cell[22] wind forecast humidity/precip — OK')
else:
    print('[Fix 5a] Cell[22] wind fetch — NOT FOUND')

if OLD_CA_CALL2 in src:
    src = src.replace(OLD_CA_CALL2, NEW_CA_CALL2)
    changed22 = True
    print('[Fix 5b] Cell[22] CA fuel moisture factor — OK')
else:
    print('[Fix 5b] Cell[22] CA call — NOT FOUND')

if changed22:
    cells[22]['source'] = [src]

# ─────────────────────────────────────────────────────────────────────────────
with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print('\n✅ Notebook saved:', NB_PATH)
