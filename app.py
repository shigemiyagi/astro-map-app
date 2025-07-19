import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from collections import defaultdict

# --- 定数とデータ ---

# 星座の開始度数（黄経）
ZODIAC_OFFSETS = {
    "牡羊座": 0, "ARIES": 0, "牡牛座": 30, "TAURUS": 30, "双子座": 60, "GEMINI": 60,
    "蟹座": 90, "CANCER": 90, "獅子座": 120, "LEO": 120, "乙女座": 150, "VIRGO": 150,
    "天秤座": 180, "LIBRA": 180, "蠍座": 210, "SCORPIO": 210, "射手座": 240, "SAGITTARIUS": 240,
    "山羊座": 270, "CAPRICORN": 270, "水瓶座": 300, "AQUARIUS": 300, "魚座": 330, "PISCES": 330,
}

# 惑星の英語名と描画色
PLANET_INFO = {
    "太陽": {"en": "Sun", "color": "#FFD700"}, "月": {"en": "Moon", "color": "#C0C0C0"},
    "水星": {"en": "Mercury", "color": "#8B4513"}, "金星": {"en": "Venus", "color": "#FF69B4"},
    "火星": {"en": "Mars", "color": "#FF4500"}, "木星": {"en": "Jupiter", "color": "#32CD32"},
    "土星": {"en": "Saturn", "color": "#4682B4"}, "天王星": {"en": "Uranus", "color": "#00FFFF"},
    "海王星": {"en": "Neptune", "color": "#0000FF"}, "冥王星": {"en": "Pluto", "color": "#800080"},
}

# 世界の有名都市リスト（緯度経度）
WORLD_CITIES = {
    '東京': (35.6895, 139.6917), 'ロンドン': (51.5074, -0.1278), 'ニューヨーク': (40.7128, -74.0060),
    'パリ': (48.8566, 2.3522), 'シンガポール': (1.3521, 103.8198), '香港': (22.3193, 114.1694),
    'シドニー': (-33.8688, 151.2093), 'ロサンゼルス': (34.0522, -118.2437), 'ドバイ': (25.2048, 55.2708),
    'ローマ': (41.9028, 12.4964), 'カイロ': (30.0444, 31.2357), 'モスクワ': (55.7558, 37.6173),
    'バンコク': (13.7563, 100.5018), 'ソウル': (37.5665, 126.9780), 'イスタンブール': (41.0082, 28.9784),
    'シカゴ': (41.8781, -87.6298), 'ベルリン': (52.5200, 13.4050), 'マドリード': (40.4168, -3.7038),
    'トロント': (43.6532, -79.3832), 'ブエノスアイレス': (-34.6037, -58.3816), 'サンパウロ': (-23.5505, -46.6333),
    'メキシコシティ': (19.4326, -99.1332), 'リオデジャネイロ': (-22.9068, -43.1729), 'ムンバイ': (19.0760, 72.8777),
    'デリー': (28.7041, 77.1025), '上海': (31.2304, 121.4737), '北京': (39.9042, 116.4074),
    'ヨハネスブルグ': (-26.2041, 28.0473), 'アムステルダム': (52.3676, 4.9041), 'ウィーン': (48.2082, 16.3738),
    'チューリッヒ': (47.3769, 8.5417), 'バンクーバー': (49.2827, -123.1207), 'サンフランシスコ': (37.7749, -122.4194),
    'ワシントンD.C.': (38.9072, -77.0369), 'ホノルル': (21.3069, -157.8583), 'アテネ': (37.9838, 23.7275),
    'ダブリン': (53.3498, -6.2603), 'プラハ': (50.0755, 14.4378), 'コペンハーゲン': (55.6761, 12.5683),
    'ストックホルム': (59.3293, 18.0686), 'オスロ': (59.9139, 10.7522), 'ヘルシンキ': (60.1699, 24.9384),
    'リスボン': (38.7223, -9.1393), 'ブリュッセル': (50.8503, 4.3517), 'ワルシャワ': (52.2297, 21.0122),
    'ブダペスト': (47.4979, 19.0402), 'キーウ': (50.4501, 30.5234), 'サンクトペテルブルク': (59.9343, 30.3351),
    '台北': (25.0330, 121.5654), 'クアラルンプール': (3.1390, 101.6869), 'マニラ': (14.5995, 120.9842),
    'ジャカルタ': (-6.2088, 106.8456), 'ハノイ': (21.0285, 105.8542), 'ホーチミン': (10.7769, 106.7009),
    'リヤド': (24.7136, 46.6753), 'アンカラ': (39.9334, 32.8597), 'エルサレム': (31.7683, 35.2137),
    'テヘラン': (35.6892, 51.3890), 'バグダッド': (33.3152, 44.3661), 'ナイロビ': (-1.2921, 36.8219),
    'ラゴス': (6.5244, 3.3792), 'サンティアゴ': (-33.4489, -70.6693), 'リマ': (-12.0464, -77.0428),
    'ボゴタ': (4.7110, -74.0721), 'カラカス': (10.4806, -66.9036), 'キングストン': (17.9712, -76.7930),
    'ハバナ': (23.1136, -82.3666), 'オタワ': (45.4215, -75.6972), 'キャンベラ': (-35.2809, 149.1300),
    'ウェリントン': (-41.2865, 174.7762), 'レイキャビク': (64.1466, -21.9426), 'モンテビデオ': (-34.9011, -56.1645),
    'アスンシオン': (-25.2637, -57.5759), 'キト': (-0.1807, -78.4678), 'パナマシティ': (8.9824, -79.5199),
    '福岡': (33.5904, 130.4017), '札幌': (43.0618, 141.3545), '那覇': (26.2124, 127.6792),
    '釜山': (35.1796, 129.0756), 'グアム': (13.4443, 144.7937), 'オークランド': (-36.8485, 174.7633),
    'メルボルン': (-37.8136, 144.9631), 'パース': (-31.9505, 115.8605), 'デンパサール': (-8.6705, 115.2126),
    'アンカレッジ': (61.2181, -149.9003), 'シアトル': (47.6062, -122.3321),
    'デンバー': (39.7392, -104.9903), 'ヒューストン': (29.7604, -95.3698), 'マイアミ': (25.7617, -80.1918),
    'モントリオール': (45.5017, -73.5673), 'マチュピチュ': (-13.1631, -72.5450), 'イースター島': (-27.1127, -109.3497)
}


# --- 計算関数 (変更なし) ---
def parse_natal_data(text_data):
    planet_data = {}
    lines = text_data.split('\n')
    pattern = re.compile(r"(\S+)\s*:\s*(\S+座)\s*([\d\.]+)\s*度")
    for line in lines:
        match = pattern.search(line)
        if match:
            planet_name_jp = match.group(1).strip()
            if planet_name_jp in PLANET_INFO or planet_name_jp == "MC":
                planet_data[planet_name_jp] = {"sign": match.group(2).strip(), "degree": float(match.group(3))}
    return planet_data

def zodiac_to_longitude(sign, degree):
    return ZODIAC_OFFSETS.get(sign, 0) + degree

def ecliptic_to_equatorial(ecl_lon_deg, obliquity_deg=23.439281):
    ecl_lon_rad = np.radians(ecl_lon_deg)
    obliquity_rad = np.radians(obliquity_deg)
    sin_dec = np.sin(ecl_lon_rad) * np.sin(obliquity_rad)
    dec_rad = np.arcsin(sin_dec)
    cos_ra = np.cos(ecl_lon_rad) / np.cos(dec_rad)
    sin_ra = (np.sin(ecl_lon_rad) * np.cos(obliquity_rad)) / np.cos(dec_rad)
    ra_rad = np.arctan2(sin_ra, cos_ra)
    if ra_rad < 0:
        ra_rad += 2 * np.pi
    return np.degrees(ra_rad), np.degrees(dec_rad)

def calculate_acg_lines(planet_coords, lst_deg):
    lines = {}
    latitudes = np.linspace(-85, 85, 150)
    for planet, coords in planet_coords.items():
        ra_deg, dec_deg = coords["ra"], coords["dec"]
        ra_rad, dec_rad = np.radians(ra_deg), np.radians(dec_deg)
        lst_rad = np.radians(lst_deg)
        
        lon_mc = (ra_deg - lst_deg + 180) % 360 - 180
        lon_ic = (lon_mc + 180 + 180) % 360 - 180
        
        lines[planet] = {"MC": {"lon": lon_mc}, "IC": {"lon": lon_ic}}
        
        ac_lons, dc_lons = [], []
        valid_lats = []
        for lat_deg in latitudes:
            lat_rad = np.radians(lat_deg)
            cos_ha_numerator = -np.tan(dec_rad) * np.tan(lat_rad)
            if abs(cos_ha_numerator) <= 1:
                ha_rad = np.arccos(cos_ha_numerator)
                lon_ac_rad = lst_rad - ra_rad - ha_rad
                lon_dc_rad = lst_rad - ra_rad + ha_rad
                ac_lons.append((np.degrees(lon_ac_rad) + 180) % 360 - 180)
                dc_lons.append((np.degrees(lon_dc_rad) + 180) % 360 - 180)
                valid_lats.append(lat_deg)

        lines[planet]["AC"] = {"lons": ac_lons, "lats": valid_lats}
        lines[planet]["DC"] = {"lons": dc_lons, "lats": valid_lats}
    return lines

def find_cities_in_bands(acg_lines, selected_planets):
    cities_by_planet_angle = {
        planet: {angle: [] for angle in ["AC", "DC", "IC", "MC"]}
        for planet in selected_planets
    }
    BAND_WIDTH = 5.0
    for city_name, (city_lat, city_lon) in WORLD_CITIES.items():
        for planet in selected_planets:
            if planet not in acg_lines: continue
            lines = acg_lines[planet]
            for angle in ["MC", "IC"]:
                line_data = lines.get(angle)
                if not line_data or line_data.get("lon") is None: continue
                center_lon = line_data["lon"]
                lon_diff = abs(city_lon - center_lon)
                if min(lon_diff, 360 - lon_diff) <= BAND_WIDTH:
                    cities_by_planet_angle[planet][angle].append(city_name)
            for angle in ["AC", "DC"]:
                line_data = lines.get(angle)
                if not line_data or not line_data.get("lats"): continue
                center_lon_at_city_lat = np.interp(city_lat, line_data["lats"], line_data["lons"])
                lon_diff = abs(city_lon - center_lon_at_city_lat)
                if min(lon_diff, 360 - lon_diff) <= BAND_WIDTH:
                    cities_by_planet_angle[planet][angle].append(city_name)
    return cities_by_planet_angle

def plot_map_with_lines(acg_lines, selected_planets):
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lon=[], lat=[], mode='lines', line=dict(width=1, color='gray'), showlegend=False))
    for planet_jp in selected_planets:
        if planet_jp not in acg_lines: continue
        planet_en = PLANET_INFO[planet_jp]["en"]
        color = PLANET_INFO[planet_jp]["color"]
        for angle in ["MC", "IC", "AC", "DC"]:
            line_data = acg_lines.get(planet_jp, {}).get(angle)
            if not line_data: continue
            if angle in ["MC", "IC"]:
                lon_val = line_data.get("lon")
                if lon_val is None: continue
                lons = np.array([lon_val, lon_val], dtype=float)
                lats = np.array([-85, 85], dtype=float)
            else:
                lons_list = line_data.get("lons")
                if not lons_list: continue
                lons = np.array(lons_list, dtype=float)
                lats = np.array(line_data.get("lats", []), dtype=float)
            if len(lons) > 1:
                jumps = np.where(np.abs(np.diff(lons)) > 180)[0]
                processed_lons = np.insert(lons, jumps + 1, np.nan)
                processed_lats = np.insert(lats, jumps + 1, np.nan)
            else:
                processed_lons = lons
                processed_lats = lats
            fig.add_trace(go.Scattergeo(
                lon=processed_lons, lat=processed_lats, mode='lines',
                line=dict(width=2, color=color), name=f'{planet_en}-{angle}',
                hoverinfo='name', connectgaps=False
            ))
    fig.update_layout(
        title_text='アストロカートグラフィーマップ', showlegend=True,
        geo=dict(
            projection_type='natural earth', showland=True, landcolor='rgb(243, 243, 243)',
            showocean=True, oceancolor='rgb(217, 237, 247)',
            showcountries=True, countrycolor='rgb(204, 204, 204)',
        ),
        margin={"r":0,"t":40,"l":0,"b":0}, height=600
    )
    return fig

# --- Streamlit アプリ本体 ---
st.set_page_config(layout="wide")
st.title('AstroCartography Map Generator 🗺️')

sample_data = """
🪐 ## ネイタルチャート ##
太陽          : 山羊座   3.64度     (第7ハウス)
月           : 水瓶座  28.81度     (第9ハウス)
水星          : 山羊座  22.60度     (第8ハウス)
金星          : 水瓶座  18.39度     (第9ハウス)
火星          : 射手座  25.00度     (第7ハウス)
木星          : 牡牛座  21.94度 (R) (第12ハウス)
土星          : 獅子座  16.19度 (R) (第3ハウス)
天王星         : 蠍座   10.61度     (第6ハウス)
海王星         : 射手座  14.42度     (第6ハウス)
冥王星         : 天秤座  14.05度     (第5ハウス)
MC          : 魚座    0.81度     (第10ハウス)
"""

st.header("1. ネイタルデータを入力")
user_input = st.text_area("鑑定対象者のネイタルデータを以下に貼り付けてください。", sample_data, height=300)

st.header("2. 描画する天体を選択")
available_planets = list(PLANET_INFO.keys())
default_selections = ["太陽", "月", "金星", "木星"]
selected_planets = st.multiselect(
    "地図に表示したい天体を選択してください。",
    options=available_planets,
    default=default_selections
)

if st.button('🗺️ 地図と都市リストを生成する'):
    if not user_input or not selected_planets:
        st.error("データ入力と天体選択の両方が必要です。")
    else:
        with st.spinner('データを解析し、地図と都市リストを生成しています...'):
            try:
                parsed_data = parse_natal_data(user_input)
                if "MC" not in parsed_data:
                    st.error("エラー: データからMC（天頂）が見つかりませんでした。")
                else:
                    mc_lon = zodiac_to_longitude(parsed_data["MC"]["sign"], parsed_data["MC"]["degree"])
                    lst_deg, _ = ecliptic_to_equatorial(mc_lon)
                    
                    planet_coords = {}
                    for planet, data in parsed_data.items():
                        if planet in PLANET_INFO:
                            ecl_lon = zodiac_to_longitude(data["sign"], data["degree"])
                            ra, dec = ecliptic_to_equatorial(ecl_lon)
                            planet_coords[planet] = {"ra": ra, "dec": dec}

                    acg_lines = calculate_acg_lines(planet_coords, lst_deg)
                    
                    fig = plot_map_with_lines(acg_lines, selected_planets)
                    st.plotly_chart(fig, use_container_width=True)

                    # --- 修正点: 都市リストをHTMLテーブルで表示 ---
                    st.header("🌠 影響を受ける主要都市リスト（中心線から±5度の範囲）")
                    
                    cities_data = find_cities_in_bands(acg_lines, selected_planets)
                    
                    if not any(any(cities.values()) for cities in cities_data.values()):
                         st.info("選択された影響線の近く（±5度）には、リストにある主要都市は含まれていませんでした。")
                    else:
                        df = pd.DataFrame.from_dict(cities_data, orient='index')
                        df = df.reindex(columns=["AC", "DC", "IC", "MC"])
                        
                        # セル内の都市リストをHTMLの改行タグ<br>で連結する
                        def join_cities_html(cities):
                            if isinstance(cities, list) and cities:
                                return "<br>".join(sorted(cities))
                            return ""
                        
                        df = df.applymap(join_cities_html)

                        # Pandas DataFrameをHTMLに変換
                        # escape=Falseにすることで<br>タグがそのままHTMLとして出力される
                        html = df.to_html(escape=False, border=0, classes=["city-table"])

                        # CSSでテーブルのスタイルを定義し、st.markdownで表示
                        st.markdown(
                            f"""
                            <style>
                                .city-table {{
                                    width: 100%;
                                    border-collapse: collapse;
                                }}
                                .city-table th, .city-table td {{
                                    border: 1px solid #e1e1e1;
                                    padding: 8px;
                                    text-align: left;
                                    vertical-align: top;
                                    word-wrap: break-word; /* セル内での改行を強制 */
                                }}
                                .city-table th {{
                                    background-color: #f2f2f2;
                                }}
                            </style>
                            {html}
                            """,
                            unsafe_allow_html=True
                        )

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.error("入力データの形式が正しいか、もう一度確認してください。")
