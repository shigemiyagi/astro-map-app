import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
from skyfield.api import load, Topos

# --- 定数とデータ ---

# 惑星の英語名、描画色
PLANET_INFO = {
    "太陽": {"en": "Sun", "color": "#FFD700"}, "月": {"en": "Moon", "color": "#C0C0C0"},
    "水星": {"en": "Mercury", "color": "#8B4513"}, "金星": {"en": "Venus", "color": "#FF69B4"},
    "火星": {"en": "Mars", "color": "#FF4500"}, "木星": {"en": "Jupiter", "color": "#32CD32"},
    "土星": {"en": "Saturn", "color": "#4682B4"}, "天王星": {"en": "Uranus", "color": "#00FFFF"},
    "海王星": {"en": "Neptune", "color": "#0000FF"}, "冥王星": {"en": "Pluto", "color": "#800080"},
}

# 惑星とアングルの元型的意味（astrocartography_detail.pdfより引用）
ARCHETYPE_INFO = {
    "太陽": {
        "archetype": "英雄、王。意識の中心、エゴ、生命力、目的意識。[cite: 37]",
        "AC": "自己が輝き、自信に満ち溢れ、強い第一印象を与える場所。リーダーシップと自己表現を促進する。[cite: 38, 39]",
        "DC": "自己の可能性を映し出すような、強力で輝かしいパートナーを引き寄せる。人間関係が自己発見の中心となる。[cite: 40]",
        "MC": "キャリアでの成功、社会的名声、野心的な目標の達成に最適。リーダーとして注目される場所。[cite: 41]",
        "IC": "家庭、家族、自身のルーツとの繋がりを通じて、活力と強い自己意識を見出す場所。[cite: 42]"
    },
    "月": {
        "archetype": "母、女王。感情、直感、安心感、大衆、過去。[cite: 44]",
        "AC": "感受性や直感が高まる。他者からは育成力があり、共感的であると見られる場所。[cite: 45]",
        "DC": "育成的な、あるいは感情的なカルマを持つパートナーを引き寄せる。人間関係において深い感情的な安心感を求める。[cite: 46]",
        "MC": "育成的な分野(癒し、食、不動産など)でのキャリア。高い知名度や人気を得るが、公の場での感情的な不安定さも伴う。[cite: 47]",
        "IC": "究極の「故郷」のライン。深い帰属意識、祖先との繋がり、感情的な安心感を得られる場所。[cite: 48]"
    },
    "金星": {
        "archetype": "恋人、芸術家。愛、美、社交性、金銭、価値観。[cite: 56]",
        "AC": "個人的な魅力や求心力が高まる。美しく、芸術的で、社交的に優雅な人物として見られる場所。[cite: 57]",
        "DC": "古典的な「ソウルメイト」または「ハネムーン」のライン。ロマンチックで調和のとれたパートナーを引き寄せる。[cite: 58]",
        "MC": "芸術、デザイン、外交、金融などの分野での成功。人気があり、好感度の高いパブリックイメージ。[cite: 59]",
        "IC": "美しく、調和のとれた快適な家庭を築く。私生活において強い平和と満足感を得られる場所。[cite: 60]"
    },
    "木星": {
        "archetype": "賢者、王。拡大、幸運、成長、知恵、楽観主義。[cite: 69]",
        "AC": "楽観主義、自信、幸運が増大する。寛大でスケールの大きなペルソナ。[cite: 70]",
        "DC": "恩恵をもたらす、賢明な、あるいは外国人のパートナーを引き寄せる。成長と機会が人間関係を通じて訪れる。[cite: 71]",
        "MC": "キャリアの成功、名声、豊かさを得るための最高のライン。職業的な昇進と拡大の機会に恵まれる。[cite: 72]",
        "IC": "広く幸福な家庭。精神的な信念と内面の成長が深まる。不動産や家族に関連して幸運がもたらされる。[cite: 73]"
    },
    # 他の惑星も同様に定義可能
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
    'ホノルル': (21.3069, -157.8583), 'サンフランシスコ': (37.7749, -122.4194)
    # 必要に応じて都市を追加
}
ALL_CITIES = {**{f"（日本）{k}": v for k, v in JP_PREFECTURES.items()}, **{f"（海外）{k}": v for k, v in WORLD_CITIES.items()}}


# --- キャッシュ ---
@st.cache_resource
def load_ephemeris():
    """天体暦データをロードする（リソースとしてキャッシュ）"""
    return load('de421.bsp')


# --- 計算ロジック ---

def calculate_acg_lines(calculation_dt_utc, selected_planets):
    """アストロカートグラフィー(ACG)のラインを計算する"""
    eph = load_ephemeris()
    earth = eph['earth']
    
    planet_map = {
        "太陽": eph['sun'], "月": eph['moon'], "水星": eph['mercury'],
        "金星": eph['venus'], "火星": eph['mars'], "木星": eph['jupiter barycenter'],
        "土星": eph['saturn barycenter'], "天王星": eph['uranus barycenter'],
        "海王星": eph['neptune barycenter'], "冥王星": eph['pluto barycenter'],
    }

    ts = load.timescale()
    t = ts.from_datetime(calculation_dt_utc)
    
    gst_rad = t.gmst * (np.pi / 12)

    lines = {}
    latitudes = np.linspace(-85, 85, 150)
    
    for planet_name in selected_planets:
        if planet_name not in planet_map: continue
        planet_obj = planet_map[planet_name]
        
        astrometric = earth.at(t).observe(planet_obj)
        ra, dec, distance = astrometric.radec()
        
        ra_rad = ra.radians
        dec_rad = dec.radians

        # MC/IC (経度線)
        lon_mc = np.degrees(ra_rad - gst_rad)
        lon_mc = (lon_mc + 180) % 360 - 180
        lon_ic = (lon_mc + 180 + 180) % 360 - 180
        lines[planet_name] = {"MC": {"lon": lon_mc}, "IC": {"lon": lon_ic}}

        # AC/DC (曲線)
        ac_lons, dc_lons = [], []
        ac_lats, dc_lats = [], []
        
        for lat in latitudes:
            lat_rad = np.radians(lat)
            if abs(lat) >= 90.0: continue
                
            cos_lha_val = -np.tan(dec_rad) * np.tan(lat_rad)
            
            if -1 <= cos_lha_val <= 1:
                lha_rad = np.arccos(cos_lha_val)
                
                lon_ac_rad = ra_rad - lha_rad - gst_rad
                ac_lons.append((np.degrees(lon_ac_rad) + 180) % 360 - 180)
                ac_lats.append(lat)
                
                lon_dc_rad = ra_rad + lha_rad - gst_rad
                dc_lons.append((np.degrees(lon_dc_rad) + 180) % 360 - 180)
                dc_lats.append(lat)

        lines[planet_name]["AC"] = {"lons": ac_lons, "lats": ac_lats}
        lines[planet_name]["DC"] = {"lons": dc_lons, "lats": dc_lats}
        
    return lines


def calculate_local_space_lines(birth_dt_utc, center_location, selected_planets):
    """ローカルスペースのライン（方位線）を計算する"""
    eph = load_ephemeris()
    earth = eph['earth']
    
    planet_map = {
        "太陽": eph['sun'], "月": eph['moon'], "水星": eph['mercury'],
        "金星": eph['venus'], "火星": eph['mars'], "木星": eph['jupiter barycenter'],
        "土星": eph['saturn barycenter'], "天王星": eph['uranus barycenter'],
        "海王星": eph['neptune barycenter'], "冥王星": eph['pluto barycenter'],
    }

    ts = load.timescale()
    t = ts.from_datetime(birth_dt_utc)

    lines = {}
    for planet_name in selected_planets:
        if planet_name not in planet_map: continue
        planet_obj = planet_map[planet_name]

        # 出生地から見た惑星の方位を計算
        observer = earth + center_location
        astrometric = observer.at(t).observe(planet_obj).apparent()
        alt, az, d = astrometric.altaz()
        
        # 大圏航路の計算
        start_lat, start_lon = center_location.latitude.degrees, center_location.longitude.degrees
        azimuth_rad = az.radians
        
        lons, lats = [start_lon], [start_lat]
        # 地球を半周するまでの点をプロット
        for dist_km in np.linspace(100, 20000, 100):
            # 簡易的な球面三角法による計算
            dist_rad = dist_km / 6371 # 地球の半径
            lat_rad = np.arcsin(np.sin(np.radians(start_lat)) * np.cos(dist_rad) +
                                np.cos(np.radians(start_lat)) * np.sin(dist_rad) * np.cos(azimuth_rad))
            lon_rad = np.radians(start_lon) + np.arctan2(np.sin(azimuth_rad) * np.sin(dist_rad) * np.cos(np.radians(start_lat)),
                                                         np.cos(dist_rad) - np.sin(np.radians(start_lat)) * np.sin(lat_rad))
            
            lats.append(np.degrees(lat_rad))
            lons.append(np.degrees(lon_rad))
        
        lines[planet_name] = {"lons": lons, "lats": lats}
        
    return lines


def find_cities_in_bands(acg_lines, selected_planets):
    """影響範囲内（±5度）の都市を探す"""
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
                if not line_data or not line_data.get("lats") or not line_data.get("lons"): continue
                # 緯度が最も近い点の経度で比較
                try:
                    center_lon_at_city_lat = np.interp(city_lat, line_data["lats"], line_data["lons"])
                    lon_diff = abs(city_lon - center_lon_at_city_lat)
                    if min(lon_diff, 360 - lon_diff) <= BAND_WIDTH:
                        cities_by_planet_angle[planet][angle].append(city_name)
                except:
                    continue # 計算エラーはスキップ
    return cities_by_planet_angle

# --- 描画ロジック ---

def plot_map(lines_data, map_type, selected_planets):
    """地図とラインを描画する"""
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lon=[], lat=[], mode='lines', line=dict(width=1, color='gray'), showlegend=False))
    
    for planet_jp in selected_planets:
        if planet_jp not in lines_data: continue
        
        planet_en = PLANET_INFO[planet_jp]["en"]
        color = PLANET_INFO[planet_jp]["color"]

        if map_type in ["ACG", "CCG"]:
            for angle in ["MC", "IC", "AC", "DC"]:
                line_data = lines_data.get(planet_jp, {}).get(angle)
                if not line_data: continue
                if angle in ["MC", "IC"]:
                    lon_val = line_data.get("lon")
                    if lon_val is None: continue
                    lons = np.array([lon_val, lon_val], dtype=float)
                    lats = np.array([-85, 85], dtype=float)
                else: # AC, DC
                    lons = np.array(line_data.get("lons", []), dtype=float)
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

        elif map_type == "Local Space":
            line_data = lines_data.get(planet_jp)
            if not line_data: continue
            lons = np.array(line_data.get("lons", []), dtype=float)
            lats = np.array(line_data.get("lats", []), dtype=float)
            
            # 180度線をまたぐプロットの補正
            jumps = np.where(np.abs(np.diff(lons)) > 180)[0]
            processed_lons = np.insert(lons, jumps + 1, np.nan)
            processed_lats = np.insert(lats, jumps + 1, np.nan)
            
            fig.add_trace(go.Scattergeo(
                lon=processed_lons, lat=processed_lats, mode='lines',
                line=dict(width=2, color=color), name=f'{planet_en} Line',
                hoverinfo='name', connectgaps=False
            ))

    map_title = {
        "ACG": "アストロカートグラフィー (AstroCartoGraphy)",
        "CCG": "サイクロカートグラフィー (CycloCartoGraphy)",
        "Local Space": "ローカルスペース占星術 (Local Space Astrology)"
    }.get(map_type, "アストロマップ")

    fig.update_layout(
        title_text=map_title, showlegend=True,
        geo=dict(
            projection_type='natural earth', showland=True, landcolor='rgb(243, 243, 243)',
            showocean=True, oceancolor='rgb(217, 237, 247)',
            showcountries=True, countrycolor='rgb(204, 204, 204)',
        ),
        margin={"r":0,"t":40,"l":0,"b":0}, height=700
    )
    return fig

# --- Streamlit アプリ本体 ---

st.set_page_config(page_title="プロフェッショナル・アストロマップ", page_icon="🗺️", layout="wide")
st.title("プロフェッショナル・アストロマップ 🗺️")

# --- サイドバー ---
with st.sidebar:
    st.header("⚙️ 設定")

    st.subheader("1. 鑑定対象者の情報")
    birth_date = st.date_input(
        "生年月日", datetime.date(2000, 1, 1),
        min_value=datetime.date(1930, 1, 1),
        max_value=datetime.date.today()
    )
    birth_time = st.time_input("出生時刻（24時間表記）", datetime.time(12, 0))
    
    location_type = st.radio("出生地の指定方法", ["日本の都道府県", "世界の主要都市", "緯度経度を直接入力"], key="loc_type")
    
    lat, lon = None, None
    if location_type == "日本の都道府県":
        pref_name = st.selectbox("出生地", list(JP_PREFECTURES.keys()), index=12)
        lat, lon = JP_PREFECTURES[pref_name]
    elif location_type == "世界の主要都市":
        city_name = st.selectbox("出生地", list(ALL_CITIES.keys()), index=list(ALL_CITIES.keys()).index("（海外）ニューヨーク"))
        lat, lon = ALL_CITIES[city_name]
    else:
        lat = st.number_input("緯度（北緯が正）", -90.0, 90.0, 35.68, format="%.4f")
        lon = st.number_input("経度（東経が正）", -180.0, 180.0, 139.69, format="%.4f")

    st.subheader("2. マップと表示設定")
    map_type = st.selectbox(
        "作成するマップの種類",
        ["アストロカートグラフィー (ACG)", "サイクロカートグラフィー (CCG)", "ローカルスペース占星術 (Local Space)"],
        help="**ACG**: 出生時の影響を見る基本の地図。[cite: 5] **CCG**: 未来の惑星配置（トランジット）の影響を見る地図。 **Local Space**: 出生地からの方位の吉凶を見る地図。"
    )

    transit_date = None
    if map_type == "サイクロカートグラフィー (CCG)":
        transit_date = st.date_input("占いたい未来の日付", datetime.date.today())

    available_planets = list(PLANET_INFO.keys())
    default_selections = ["太陽", "月", "金星", "木星"]
    selected_planets = st.multiselect(
        "描画する天体を選択",
        options=available_planets,
        default=default_selections
    )

# --- メイン画面 ---
if st.button('🗺️ 地図と分析を生成する', use_container_width=True):
    if not all([birth_date, birth_time, lat is not None, lon is not None]):
        st.error("すべての鑑定情報を正しく入力してください。")
    elif not selected_planets:
        st.error("描画する天体を1つ以上選択してください。")
    else:
        with st.spinner('専門的な天文計算に基づき、地図と分析を生成しています...'):
            try:
                # タイムゾーンを考慮してUTCに変換
                birth_dt_local = datetime.datetime.combine(birth_date, birth_time)
                # 経度からタイムゾーンを簡易的に推定
                tz_offset_hours = lon / 15.0
                tz_info = datetime.timezone(datetime.timedelta(hours=tz_offset_hours))
                birth_dt_utc = birth_dt_local.replace(tzinfo=tz_info).astimezone(datetime.timezone.utc)
                
                lines_data = {}
                center_location = Topos(latitude_degrees=lat, longitude_degrees=lon)

                if map_type in ["アストロカートグラフィー (ACG)", "サイクロカートグラフィー (CCG)"]:
                    calc_dt = birth_dt_utc
                    if map_type == "サイクロカートグラフィー (CCG)":
                         # CCGの場合、時刻は正午(UTC)とする
                        calc_dt_local = datetime.datetime.combine(transit_date, datetime.time(12,0))
                        calc_dt = calc_dt_local.replace(tzinfo=datetime.timezone.utc)
                    
                    lines_data = calculate_acg_lines(calc_dt, selected_planets)
                
                elif map_type == "ローカルスペース占星術 (Local Space)":
                    lines_data = calculate_local_space_lines(birth_dt_utc, center_location, selected_planets)

                if not lines_data:
                    st.warning("計算結果が空でした。入力内容を確認してください。")
                else:
                    fig = plot_map(lines_data, map_type.split(" ")[0], selected_planets)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.header("🌠 惑星ラインの解説")
                    st.info("PDF資料に基づき、選択された惑星とアングルが持つ元型的な意味を解説します。[cite: 33]")
                    for planet in selected_planets:
                        if planet in ARCHETYPE_INFO:
                            with st.expander(f"**{planet}** の意味と解釈"):
                                st.markdown(f"**元型**: {ARCHETYPE_INFO[planet]['archetype']}")
                                if map_type.startswith("アストロ") or map_type.startswith("サイクロ"):
                                    st.markdown(f"**AC (自己表現)**: {ARCHETYPE_INFO[planet]['AC']}")
                                    st.markdown(f"**DC (人間関係)**: {ARCHETYPE_INFO[planet]['DC']}")
                                    st.markdown(f"**MC (キャリア)**: {ARCHETYPE_INFO[planet]['MC']}")
                                    st.markdown(f"**IC (家庭・基盤)**: {ARCHETYPE_INFO[planet]['IC']}")
                                else:
                                    st.markdown("ローカルスペース・ラインは、この惑星のエネルギーが向かう方位を示します。その方向に旅行したり、家のその方角を活性化させたりすることで、惑星のテーマが生活にもたらされます。[cite: 117]")


                    if map_type in ["アストロカートグラフィー (ACG)", "サイクロカートグラフィー (CCG)"]:
                        st.header("🏙️ 影響を受ける主要都市リスト（中心線から±5度）")
                        cities_data = find_cities_in_bands(lines_data, selected_planets)
                        
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

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.error("入力データの形式が正しいか、もう一度確認してください。特に、夏時間などの考慮が必要な場合は、時刻を調整してください。")
