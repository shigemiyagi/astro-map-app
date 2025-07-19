import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from collections import defaultdict
import datetime
import swisseph as swe
import os # 診断機能のためにosライブラリをインポート

# --- 定数とデータ ---

# 星座の開始度数（黄経）
ZODIAC_OFFSETS = {
    "牡羊座": 0, "ARIES": 0, "牡牛座": 30, "TAURUS": 30, "双子座": 60, "GEMINI": 60,
    "蟹座": 90, "CANCER": 90, "獅子座": 120, "LEO": 120, "乙女座": 150, "VIRGO": 150,
    "天秤座": 180, "LIBRA": 180, "蠍座": 210, "SCORPIO": 210, "射手座": 240, "SAGITTARIUS": 240,
    "山羊座": 270, "CAPRICORN": 270, "水瓶座": 300, "AQUARIUS": 300, "魚座": 330, "PISCES": 330,
}

# 惑星の英語名、描画色、およびswissephでのID
PLANET_INFO = {
    "太陽": {"en": "Sun", "color": "#FFD700", "id": swe.SUN},
    "月": {"en": "Moon", "color": "#C0C0C0", "id": swe.MOON},
    "水星": {"en": "Mercury", "color": "#8B4513", "id": swe.MERCURY},
    "金星": {"en": "Venus", "color": "#FF69B4", "id": swe.VENUS},
    "火星": {"en": "Mars", "color": "#FF4500", "id": swe.MARS},
    "木星": {"en": "Jupiter", "color": "#32CD32", "id": swe.JUPITER},
    "土星": {"en": "Saturn", "color": "#4682B4", "id": swe.SATURN},
    "天王星": {"en": "Uranus", "color": "#00FFFF", "id": swe.URANUS},
    "海王星": {"en": "Neptune", "color": "#0000FF", "id": swe.NEPTUNE},
    "冥王星": {"en": "Pluto", "color": "#800080", "id": swe.PLUTO},
}

# 都道府県のリストと県庁所在地の緯度経度
JP_PREFECTURES = {
    '北海道': (43.06417, 141.34694), '青森県': (40.82444, 140.74000), '岩手県': (39.70361, 141.15250),
    '宮城県': (38.26889, 140.87194), '秋田県': (39.71861, 140.10250), '山形県': (38.24056, 140.36333),
    '福島県': (37.75000, 140.46778), '茨城県': (36.34139, 140.44667), '栃木県': (36.56583, 139.88361),
    '群馬県': (36.39111, 139.06083), '埼玉県': (35.86139, 139.64556), '千葉県': (35.60472, 140.12333),
    '東京都': (35.68944, 139.69167), '神奈川県': (35.44778, 139.64250), '新潟県': (37.90222, 139.02361),
    '富山県': (36.69528, 137.21139), '石川県': (36.59444, 136.62556), '福井県': (36.06528, 136.22194),
    '山梨県': (35.66389, 138.56833), '長野県': (36.65139, 138.18111), '岐阜県': (35.42306, 136.72222),
    '静岡県': (34.97694, 138.38306), '愛知県': (35.18028, 136.90667), '三重県': (34.73028, 136.50861),
    '滋賀県': (35.00444, 135.86833), '京都府': (35.02139, 135.75556), '大阪府': (34.68639, 135.52000),
    '兵庫県': (34.69139, 135.18306), '奈良県': (34.68528, 135.83278), '和歌山県': (34.22611, 135.16750),
    '鳥取県': (35.50361, 134.23833), '島根県': (35.47222, 133.05056), '岡山県': (34.66167, 133.93500),
    '広島県': (34.39639, 132.45944), '山口県': (34.18583, 131.47139), '徳島県': (34.06583, 134.55944),
    '香川県': (34.34028, 134.04333), '愛媛県': (33.84167, 132.76611), '高知県': (33.55972, 133.53111),
    '福岡県': (33.60639, 130.41806), '佐賀県': (33.26389, 130.30167), '長崎県': (32.74472, 129.87361),
    '熊本県': (32.78972, 130.74167), '大分県': (33.23806, 131.61250), '宮崎県': (31.91111, 131.42389),
    '鹿児島県': (31.56028, 130.55806), '沖縄県': (26.21250, 127.68111)
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


# --- 新しい計算ロジック ---

def calculate_acg_lines_with_swisseph(birth_dt_jst, selected_planets):
    swe.set_ephe_path('./ephe')
    
    birth_dt_utc = birth_dt_jst - datetime.timedelta(hours=9)
    
    jd_utc, ret = swe.utc_to_jd(
        birth_dt_utc.year, birth_dt_utc.month, birth_dt_utc.day,
        birth_dt_utc.hour, birth_dt_utc.minute, birth_dt_utc.second,
        swe.GREG_CAL
    )
    if ret != 0:
        st.error("日付の変換に失敗しました。天体暦ファイルが'ephe'フォルダに正しく配置されているか確認してください。")
        return {}

    lines = {}
    latitudes = np.linspace(-85, 85, 150)
    
    planet_id_map = {p_info["id"]: p_name for p_name, p_info in PLANET_INFO.items() if p_name in selected_planets}
    
    calc_flags = swe.FLG_SWIEPH

    for planet_id, planet_name in planet_id_map.items():
        ac_lons, dc_lons = [], []
        ac_lats, dc_lats = [], []

        res, lon_mc_arr, ret = swe.acg_pos(jd_utc, planet_id, 0, 0, swe.MC | calc_flags, 0)
        lon_mc = lon_mc_arr[0] if isinstance(lon_mc_arr, (list, tuple)) else lon_mc_arr
        
        res, lon_ic_arr, ret = swe.acg_pos(jd_utc, planet_id, 0, 0, swe.IC | calc_flags, 0)
        lon_ic = lon_ic_arr[0] if isinstance(lon_ic_arr, (list, tuple)) else lon_ic_arr

        lines[planet_name] = {"MC": {"lon": lon_mc}, "IC": {"lon": lon_ic}}

        for lat in latitudes:
            res_ac, lon_ac_arr, ret_ac = swe.acg_pos(jd_utc, planet_id, lat, 0, swe.RISE | calc_flags, 0)
            if res_ac == 0:
                lon_ac = lon_ac_arr[0] if isinstance(lon_ac_arr, (list, tuple)) else lon_ac_arr
                ac_lons.append(lon_ac)
                ac_lats.append(lat)
            
            res_dc, lon_dc_arr, ret_dc = swe.acg_pos(jd_utc, planet_id, lat, 0, swe.SET | calc_flags, 0)
            if res_dc == 0:
                lon_dc = lon_dc_arr[0] if isinstance(lon_dc_arr, (list, tuple)) else lon_dc_arr
                dc_lons.append(lon_dc)
                dc_lats.append(lat)
        
        ac_lons_norm = [(lon + 180) % 360 - 180 for lon in ac_lons]
        dc_lons_norm = [(lon + 180) % 360 - 180 for lon in dc_lons]

        lines[planet_name]["AC"] = {"lons": ac_lons_norm, "lats": ac_lats}
        lines[planet_name]["DC"] = {"lons": dc_lons_norm, "lats": dc_lats}
    
    swe.close()
    return lines


# --- 変更なし (以降の関数) ---

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

def format_data_as_markdown(cities_data):
    final_blocks = ["# アストロカートグラフィーで影響を受ける主要都市リスト"]
    for planet in PLANET_INFO.keys():
        if planet in cities_data:
            planet_data = cities_data[planet]
            if any(planet_data.values()):
                planet_section = [f"## {planet}"]
                for angle in ["AC", "DC", "IC", "MC"]:
                    cities = planet_data.get(angle, [])
                    if cities:
                        planet_section.append(f"### {angle}")
                        planet_section.append(", ".join(sorted(cities)))
                final_blocks.append("\n".join(planet_section))
    return "\n\n".join(final_blocks)

# --- Streamlit アプリ本体 ---
st.set_page_config(layout="wide")
st.title('AstroCartography Map Generator 🗺️')

st.header("1. 鑑定対象者の情報を入力")

col1, col2, col3 = st.columns(3)
with col1:
    birth_date = st.date_input(
        "生年月日", datetime.date(2000, 1, 1),
        min_value=datetime.date(1930, 1, 1),
        max_value=datetime.date.today()
    )
with col2:
    birth_time = st.time_input("出生時刻", datetime.time(12, 0))
with col3:
    pref_name = st.selectbox("出生地（都道府県）", list(JP_PREFECTURES.keys()), index=12)

st.header("2. 描画する天体を選択")
available_planets = list(PLANET_INFO.keys())
default_selections = ["太陽", "月", "金星", "木星"]
selected_planets = st.multiselect(
    "地図に表示したい天体を選択してください。",
    options=available_planets,
    default=default_selections
)

if st.button('🗺️ 地図と都市リストを生成する'):
    if not all([birth_date, birth_time, pref_name]):
        st.error("すべての鑑定情報を入力してください。")
    else:
        with st.spinner('正確な天文計算に基づき、地図と都市リストを生成しています...'):
            try:
                # --- 修正点: 診断機能を追加 ---
                ephe_dir = './ephe'
                with st.expander("ファイルチェック（デバッグ用）"):
                    st.write(f"天体暦データフォルダ '{ephe_dir}' の状態を確認します...")
                    if os.path.isdir(ephe_dir):
                        st.success(f"✅ フォルダ '{ephe_dir}' が見つかりました。")
                        files_in_dir = os.listdir(ephe_dir)
                        if files_in_dir:
                            st.write("フォルダ内のファイル:")
                            st.code('\n'.join(files_in_dir))
                            if 'seas_18.se1' in files_in_dir:
                                st.success("✅ 主要な天体暦ファイルが見つかりました。")
                            else:
                                st.error("🚨 主要な天体暦ファイル ('seas_18.se1' など) が見つかりません。")
                        else:
                            st.error(f"🚨 フォルダ '{ephe_dir}' は空です。")
                    else:
                        st.error(f"🚨 フォルダ '{ephe_dir}' が見つかりません。GitHubリポジトリにフォルダを追加してアップロードしてください。")
                # --- 診断機能ここまで ---

                birth_dt_jst = datetime.datetime.combine(birth_date, birth_time)
                
                acg_lines = calculate_acg_lines_with_swisseph(birth_dt_jst, selected_planets)
                
                if not acg_lines:
                    st.warning("計算結果が空でした。エラーメッセージを確認するか、別の入力でお試しください。")
                else:
                    fig = plot_map_with_lines(acg_lines, selected_planets)
                    st.plotly_chart(fig, use_container_width=True)

                    st.header("🌠 影響を受ける主要都市リスト（中心線から±5度の範囲）")
                    cities_data = find_cities_in_bands(acg_lines, selected_planets)
                    
                    if not any(any(cities.values()) for cities in cities_data.values()):
                         st.info("選択された影響線の近く（±5度）には、リストにある主要都市は含まれていませんでした。")
                    else:
                        df = pd.DataFrame.from_dict(cities_data, orient='index')
                        df = df.reindex(columns=["AC", "DC", "IC", "MC"])
                        def join_cities_html(cities):
                            if isinstance(cities, list) and cities:
                                return "<br>".join(sorted(cities))
                            return ""
                        df_html = df.applymap(join_cities_html)
                        html_table = df_html.to_html(escape=False, index=True, border=0, header=True)
                        st.markdown("""<style>
                            table.dataframe { width: 100% !important; border-collapse: collapse; }
                            table.dataframe th, table.dataframe td { border: 1px solid #e1e1e1; padding: 8px; text-align: left; vertical-align: top; white-space: normal; word-wrap: break-word; }
                            table.dataframe th { background-color: #f2f2f2; }
                        </style>""", unsafe_allow_html=True)
                        st.markdown(html_table, unsafe_allow_html=True)

                        st.divider()
                        st.subheader("📋 マークダウン形式でコピー")
                        markdown_text = format_data_as_markdown(cities_data)
                        st.text_area(
                            "以下のテキストをコピーして、メモ帳やドキュメントに貼り付けてください。",
                            markdown_text,
                            height=300
                        )

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.error("入力データの形式が正しいか、もう一度確認してください。")
