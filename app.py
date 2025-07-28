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
        [cite_start]"archetype": "英雄、王。意識の中心、エゴ、生命力、目的意識。[cite: 37]",
        [cite_start]"AC": "自己が輝き、自信に満ち溢れ、強い第一印象を与える場所。リーダーシップと自己表現を促進する。[cite: 38]",
        [cite_start]"DC": "自己の可能性を映し出すような、強力で輝かしいパートナーを引き寄せる。人間関係が自己発見の中心となる。[cite: 40]",
        [cite_start]"MC": "キャリアでの成功、社会的名声、野心的な目標の達成に最適。リーダーとして注目される場所。[cite: 41]",
        [cite_start]"IC": "家庭、家族、自身のルーツとの繋がりを通じて、活力と強い自己意識を見出す場所。[cite: 42]"
    },
    "月": {
        [cite_start]"archetype": "母、女王。感情、直感、安心感、大衆、過去。[cite: 44]",
        [cite_start]"AC": "感受性や直感が高まる。他者からは育成力があり、共感的であると見られる場所。[cite: 45]",
        [cite_start]"DC": "育成的な、あるいは感情的なカルマを持つパートナーを引き寄せる。人間関係において深い感情的な安心感を求める。[cite: 46]",
        [cite_start]"MC": "育成的な分野(癒し、食、不動産など)でのキャリア。高い知名度や人気を得るが、公の場での感情的な不安定さも伴う。[cite: 47]",
        [cite_start]"IC": "究極の「故郷」のライン。深い帰属意識、祖先との繋がり、感情的な安心感を得られる場所。[cite: 48]"
    },
    "金星": {
        [cite_start]"archetype": "恋人、芸術家。愛、美、社交性、金銭、価値観。[cite: 56]",
        [cite_start]"AC": "個人的な魅力や求心力が高まる。美しく、芸術的で、社交的に優雅な人物として見られる場所。[cite: 57]",
        [cite_start]"DC": "古典的な「ソウルメイト」または「ハネムーン」のライン。ロマンチックで調和のとれたパートナーを引き寄せる。[cite: 58]",
        [cite_start]"MC": "芸術、デザイン、外交、金融などの分野での成功。人気があり、好感度の高いパブリックイメージ。[cite: 59]",
        [cite_start]"IC": "美しく、調和のとれた快適な家庭を築く。私生活において強い平和と満足感を得られる場所。[cite: 60]"
    },
    "木星": {
        [cite_start]"archetype": "賢者、王。拡大、幸運、成長、知恵、楽観主義。[cite: 69]",
        [cite_start]"AC": "楽観主義、自信、幸運が増大する。寛大でスケールの大きなペルソナ。[cite: 70]",
        [cite_start]"DC": "恩恵をもたらす、賢明な、あるいは外国人のパートナーを引き寄せる。成長と機会が人間関係を通じて訪れる。[cite: 71]",
        [cite_start]"MC": "キャリアの成功、名声、豊かさを得るための最高のライン。職業的な昇進と拡大の機会に恵まれる。[cite: 72]",
        [cite_start]"IC": "広く幸福な家庭。精神的な信念と内面の成長が深まる。不動産や家族に関連して幸運がもたらされる。[cite: 73]"
    },
    # 他の惑星も同様に定義可能
}

# 都道府県と世界の都市リスト
JP_PREFECTURES = {'北海道':(43.06417,141.34694),'青森県':(40.82444,140.74),'岩手県':(39.70361,141.1525),'宮城県':(38.26889,140.87194),'秋田県':(39.71861,140.1025),'山形県':(38.24056,140.36333),'福島県':(37.75,140.46778),'茨城県':(36.34139,140.44667),'栃木県':(36.56583,139.88361),'群馬県':(36.39111,139.06083),'埼玉県':(35.86139,139.64556),'千葉県':(35.60472,140.12333),'東京都':(35.68944,139.69167),'神奈川県':(35.44778,139.6425),'新潟県':(37.90222,139.02361),'富山県':(36.69528,137.21139),'石川県':(36.59444,136.62556),'福井県':(36.06528,136.22194),'山梨県':(35.66389,138.56833),'長野県':(36.65139,138.18111),'岐阜県':(35.42306,136.72222),'静岡県':(34.97694,138.38306),'愛知県':(35.18028,136.90667),'三重県':(34.73028,136.50861),'滋賀県':(35.00444,135.86833),'京都府':(35.02139,135.75556),'大阪府':(34.68639,135.52),'兵庫県':(34.69139,135.18306),'奈良県':(34.68528,135.83278),'和歌山県':(34.22611,135.1675),'鳥取県':(35.50361,134.23833),'島根県':(35.47222,133.05056),'岡山県':(34.66167,133.935),'広島県':(34.39639,132.45944),'山口県':(34.18583,131.47139),'徳島県':(34.06583,134.55944),'香川県':(34.34028,134.04333),'愛媛県':(33.84167,132.76611),'高知県':(33.55972,133.53111),'福岡県':(33.60639,130.41806),'佐賀県':(33.26389,130.30167),'長崎県':(32.74472,129.87361),'熊本県':(32.78972,130.74167),'大分県':(33.23806,131.6125),'宮崎県':(31.91111,131.42389),'鹿児島県':(31.56028,130.55806),'沖縄県':(26.2125,127.68111)}
WORLD_CITIES = {'東京':(35.6895,139.6917),'ロンドン':(51.5074,-0.1278),'ニューヨーク':(40.7128,-74.006),'パリ':(48.8566,2.3522),'シンガポール':(1.3521,103.8198),'香港':(22.3193,114.1694),'シドニー':(-33.8688,151.2093),'ロサンゼルス':(34.0522,-118.2437),'ドバイ':(25.2048,55.2708),'ローマ':(41.9028,12.4964),'カイロ':(30.0444,31.2357),'モスクワ':(55.7558,37.6173),'バンコク':(13.7563,100.5018),'ソウル':(37.5665,126.978),'イスタンブール':(41.0082,28.9784),'シカゴ':(41.8781,-87.6298),'ベルリン':(52.52,13.405),'マドリード':(40.4168,-3.7038),'ホノルル':(21.3069,-157.8583),'サンフランシスコ':(37.7749,-122.4194)}
ALL_CITIES = {**{f"（日本）{k}": v for k, v in JP_PREFECTURES.items()}, **{f"（海外）{k}": v for k, v in WORLD_CITIES.items()}}


# --- キャッシュ ---
@st.cache_resource
def load_ephemeris():
    """天体暦データをロードする（リソースとしてキャッシュ）"""
    return load('de421.bsp')

# --- 計算ロジック ---
def calculate_acg_lines(calculation_dt_utc, selected_planets):
    eph = load_ephemeris()
    earth = eph['earth']
    planet_map = {"太陽":eph['sun'],"月":eph['moon'],"水星":eph['mercury'],"金星":eph['venus'],"火星":eph['mars'],"木星":eph['jupiter barycenter'],"土星":eph['saturn barycenter'],"天王星":eph['uranus barycenter'],"海王星":eph['neptune barycenter'],"冥王星":eph['pluto barycenter']}
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
        lon_mc = np.degrees(ra_rad - gst_rad)
        lon_mc = (lon_mc + 180) % 360 - 180
        lon_ic = (lon_mc + 180 + 180) % 360 - 180
        lines[planet_name] = {"MC": {"lon": lon_mc}, "IC": {"lon": lon_ic}}
        ac_lons, dc_lons, ac_lats, dc_lats = [], [], [], []
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
    eph = load_ephemeris()
    earth = eph['earth']
    planet_map = {"太陽":eph['sun'],"月":eph['moon'],"水星":eph['mercury'],"金星":eph['venus'],"火星":eph['mars'],"木星":eph['jupiter barycenter'],"土星":eph['saturn barycenter'],"天王星":eph['uranus barycenter'],"海王星":eph['neptune barycenter'],"冥王星":eph['pluto barycenter']}
    ts = load.timescale()
    t = ts.from_datetime(birth_dt_utc)
    lines = {}
    for planet_name in selected_planets:
        if planet_name not in planet_map: continue
        planet_obj = planet_map[planet_name]
        observer = earth + center_location
        astrometric = observer.at(t).observe(planet_obj).apparent()
        alt, az, d = astrometric.altaz()
        start_lat, start_lon = center_location.latitude.degrees, center_location.longitude.degrees
        azimuth_rad = az.radians
        lons, lats = [start_lon], [start_lat]
        for dist_km in np.linspace(100, 20000, 100):
            dist_rad = dist_km / 6371
            lat_rad = np.arcsin(np.sin(np.radians(start_lat)) * np.cos(dist_rad) + np.cos(np.radians(start_lat)) * np.sin(dist_rad) * np.cos(azimuth_rad))
            lon_rad = np.radians(start_lon) + np.arctan2(np.sin(azimuth_rad) * np.sin(dist_rad) * np.cos(np.radians(start_lat)), np.cos(dist_rad) - np.sin(np.radians(start_lat)) * np.sin(lat_rad))
            lats.append(np.degrees(lat_rad))
            lons.append(np.degrees(lon_rad))
        lines[planet_name] = {"lons": lons, "lats": lats}
    return lines

def find_cities_in_bands(acg_lines, selected_planets):
    cities_by_planet_angle = {planet: {angle: [] for angle in ["AC", "DC", "IC", "MC"]} for planet in selected_planets}
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
                try:
                    center_lon_at_city_lat = np.interp(city_lat, line_data["lats"], line_data["lons"])
                    lon_diff = abs(city_lon - center_lon_at_city_lat)
                    if min(lon_diff, 360 - lon_diff) <= BAND_WIDTH:
                        cities_by_planet_angle[planet][angle].append(city_name)
                except:
                    continue
    return cities_by_planet_angle

# --- 描画・テキスト生成ロジック ---
def plot_map(lines_data, map_type, selected_planets):
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
                    lons, lats = np.array([lon_val, lon_val], dtype=float), np.array([-85, 85], dtype=float)
                else:
                    lons, lats = np.array(line_data.get("lons", []), dtype=float), np.array(line_data.get("lats", []), dtype=float)
                if len(lons) > 1:
                    jumps = np.where(np.abs(np.diff(lons)) > 180)[0]
                    processed_lons, processed_lats = np.insert(lons, jumps + 1, np.nan), np.insert(lats, jumps + 1, np.nan)
                else:
                    processed_lons, processed_lats = lons, lats
                fig.add_trace(go.Scattergeo(lon=processed_lons, lat=processed_lats, mode='lines', line=dict(width=2, color=color), name=f'{planet_en}-{angle}', hoverinfo='name', connectgaps=False))
        elif map_type == "Local Space":
            line_data = lines_data.get(planet_jp)
            if not line_data: continue
            lons, lats = np.array(line_data.get("lons", []), dtype=float), np.array(line_data.get("lats", []), dtype=float)
            jumps = np.where(np.abs(np.diff(lons)) > 180)[0]
            processed_lons, processed_lats = np.insert(lons, jumps + 1, np.nan), np.insert(lats, jumps + 1, np.nan)
            fig.add_trace(go.Scattergeo(lon=processed_lons, lat=processed_lats, mode='lines', line=dict(width=2, color=color), name=f'{planet_en} Line', hoverinfo='name', connectgaps=False))
    title_text = {"ACG": "アストロカートグラフィー (ACG)", "CCG": "サイクロカートグラフィー (CCG)", "Local Space": "ローカルスペース占星術 (Local Space)"}.get(map_type, "アストロマップ")
    fig.update_layout(title_text=title_text, showlegend=True, geo=dict(projection_type='natural earth', showland=True, landcolor='rgb(243, 243, 243)', showocean=True, oceancolor='rgb(217, 237, 247)', showcountries=True, countrycolor='rgb(204, 204, 204)'), margin={"r":0,"t":40,"l":0,"b":0}, height=600)
    return fig

def format_full_report(birth_info, acg_cities, ccg_cities, transit_date, selected_planets):
    report_lines = ["# アストロマップ総合鑑定レポート", "---", "## 鑑定対象者の情報"]
    report_lines.append(f"- **生年月日**: {birth_info['date']}")
    report_lines.append(f"- **出生時刻**: {birth_info['time']}")
    report_lines.append(f"- **出生地**: {birth_info['loc_name']} (緯度: {birth_info['lat']:.4f}, 経度: {birth_info['lon']:.4f})")
    
    def format_city_list(cities_data, planets):
        lines = []
        if not any(any(cities.values()) for cities in cities_data.values()):
            lines.append("影響範囲内（±5度）にリスト上の主要都市はありませんでした。")
        else:
            for planet in planets:
                if planet in cities_data and any(cities_data[planet].values()):
                    lines.append(f"\n### {planet}")
                    for angle in ["AC", "DC", "MC", "IC"]:
                        cities = cities_data[planet].get(angle, [])
                        if cities:
                            lines.append(f"- **{angle}**: " + ", ".join(sorted(cities)))
        return lines

    report_lines.extend(["\n---\n", "## 1. アストロカートグラフィー (ACG) - 生涯を通じた影響", "影響を受ける主要都市リスト（中心線から±5度の範囲）"])
    report_lines.extend(format_city_list(acg_cities, selected_planets))
    
    report_lines.extend(["\n---\n", f"## 2. サイクロカートグラフィー (CCG) - {transit_date} 時点での影響", "影響を受ける主要都市リスト（中心線から±5度の範囲）"])
    report_lines.extend(format_city_list(ccg_cities, selected_planets))

    report_lines.extend(["\n---\n", "## 3. ローカルスペース占星術 - エネルギーの方位", "ローカルスペースは、特定の場所からの方位のエネルギーを示します。地図上の線は、各惑星のエネルギーが向かう方向を表しており、旅行や移転、インテリアの配置などで活用できます。"])
    
    report_lines.extend(["\n---\n", "## 4. 惑星とアングルの解説"])
    for planet in selected_planets:
        if planet in ARCHETYPE_INFO:
            report_lines.append(f"\n### {planet}")
            info = ARCHETYPE_INFO[planet]
            report_lines.append(f"- **元型**: {info['archetype']}")
            report_lines.append(f"- **AC (自己表現)**: {info['AC']}")
            report_lines.append(f"- **DC (人間関係)**: {info['DC']}")
            report_lines.append(f"- **MC (キャリア)**: {info['MC']}")
            report_lines.append(f"- **IC (家庭・基盤)**: {info['IC']}")
            
    return "\n".join(report_lines)

# --- Streamlit アプリ本体 ---
st.set_page_config(page_title="プロフェッショナル・アストロマップ", page_icon="🗺️", layout="wide")
st.title("プロフェッショナル・アストロマップ 🗺️")

with st.sidebar:
    st.header("⚙️ 設定")
    st.subheader("1. 鑑定対象者の情報")
    birth_date = st.date_input("生年月日", datetime.date(2000, 1, 1), min_value=datetime.date(1930, 1, 1), max_value=datetime.date.today())
    birth_time = st.time_input("出生時刻（24時間表記）", datetime.time(12, 0))
    location_type = st.radio("出生地の指定方法", ["日本の都道府県", "世界の主要都市", "緯度経度を直接入力"], key="loc_type")
    lat, lon, loc_name = None, None, None
    if location_type == "日本の都道府県":
        loc_name = st.selectbox("出生地", list(JP_PREFECTURES.keys()), index=12)
        lat, lon = JP_PREFECTURES[loc_name]
    elif location_type == "世界の主要都市":
        loc_name = st.selectbox("出生地", list(ALL_CITIES.keys()), index=list(ALL_CITIES.keys()).index("（海外）ニューヨーク"))
        lat, lon = ALL_CITIES[loc_name]
    else:
        lat = st.number_input("緯度（北緯が正）", -90.0, 90.0, 35.68, format="%.4f")
        lon = st.number_input("経度（東経が正）", -180.0, 180.0, 139.69, format="%.4f")
        loc_name = f"緯度:{lat}, 経度:{lon}"
    st.subheader("2. 表示設定")
    transit_date = st.date_input("未来予測（CCG）の日付", datetime.date.today())
    available_planets = list(PLANET_INFO.keys())
    default_selections = ["太陽", "月", "金星", "木星"]
    selected_planets = st.multiselect("描画する天体を選択", options=available_planets, default=default_selections)

if st.button('🗺️ すべてのマップと分析結果を生成する', use_container_width=True):
    if not all([birth_date, birth_time, lat is not None, lon is not None]):
        st.error("すべての鑑定情報を正しく入力してください。")
    elif not selected_planets:
        st.error("描画する天体を1つ以上選択してください。")
    else:
        with st.spinner('専門的な天文計算に基づき、すべての分析結果を生成しています...'):
            try:
                birth_dt_local = datetime.datetime.combine(birth_date, birth_time)
                tz_offset_hours = lon / 15.0
                tz_info = datetime.timezone(datetime.timedelta(hours=tz_offset_hours))
                birth_dt_utc = birth_dt_local.replace(tzinfo=tz_info).astimezone(datetime.timezone.utc)
                center_location = Topos(latitude_degrees=lat, longitude_degrees=lon)
                transit_dt_local = datetime.datetime.combine(transit_date, datetime.time(12, 0))
                transit_dt_utc = transit_dt_local.replace(tzinfo=datetime.timezone.utc)

                # --- 1. ACG ---
                st.header("1. アストロカートグラフィー (ACG) - 生涯を通じた影響")
                acg_lines = calculate_acg_lines(birth_dt_utc, selected_planets)
                acg_fig = plot_map(acg_lines, "ACG", selected_planets)
                st.plotly_chart(acg_fig, use_container_width=True)
                acg_cities = find_cities_in_bands(acg_lines, selected_planets)
                # (都市リストのテーブル表示はテキスト出力に集約)

                # --- 2. CCG ---
                st.header(f"2. サイクロカートグラフィー (CCG) - {transit_date} 時点での影響")
                ccg_lines = calculate_acg_lines(transit_dt_utc, selected_planets)
                ccg_fig = plot_map(ccg_lines, "CCG", selected_planets)
                st.plotly_chart(ccg_fig, use_container_width=True)
                ccg_cities = find_cities_in_bands(ccg_lines, selected_planets)

                # --- 3. Local Space ---
                st.header("3. ローカルスペース占星術 - エネルギーの方位")
                local_space_lines = calculate_local_space_lines(birth_dt_utc, center_location, selected_planets)
                ls_fig = plot_map(local_space_lines, "Local Space", selected_planets)
                st.plotly_chart(ls_fig, use_container_width=True)

                # --- 4. 解説 ---
                st.header("4. 惑星とアングルの解説")
                for planet in selected_planets:
                    if planet in ARCHETYPE_INFO:
                        with st.expander(f"**{planet}** の意味と解釈"):
                            info = ARCHETYPE_INFO[planet]
                            st.markdown(f"**元型**: {info['archetype']}")
                            st.markdown(f"**AC (自己表現)**: {info['AC']}")
                            st.markdown(f"**DC (人間関係)**: {info['DC']}")
                            st.markdown(f"**MC (キャリア)**: {info['MC']}")
                            st.markdown(f"**IC (家庭・基盤)**: {info['IC']}")

                # --- 5. 全結果のテキスト出力 ---
                st.divider()
                st.header("📋 全結果のテキスト出力")
                st.info("以下のテキストをコピーして、メモ帳やドキュメントに貼り付けてください。")
                birth_info_dict = {'date': birth_date.strftime('%Y-%m-%d'), 'time': birth_time.strftime('%H:%M'), 'loc_name': loc_name, 'lat': lat, 'lon': lon}
                full_report_text = format_full_report(birth_info_dict, acg_cities, ccg_cities, transit_date, selected_planets)
                st.text_area("鑑定レポート", full_report_text, height=400)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.error("入力データの形式が正しいか、もう一度確認してください。")
