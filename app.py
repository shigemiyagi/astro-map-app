import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# --- 定数とデータ ---

# 星座の開始度数（黄経）
ZODIAC_OFFSETS = {
    "牡羊座": 0, "ARIES": 0,
    "牡牛座": 30, "TAURUS": 30,
    "双子座": 60, "GEMINI": 60,
    "蟹座": 90, "CANCER": 90,
    "獅子座": 120, "LEO": 120,
    "乙女座": 150, "VIRGO": 150,
    "天秤座": 180, "LIBRA": 180,
    "蠍座": 210, "SCORPIO": 210,
    "射手座": 240, "SAGITTARIUS": 240,
    "山羊座": 270, "CAPRICORN": 270,
    "水瓶座": 300, "AQUARIUS": 300,
    "魚座": 330, "PISCES": 330,
}

# 惑星の英語名と描画色のマッピング
PLANET_INFO = {
    "太陽": {"en": "Sun", "color": "#FFD700"},
    "月": {"en": "Moon", "color": "#C0C0C0"},
    "水星": {"en": "Mercury", "color": "#8B4513"},
    "金星": {"en": "Venus", "color": "#FF69B4"},
    "火星": {"en": "Mars", "color": "#FF4500"},
    "木星": {"en": "Jupiter", "color": "#32CD32"},
    "土星": {"en": "Saturn", "color": "#4682B4"},
    "天王星": {"en": "Uranus", "color": "#00FFFF"},
    "海王星": {"en": "Neptune", "color": "#0000FF"},
    "冥王星": {"en": "Pluto", "color": "#800080"},
    "ASC": {"en": "Ascendant", "color": "#FFA500"},
    "MC": {"en": "Midheaven", "color": "#DC143C"},
}

# --- 計算関数 ---

def parse_natal_data(text_data):
    """テキストから惑星とMCのデータを抽出する"""
    planet_data = {}
    lines = text_data.split('\n')
    # 正規表現パターン: (惑星名) : (星座名) (度数)度
    pattern = re.compile(r"(\S+)\s*:\s*(\S+座)\s*([\d\.]+)\s*度")
    
    for line in lines:
        match = pattern.search(line)
        if match:
            planet_name_jp = match.group(1).strip()
            sign = match.group(2).strip()
            degree = float(match.group(3))
            
            if planet_name_jp in PLANET_INFO or planet_name_jp == "MC":
                planet_data[planet_name_jp] = {"sign": sign, "degree": degree}
    return planet_data

def zodiac_to_longitude(sign, degree):
    """星座と度数から黄経（0-360度）を計算する"""
    return ZODIAC_OFFSETS.get(sign, 0) + degree

def ecliptic_to_equatorial(ecl_lon_deg, obliquity_deg=23.439281):
    """黄経から赤経(RA)と赤緯(Dec)を計算する（簡易版）"""
    ecl_lon_rad = np.radians(ecl_lon_deg)
    obliquity_rad = np.radians(obliquity_deg)
    
    # 赤緯(Dec)の計算
    sin_dec = np.sin(ecl_lon_rad) * np.sin(obliquity_rad)
    dec_rad = np.arcsin(sin_dec)
    
    # 赤経(RA)の計算
    cos_ra = np.cos(ecl_lon_rad) / np.cos(dec_rad)
    sin_ra = (np.sin(ecl_lon_rad) * np.cos(obliquity_rad)) / np.cos(dec_rad)
    ra_rad = np.arctan2(sin_ra, cos_ra)
    
    # 0-2PIの範囲に正規化
    if ra_rad < 0:
        ra_rad += 2 * np.pi
        
    return np.degrees(ra_rad), np.degrees(dec_rad)

def calculate_acg_lines(planet_coords, lst_deg):
    """惑星の座標と恒星時からACGラインを計算する"""
    lines = {}
    latitudes = np.linspace(-70, 70, 100) # 計算する緯度の範囲

    for planet, coords in planet_coords.items():
        ra_deg, dec_deg = coords["ra"], coords["dec"]
        ra_rad, dec_rad = np.radians(ra_deg), np.radians(dec_deg)
        lst_rad = np.radians(lst_deg)
        
        # MC Line (経線)
        lon_mc = ra_deg - lst_deg
        
        # IC Line (経線)
        lon_ic = lon_mc + 180
        
        # 経度を-180から180の範囲に正規化
        lon_mc = (lon_mc + 180) % 360 - 180
        lon_ic = (lon_ic + 180) % 360 - 180
        
        lines[planet] = {
            "MC": {"lon": [lon_mc, lon_mc], "lat": [-90, 90]},
            "IC": {"lon": [lon_ic, lon_ic], "lat": [-90, 90]},
        }
        
        # AC/DC Lines (曲線)
        ac_lons, dc_lons = [], []
        valid_lats = []
        
        for lat_deg in latitudes:
            lat_rad = np.radians(lat_deg)
            # 時角(Hour Angle)を計算
            cos_ha_numerator = -np.tan(dec_rad) * np.tan(lat_rad)
            
            if abs(cos_ha_numerator) <= 1:
                ha_rad = np.arccos(cos_ha_numerator)
                
                # AC/DCの経度を計算
                lon_ac_rad = lst_rad - ra_rad - ha_rad
                lon_dc_rad = lst_rad - ra_rad + ha_rad
                
                ac_lons.append(np.degrees(lon_ac_rad))
                dc_lons.append(np.degrees(lon_dc_rad))
                valid_lats.append(lat_deg)

        # 経度を-180から180の範囲に正規化
        ac_lons_norm = [(lon + 180) % 360 - 180 for lon in ac_lons]
        dc_lons_norm = [(lon + 180) % 360 - 180 for lon in dc_lons]
        
        lines[planet]["AC"] = {"lon": ac_lons_norm, "lat": valid_lats}
        lines[planet]["DC"] = {"lon": dc_lons_norm, "lat": valid_lats}
        
    return lines

# --- 描画関数 ---

def plot_map(acg_lines, selected_planets):
    """Plotlyでインタラクティブな地図を描画する"""
    fig = go.Figure()

    # ベースマップ
    fig.add_trace(go.Scattergeo(
        lon=[],
        lat=[],
        mode='lines',
        line=dict(width=1, color='gray'),
        showlegend=False
    ))

    # 選択された惑星のラインを描画
    for planet_jp in selected_planets:
        if planet_jp not in acg_lines:
            continue
        
        planet_en = PLANET_INFO[planet_jp]["en"]
        color = PLANET_INFO[planet_jp]["color"]
        
        for angle in ["MC", "IC", "AC", "DC"]:
            line_data = acg_lines[planet_jp][angle]
            
            # 経度が日付変更線をまたぐ場合の処理
            lons = np.array(line_data['lon'])
            diffs = np.diff(lons)
            split_indices = np.where(np.abs(diffs) > 180)[0] + 1
            
            lon_segments = np.split(lons, split_indices)
            lat_segments = np.split(np.array(line_data['lat']), split_indices)
            
            for i in range(len(lon_segments)):
                fig.add_trace(go.Scattergeo(
                    lon=lon_segments[i],
                    lat=lat_segments[i],
                    mode='lines',
                    line=dict(width=2, color=color),
                    name=f'{planet_en}-{angle}',
                    hoverinfo='name'
                ))

    fig.update_layout(
        title_text='アストロカートグラフィーマップ',
        showlegend=True,
        geo=dict(
            projection_type='natural earth',
            showland=True, landcolor='rgb(243, 243, 243)',
            showocean=True, oceancolor='rgb(217, 237, 247)',
            showcountries=True, countrycolor='rgb(204, 204, 204)',
            showlakes=True, lakecolor='rgb(217, 237, 247)',
        ),
        margin={"r":0,"t":40,"l":0,"b":0},
        height=600
    )
    return fig

# --- Streamlit アプリ本体 ---

st.set_page_config(layout="wide")
st.title('AstroCartography Map Generator 🗺️')

# サンプルデータ
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
user_input = st.text_area(
    "鑑定対象者のネイタルデータを以下に貼り付けてください。",
    sample_data,
    height=300
)

st.header("2. 描画する天体を選択")
available_planets = list(PLANET_INFO.keys())
# MC/ASCは計算基準なのでデフォルトでは選択しない
default_selections = ["太陽", "月", "金星", "木星"]
selected_planets = st.multiselect(
    "地図に表示したい天体を選択してください。",
    options=available_planets,
    default=default_selections
)

if st.button('🗺️ 地図を描画する'):
    if not user_input:
        st.error("ネイタルデータを入力してください。")
    elif not selected_planets:
        st.error("描画する天体を1つ以上選択してください。")
    else:
        with st.spinner('データを解析し、地図を生成しています...'):
            try:
                # 1. データ解析
                parsed_data = parse_natal_data(user_input)
                
                if "MC" not in parsed_data:
                    st.error("エラー: データからMC（天頂）が見つかりませんでした。計算の基準となるため必須です。")
                else:
                    # 2. 座標計算
                    mc_lon = zodiac_to_longitude(parsed_data["MC"]["sign"], parsed_data["MC"]["degree"])
                    # MCの赤経が地方恒星時(LST)の代わりとなる
                    lst_deg, _ = ecliptic_to_equatorial(mc_lon)
                    
                    planet_coords = {}
                    for planet, data in parsed_data.items():
                        if planet == "MC": continue
                        ecl_lon = zodiac_to_longitude(data["sign"], data["degree"])
                        ra, dec = ecliptic_to_equatorial(ecl_lon)
                        planet_coords[planet] = {"ra": ra, "dec": dec}

                    # 3. ACGライン計算
                    acg_lines = calculate_acg_lines(planet_coords, lst_deg)
                    
                    # 4. 地図描画
                    fig = plot_map(acg_lines, selected_planets)
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.error("入力データの形式が正しいか確認してください。")
