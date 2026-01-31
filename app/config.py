"""アプリケーション設定"""

# 河川事業に関連するキーワード辞書
RIVER_KEYWORDS = {
    "事業課題": [
        "洪水対策", "治水", "水害", "浸水", "氾濫", "堤防", "護岸",
        "河川整備", "河道掘削", "遊水地", "調節池", "放水路",
        "土砂災害", "土石流", "地すべり", "崖崩れ",
        "水質汚濁", "水質改善", "水環境", "生態系",
        "老朽化", "維持管理", "長寿命化", "インフラ老朽化",
        "気候変動", "豪雨", "台風", "線状降水帯",
        "流域治水", "内水氾濫", "高潮", "津波",
        "河川管理", "水位管理", "ダム管理", "砂防",
    ],
    "数値解析・シミュレーション": [
        "数値解析", "数値シミュレーション", "数値計算",
        "洪水シミュレーション", "氾濫シミュレーション", "浸水シミュレーション",
        "流出解析", "降雨流出", "流量計算",
        "河床変動", "河床変動計算", "土砂輸送",
        "水理計算", "水理解析", "不等流計算", "不定流計算",
        "二次元解析", "三次元解析", "準二次元解析",
        "有限要素法", "有限差分法", "有限体積法",
        "iRIC", "Nays2DFlood", "RiverFlow2D",
        "HEC-RAS", "MIKE", "FLO-2D",
        "CFD", "流体解析", "乱流モデル",
        "地盤解析", "浸透流解析", "安定解析",
        "構造解析", "耐震解析", "動的解析",
    ],
    "先端技術": [
        "AI", "人工知能", "機械学習", "深層学習", "ディープラーニング",
        "IoT", "センサー", "リモートセンシング", "衛星",
        "ドローン", "UAV", "点群", "LiDAR", "レーザー測量",
        "GIS", "地理情報", "デジタルツイン",
        "BIM/CIM", "3次元モデル", "三次元モデル",
        "DX", "デジタルトランスフォーメーション",
        "ビッグデータ", "データ解析", "統計解析",
        "リアルタイム", "予測", "早期警戒",
        "自動化", "ロボット", "ICT施工",
    ],
    "政策・制度": [
        "河川法", "水防法", "砂防法",
        "国土強靱化", "防災・減災", "事前防災",
        "グリーンインフラ", "自然共生",
        "流域マネジメント", "統合水資源管理",
        "PPP", "PFI", "官民連携",
        "技術基準", "ガイドライン", "マニュアル",
        "予算", "事業評価", "費用便益",
    ],
}

# 国土交通省の情報ソース
MLIT_SOURCES = [
    {
        "name": "国土交通省 水管理・国土保全局",
        "url": "https://www.mlit.go.jp/river/index.html",
        "type": "main_page",
    },
    {
        "name": "国土交通省 報道発表（河川）",
        "url": "https://www.mlit.go.jp/river/river_tk1_000014.html",
        "type": "press_release",
    },
    {
        "name": "国土交通省 河川の技術基準",
        "url": "https://www.mlit.go.jp/river/shishin_guideline/index.html",
        "type": "technical",
    },
    {
        "name": "国土交通省 河川砂防技術研究開発",
        "url": "https://www.mlit.go.jp/river/gijutsu/index.html",
        "type": "research",
    },
]

# 主要な都道府県河川関連ページ
PREFECTURE_SOURCES = [
    {"name": "北海道", "region": "北海道",
     "url": "https://www.pref.hokkaido.lg.jp/kn/ksb/index.html"},
    {"name": "東京都", "region": "関東",
     "url": "https://www.kensetsu.metro.tokyo.lg.jp/jigyo/river/index.html"},
    {"name": "新潟県", "region": "中部",
     "url": "https://www.pref.niigata.lg.jp/site/kasen/"},
    {"name": "愛知県", "region": "中部",
     "url": "https://www.pref.aichi.jp/soshiki/kasen/"},
    {"name": "大阪府", "region": "近畿",
     "url": "https://www.pref.osaka.lg.jp/kasenseibi/index.html"},
    {"name": "広島県", "region": "中国",
     "url": "https://www.pref.hiroshima.lg.jp/soshiki/98/"},
    {"name": "福岡県", "region": "九州",
     "url": "https://www.pref.fukuoka.lg.jp/contents/kasen.html"},
    {"name": "宮城県", "region": "東北",
     "url": "https://www.pref.miyagi.jp/soshiki/kasen/"},
    {"name": "静岡県", "region": "中部",
     "url": "https://www.pref.shizuoka.jp/kensetsu/ke-400/index.html"},
    {"name": "熊本県", "region": "九州",
     "url": "https://www.pref.kumamoto.jp/soshiki/97/"},
]

# 地方整備局
REGIONAL_BUREAU_SOURCES = [
    {"name": "北海道開発局", "region": "北海道",
     "url": "https://www.hkd.mlit.go.jp/ky/kn/river_firing/index.html"},
    {"name": "東北地方整備局", "region": "東北",
     "url": "https://www.thr.mlit.go.jp/river/index.html"},
    {"name": "関東地方整備局", "region": "関東",
     "url": "https://www.ktr.mlit.go.jp/river/index.htm"},
    {"name": "北陸地方整備局", "region": "中部",
     "url": "https://www.hrr.mlit.go.jp/river/index.html"},
    {"name": "中部地方整備局", "region": "中部",
     "url": "https://www.cbr.mlit.go.jp/kawatomizu/index.htm"},
    {"name": "近畿地方整備局", "region": "近畿",
     "url": "https://www.kkr.mlit.go.jp/river/index.php"},
    {"name": "中国地方整備局", "region": "中国",
     "url": "https://www.cgr.mlit.go.jp/river/index.html"},
    {"name": "四国地方整備局", "region": "四国",
     "url": "https://www.skr.mlit.go.jp/kasen/index.html"},
    {"name": "九州地方整備局", "region": "九州",
     "url": "https://www.qsr.mlit.go.jp/n-kasen/index.html"},
]
