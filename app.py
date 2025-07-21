import streamlit as st
import swisseph as swe
import datetime
from datetime import timezone, timedelta
import math
import traceback
import pandas as pd
import altair as alt
from collections import defaultdict

# --- 初期設定 ---
APP_VERSION = "8.1 (計算ロジック改善版)"
swe.set_ephe_path('ephe')

# --- 定数定義 (変更なし、内容は省略) ---
PLANET_IDS = {
    "太陽": swe.SUN, "月": swe.MOON, "水星": swe.MERCURY, "金星": swe.VENUS, "火星": swe.MARS,
    "木星": swe.JUPITER, "土星": swe.SATURN, "天王星": swe.URANUS, "海王星": swe.NEPTUNE, "冥王星": swe.PLUTO,
}
MAJOR_ASPECTS = { 0: '合', 60: 'セクスタイル', 90: 'スクエア', 120: 'トライン', 180: 'オポジション' }
GOOD_ASPECTS = { 0: '合', 60: 'セクスタイル', 120: 'トライン' }
ORB = 1.2
ZODIAC_SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
    "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"
]
RULER_OF_SIGN = {
    "牡羊座": "火星", "牡牛座": "金星", "双子座": "水星", "蟹座": "月", "獅子座": "太陽",
    "乙女座": "水星", "天秤座": "金星", "蠍座": "火星", "射手座": "木星", "山羊座": "土星",
    "水瓶座": "土星", "魚座": "木星"
}
EVENT_DEFINITIONS = {
    "T_JUP_7H_INGRESS": {"score": 95, "title": "T木星が第7ハウス入り", "desc": "約12年に一度の最大の結婚幸運期。出会いのチャンスが拡大し、関係がスムーズに進展しやすい1年間。"},
    "T_SAT_7H_INGRESS": {"score": 90, "title": "T土星が第7ハウス入り", "desc": "パートナーシップに対する責任感が生まれ、関係を真剣に考える時期。結婚を固めるタイミング。"},
    "T_JUP_CONJ_DSC": {"score": 90, "title": "T木星とNディセンダントが合", "desc": "素晴らしいパートナーとの出会いや、現在の関係が結婚へと発展する絶好のチャンス。"},
    "T_JUP_ASPECT_VENUS": {"score": 80, "title": "T木星がN金星に吉角", "desc": "恋愛運が最高潮に。人生を楽しむ喜びにあふれ、幸せな恋愛・結婚に繋がりやすい。"},
    "T_JUP_ASPECT_SUN": {"score": 75, "title": "T木星がN太陽に吉角", "desc": "人生の発展期。自己肯定感が高まり、良きパートナーを引き寄せ、人生のステージが上がる。"},
    "T_SAT_CONJ_DSC": {"score": 85, "title": "T土星とNディセンダントが合", "desc": "運命的な相手との関係が始まり、長期的な契約を結ぶ時。結婚への決意が固まる。"},
    "T_SAT_ASPECT_VENUS": {"score": 70, "title": "T土星がN金星にアスペクト", "desc": "恋愛関係に試練や責任が伴うが、それを乗り越えることで関係が安定し、真剣なものへと進む。結婚への覚悟を固める時期。"},
    "T_URA_ASPECT_VENUS": {"score": 75, "title": "T天王星がN金星にアスペクト", "desc": "突然の出会いや電撃的な恋愛、または現在の関係に変化が訪れる。今までにないタイプの人に強く惹かれ、関係性が大きく動く可能性。"},
    "SA_ASC_CONJ_VENUS": {"score": 90, "title": "SA ASCがN金星に合", "desc": "自分自身が愛のエネルギーに満ち、魅力が高まる時期。恋愛や結婚の大きなチャンス。"},
    "SA_MC_CONJ_VENUS": {"score": 85, "title": "SA MCがN金星に合", "desc": "恋愛や結婚が社会的なステータスアップに繋がる可能性。公に認められる喜び。"},
    "SA_VENUS_CONJ_ASC": {"score": 88, "title": "SA金星がN ASCに合", "desc": "愛される喜びを実感する時。人生の新しい扉が開き、パートナーシップが始まる。"},
    "SA_JUP_CONJ_ASC": {"score": 85, "title": "SA木星がN ASCに合", "desc": "人生における大きな幸運期。拡大と発展のエネルギーが自分に降り注ぐ。"},
    "SA_7Ruler_CONJ_ASC_DSC": {"score": 95, "title": "SA 7H支配星がN ASC/DSCに合", "desc": "結婚の運命を司る星が「自分」か「パートナー」の感受点に重なる、極めて重要な時期。"},
    "P_MOON_7H_INGRESS": {"score": 80, "title": "P月が第7ハウス入り", "desc": "約2.5年間、結婚やパートナーへの意識が自然と高まる。心がパートナーを求める時期。"},
    "P_MOON_CONJ_JUP": {"score": 70, "title": "P月がN木星に合", "desc": "精神的に満たされ、幸福感が高まる。楽観的な気持ちが良縁を引き寄せる。"},
    "P_MOON_CONJ_VENUS": {"score": 75, "title": "P月がN金星に合", "desc": "恋愛気分が盛り上がり、ときめきを感じやすい。デートや出会いに最適なタイミング。"},
    "P_VENUS_ASPECT_MARS": {"score": 80, "title": "P金星がN火星にアスペクト", "desc": "愛情と情熱が結びつき、ロマンスが燃え上がる強力な配置。関係が急速に進展しやすい。"}
}
PREFECTURES = {
    "北海道": (141.35, 43.06), "青森県": (140.74, 40.82), "岩手県": (141.15, 39.70),
    "宮城県": (140.87, 38.27), "秋田県": (140.10, 39.72), "山形県": (140.36, 38.24),
    "福島県": (140.47, 37.75), "茨城県": (140.45, 36.34), "栃木県": (139.88, 36.57),
    "群馬県": (139.06, 36.39), "埼玉県": (139.65, 35.86), "千葉県": (140.12, 35.60),
    "東京都": (139.69, 35.69), "神奈川県": (139.64, 35.45), "新潟県": (139.02, 37.90),
    "富山県": (137.21, 36.70), "石川県": (136.63, 36.59), "福井県": (136.07, 36.07),
    "山梨県": (138.57, 35.66), "長野県": (138.18, 36.65), "岐阜県": (136.72, 35.39),
    "静岡県": (138.38, 34.98), "愛知県": (136.91, 35.18), "三重県": (136.51, 34.73),
    "滋賀県": (135.87, 35.00), "京都府": (135.76, 35.02), "大阪府": (135.52, 34.69),
    "兵庫県": (135.18, 34.69), "奈良県": (135.83, 34.69), "和歌山県": (135.17, 34.23),
    "鳥取県": (134.24, 35.50), "島根県": (133.05, 35.47), "岡山県": (133.93, 34.66),
    "広島県": (132.46, 34.40), "山口県": (131.47, 34.19), "徳島県": (134.55, 34.07),
    "香川県": (134.04, 34.34), "愛媛県": (132.77, 33.84), "高知県": (133.53, 33.56),
    "福岡県": (130.42, 33.61), "佐賀県": (130.30, 33.26), "長崎県": (129.88, 32.75),
    "熊本県": (130.74, 32.79), "大分県": (131.61, 33.24), "宮崎県": (131.42, 31.91),
    "鹿児島県": (130.56, 31.56), "沖縄県": (127.68, 26.21)
}


# --- 計算ロジック関数 ---

def get_natal_chart(birth_dt_jst, lon, lat):
    # (変更なし)
    dt_utc = birth_dt_jst.astimezone(timezone.utc)
    year, month, day, hour, minute = dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute
    second = float(dt_utc.second)
    jday = swe.utc_to_jd(year, month, day, hour, minute, second, 1)[1]

    chart_data = {"jday": jday, "lon": lon, "lat": lat}
    
    cusps, ascmc = swe.houses(jday, lat, lon, b'P')
    if not isinstance(cusps, tuple):
        st.error("ハウス計算に失敗しました。出生時刻や場所が有効か確認してください。")
        return None
        
    chart_data["ASC_pos"] = float(ascmc[0])
    chart_data["MC_pos"] = float(ascmc[1])
    
    temp_planet_ids = PLANET_IDS.copy()
    temp_planet_ids.update({"ASC": swe.ASC, "MC": swe.MC})
    
    for name, pid in temp_planet_ids.items():
        if name in ["ASC", "MC"]:
            chart_data[name] = chart_data[f"{name}_pos"]
        else:
             chart_data[name] = float(swe.calc_ut(jday, pid)[0][0])

    chart_data["DSC_pos"] = (chart_data["ASC_pos"] + 180) % 360
    chart_data["IC_pos"] = (chart_data["MC_pos"] + 180) % 360
    chart_data["cusps"] = cusps

    dsc_sign_index = int(chart_data["DSC_pos"] / 30)
    dsc_sign = ZODIAC_SIGNS[dsc_sign_index]
    ruler_name = RULER_OF_SIGN[dsc_sign]
    chart_data["7H_RulerName"] = ruler_name
    chart_data["7H_Ruler_pos"] = chart_data.get(ruler_name)
    
    return chart_data

def calculate_midpoint(p1, p2):
    diff = (p2 - p1 + 360) % 360
    midpoint = (p1 + diff / 2) % 360 if diff <= 180 else (p2 + (360 - diff) / 2) % 360
    return midpoint

def create_composite_chart(chart_a, chart_b):
    composite_chart = {"lon": chart_a["lon"], "lat": chart_a["lat"]}
    
    for name in PLANET_IDS.keys():
        composite_chart[name] = calculate_midpoint(chart_a[name], chart_b[name])

    composite_chart["ASC_pos"] = calculate_midpoint(chart_a["ASC_pos"], chart_b["ASC_pos"])
    composite_chart["MC_pos"] = calculate_midpoint(chart_a["MC_pos"], chart_b["MC_pos"])
    
    composite_chart["cusps"] = tuple([(composite_chart["ASC_pos"] + 30 * i) % 360 for i in range(12)])
    composite_chart["DSC_pos"] = (composite_chart["ASC_pos"] + 180) % 360
    
    # ▼▼▼ 修正点 ▼▼▼
    # 計算の基準となるjdayと太陽の位置をチャートデータに含める
    composite_chart["jday"] = chart_a["jday"]
    composite_chart["太陽"] = composite_chart.get("太陽")
    
    composite_chart["7H_RulerName"] = None
    composite_chart["7H_Ruler_pos"] = None
    
    return composite_chart

# ▼▼▼ 全面的にリファクタリングした関数 ▼▼▼
# @st.cache_data
def find_events(_natal_chart, birth_dt, years=80, is_composite=False):
    events_by_date = {}
    t_planets = ["木星", "土星", "天王星"]
    p_planets = ["月", "金星"]
    
    sa_points = ["ASC_pos", "MC_pos", "金星", "木星"] if is_composite else ["ASC_pos", "MC_pos", "金星", "木星", "7H_Ruler_pos"]

    # 基準となるユリウス日と太陽の位置をチャートデータから取得
    base_jday = _natal_chart["jday"]
    natal_sun_pos = _natal_chart["太陽"]

    prev_positions = {}

    for day_offset in range(1, int(365.25 * years)):
        current_date = birth_dt + timedelta(days=day_offset)

        # --- 計算ロジックをシンプルに統一 ---
        current_jday = base_jday + day_offset
        p_jday = base_jday + day_offset / 365.25

        t_pos = {p: float(swe.calc_ut(current_jday, PLANET_IDS[p])[0][0]) for p in t_planets}
        p_pos = {p: float(swe.calc_ut(p_jday, PLANET_IDS[p])[0][0]) for p in p_planets}
        sa_arc = float(swe.calc_ut(p_jday, swe.SUN)[0][0]) - natal_sun_pos
        sa_pos = {p: (_natal_chart.get(p, 0) + sa_arc) % 360 for p in sa_points if p in _natal_chart and _natal_chart.get(p) is not None}

        if not prev_positions:
            prev_positions = {'t': t_pos, 'p': p_pos, 'sa': sa_pos}
            continue
        
        # --- イベント発生をチェック (ヘルパー関数) ---
        def check_crossing(current_pos, prev_pos, target_pos, orb):
            dist_curr = (current_pos - target_pos + 180) % 360 - 180
            dist_prev = (prev_pos - target_pos + 180) % 360 - 180
            if abs(dist_curr) <= orb and abs(dist_prev) > orb and abs(dist_prev - dist_curr) < (orb * 5): return True
            if dist_prev * dist_curr < 0 and abs(dist_prev - dist_curr) < (orb * 5): return True
            return False

        def check_ingress(current_pos, prev_pos, cusp_pos):
            norm_curr = (current_pos - cusp_pos + 360) % 360
            norm_prev = (prev_pos - cusp_pos + 360) % 360
            if norm_prev > 350 and norm_curr < 10: return True
            return False

        # --- チェックロジック本体 (変更なし) ---
        if check_ingress(t_pos["木星"], prev_positions['t']["木星"], _natal_chart["cusps"][6]): events_by_date.setdefault(current_date.date(), []).append("T_JUP_7H_INGRESS")
        if check_ingress(p_pos["月"], prev_positions['p']["月"], _natal_chart["cusps"][6]): events_by_date.setdefault(current_date.date(), []).append("P_MOON_7H_INGRESS")
        if check_crossing(t_pos["木星"], prev_positions['t']["木星"], _natal_chart["DSC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("T_JUP_CONJ_DSC")
        # ...(他の多数のチェックロジックは変更ないため省略)...

        if not is_composite and "7H_Ruler_pos" in sa_pos:
            if check_crossing(sa_pos["7H_Ruler_pos"], prev_positions['sa'].get("7H_Ruler_pos", 0), _natal_chart["ASC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_7Ruler_CONJ_ASC_DSC")
            if check_crossing(sa_pos["7H_Ruler_pos"], prev_positions['sa'].get("7H_Ruler_pos", 0), _natal_chart["DSC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_7Ruler_CONJ_ASC_DSC")
        
        prev_positions = {'t': t_pos, 'p': p_pos, 'sa': sa_pos}
        
    # --- スコアリングとソート (変更なし) ---
    scored_events = []
    for date, event_keys in events_by_date.items():
        unique_keys = list(set(event_keys))
        total_score = sum(EVENT_DEFINITIONS[key]["score"] for key in unique_keys)
        scored_events.append({"date": date, "score": total_score, "keys": unique_keys})
    
    if not scored_events: return []
    max_score = max(event["score"] for event in scored_events) if scored_events else 0
    if max_score > 0:
        for event in scored_events:
            event["normalized_score"] = (event["score"] / max_score) * 100
    return sorted(scored_events, key=lambda x: x["score"], reverse=True)


def synthesize_couple_events(events_a, events_b, events_comp):
    # (変更なし)
    monthly_scores = defaultdict(lambda: {'score': 0, 'events': defaultdict(list)})
    all_event_lists = {'Aさん': events_a, 'Bさん': events_b, 'お二人の関係性': events_comp}
    for person, event_list in all_event_lists.items():
        for event in event_list:
            month_key = event['date'].strftime('%Y-%m')
            monthly_scores[month_key]['score'] += event.get('normalized_score', 0)
            monthly_scores[month_key]['events'][person].extend(event['keys'])
    if not monthly_scores: return []
    max_combined_score = max(data['score'] for data in monthly_scores.values())
    final_events = []
    for month_str, data in monthly_scores.items():
        if data['score'] > 0:
            final_events.append({
                "month": month_str, "score": data['score'],
                "normalized_score": (data['score'] / max_combined_score) * 100,
                "events_detail": data['events']
            })
    return sorted(final_events, key=lambda x: x['score'], reverse=True)


# --- Streamlit UI (変更なし、内容は省略) ---
st.set_page_config(page_title="結婚タイミング占い【PRO】", page_icon="💖")
st.title("💖 結婚タイミング占い【PRO版】")
st.info(f"アプリバージョン: {APP_VERSION}")
st.sidebar.title("モード選択")
mode = st.sidebar.radio("鑑定する人数を選んでください", ("1人用", "2人用"))

if mode == "1人用":
    # ... 1人用UI ...
    pass
elif mode == "2人用":
    # ... 2人用UIと鑑定実行ロジック ...
    # この部分は変更がないため省略しています
    pass
