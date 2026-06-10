import json, sys
sys.stdout.reconfigure(encoding='utf-8')

nb_path = 'D:/PuperAI69/wildfire_spread_forecast_ML.ipynb'
with open(nb_path, encoding='utf-8') as f:
    nb = json.load(f)

new_src = r"""# ============================================================
# CELL 19: สร้าง Interactive Folium Map
# ============================================================

import folium
from folium.plugins import HeatMap, MarkerCluster

MAP_CENTER = [18.33, 99.15]
m = folium.Map(location=MAP_CENTER, zoom_start=8,
               tiles="CartoDB positron", control_scale=True)

# ─── Layer 1: Fire Probability Heatmap ─────────────────────
heat_data = []
step_lat = max(1, int(GRID_RES / 0.01))
step_lon = step_lat

for ri in range(0, lat_grid.shape[0], step_lat):
    for ci in range(0, lat_grid.shape[1], step_lon):
        p = float(prob_combined[ri, ci])
        if p > 0.05:
            heat_data.append([float(lat_grid[ri, ci]),
                               float(lon_grid[ri, ci]),
                               p])

HeatMap(
    heat_data,
    name="🔥 Fire Probability Heatmap",
    radius=15, blur=20, max_zoom=12,
    gradient={
        "0.0": "green", "0.3": "yellow",
        "0.5": "orange", "0.7": "red", "1.0": "darkred"
    }
).add_to(m)

# ─── Layer 2: Zone Boundaries (colored by risk) ─────────────
fg_zones = folium.FeatureGroup(name="🏔️ Zones (Risk Color)", show=True)
for _, zrow in proj_risk.iterrows():
    zone_polys = gdf_risk[gdf_risk["PROJECT"] == zrow["PROJECT"]]
    for _, zp in zone_polys.iterrows():
        geom = zp.geometry
        if geom is None: continue

        popup_html = (
            f"<b>{zp['PROJECT']}</b><br>"
            f"ประเภท: {zp['PROJ_TYPE'][:30]}<br>"
            f"ความเสี่ยง: {zp['risk_level']}<br>"
            f"Prob max: {zp['prob_max']:.3f}<br>"
            f"Prob mean: {zp['prob_mean']:.3f}<br>"
            f"พื้นที่เสี่ยงสูง: {zp['high_risk_pct']:.0f}%"
        )

        color = zp["risk_color"]
        folium.GeoJson(
            mapping(geom),
            style_function=lambda feat, c=color: {
                "fillColor": c, "color": "gray",
                "weight": 1, "fillOpacity": 0.4
            },
            tooltip=folium.Tooltip(popup_html)
        ).add_to(fg_zones)

fg_zones.add_to(m)

# ─── Layer 3: Hotspot Markers ───────────────────────────────
fg_hp = folium.FeatureGroup(name="🛰️ Hotspot (Today)", show=True)
if not hp_today.empty:
    cluster = MarkerCluster().add_to(fg_hp)
    for _, row in hp_today.iterrows():
        frp_val = row.get("frp", 0)
        if frp_val > 50: mc = "red"
        elif frp_val > 20: mc = "orange"
        else: mc = "lightred"

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(
                f"<b>Hotspot</b><br>"
                f"จังหวัด: {row.get('province','N/A')}<br>"
                f"FRP: {frp_val:.1f} MW<br>"
                f"การใช้ที่ดิน: {row.get('lu_hp_name','N/A')}<br>"
                f"วันที่: {row.get('acq_date','N/A')}",
                max_width=250
            ),
            icon=folium.Icon(color=mc, icon="fire", prefix="fa")
        ).add_to(cluster)
fg_hp.add_to(m)

# ─── Layer 4: Wind Arrows (shaft + arrowhead) ────────────────
fg_wind = folium.FeatureGroup(name="💨 Wind Direction", show=True)

# wd_fc = "wind FROM" (meteorological) → +180 = ทิศที่ลมพัดไป (fire spreads toward)
arrow_deg = float((wd_fc + 180) % 360)
scale     = 0.30                         # ความยาวลูกศร (degrees)
step      = max(3, int(1.5 / GRID_RES))  # ห่างทุก ~1.5 degree

arrow_dx = float(np.sin(np.radians(arrow_deg)) * scale)
arrow_dy = float(np.cos(np.radians(arrow_deg)) * scale)

for ri in range(0, lat_grid.shape[0], step):
    for ci in range(0, lat_grid.shape[1], step):
        lat_c = float(lat_grid[ri, ci])
        lon_c = float(lon_grid[ri, ci])
        if not (LAT_MIN + 0.8 < lat_c < LAT_MAX - 0.8 and
                LON_MIN + 0.8 < lon_c < LON_MAX - 0.8):
            continue

        end_lat = lat_c + arrow_dy
        end_lon = lon_c + arrow_dx

        # shaft
        folium.PolyLine(
            [[lat_c, lon_c], [end_lat, end_lon]],
            color="#1565C0", weight=2, opacity=0.8
        ).add_to(fg_wind)

        # arrowhead: ▲ rotated by arrow_deg (CSS: 0=up=north, 90=east CW)
        folium.Marker(
            [end_lat, end_lon],
            icon=folium.DivIcon(
                html=(
                    '<div style="'
                    'font-size:14px;'
                    'color:#1565C0;'
                    'transform:rotate(' + str(int(arrow_deg)) + 'deg);'
                    'transform-origin:50% 50%;'
                    'margin:-7px 0 0 -5px;'
                    '">▲</div>'
                ),
                icon_size=(10, 10),
                icon_anchor=(5, 5)
            )
        ).add_to(fg_wind)

fg_wind.add_to(m)

# ─── Legend ─────────────────────────────────────────────────
legend_html = (
    '<div style="position:fixed; bottom:30px; left:30px; z-index:9999;'
    '     background:white; padding:12px; border-radius:8px;'
    '     border:1px solid gray; font-family:Arial; font-size:12px;">'
    '  <b>🔥 Fire Probability</b><br>'
    '  <span style="color:darkred">■</span> &gt; 0.7: สูงมาก<br>'
    '  <span style="color:red">■</span> 0.5–0.7: สูง<br>'
    '  <span style="color:orange">■</span> 0.3–0.5: ปานกลาง<br>'
    '  <span style="color:yellow">■</span> 0.1–0.3: ต่ำ<br>'
    '  <span style="color:green">■</span> &lt; 0.1: ปลอดภัย<br>'
    '  <hr>'
    '  <b>💨 Wind</b> {:.1f} m/s @ {:.0f}°<br>'
    '  <b>📅</b> {}'
    '</div>'
).format(ws_fc, wd_fc, datetime.now().strftime("%Y-%m-%d %H:%M"))

m.get_root().html.add_child(folium.Element(legend_html))

# ─── Layer Control ──────────────────────────────────────────
folium.LayerControl(collapsed=False).add_to(m)

# ─── Save map ───────────────────────────────────────────────
map_path = OUT_DIR / "wildfire_forecast_map.html"
m.save(str(map_path))
print(f"✅ Interactive Map saved → {map_path}")
print("   เปิดไฟล์ .html ใน browser ได้เลย")
"""

nb['cells'][29]['source'] = [new_src]

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Done: cell 29 updated")
print("  - Burned Area layer removed")
print("  - Wind arrows: shaft + arrowhead (▲ rotated to wind direction)")
