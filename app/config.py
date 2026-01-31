"""アプリケーション設定"""

# ========================================
# 河川事業に関連するキーワード辞書
# ========================================
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
    "発注・調達": [
        "一般競争入札", "公募型プロポーザル", "総合評価落札方式",
        "簡易公募型競争入札", "指名競争入札",
        "業務委託", "工事発注", "設計業務", "調査業務", "測量業務",
        "河川測量", "河川設計", "河川工事", "護岸工事", "堤防工事",
        "砂防工事", "ダム工事", "水門工事",
        "解析業務", "シミュレーション業務", "検討業務",
        "技術提案", "プロポーザル", "総合評価",
    ],
    "河道計画・河道設計": [
        "河道計画", "河道設計", "河道改修",
        "河道断面", "計画高水位", "計画高水流量", "流下能力",
        "河道整正", "河道拡幅", "引堤", "築堤",
        "河床掘削", "河道掘削", "河床低下",
        "低水路", "高水敷", "複断面",
        "河道平面形", "蛇行", "河岸侵食", "河道安定",
        "粗度係数", "マニング", "流速",
        "背水計算", "水面形", "等流", "不等流",
        "河道内樹木", "樹木伐採", "阻害率",
        "洪水流下", "流下能力評価", "流量配分",
        "河川砂防技術基準", "河道計画検討",
        "河道の平面形状", "河道の縦横断形状",
        "治水安全度", "計画規模", "超過確率",
        "河床材料", "河床形態", "移動床", "固定床",
    ],
}

# ========================================
# 河道計画・設計関連の業務分類
# ========================================
KADOU_BUSINESS_CATEGORIES = {
    "河道計画策定": [
        "河道計画", "河道計画検討", "河道計画策定",
        "流下能力", "流量配分", "計画高水流量",
        "治水安全度", "計画規模",
    ],
    "河道設計": [
        "河道設計", "河道断面", "河道改修設計",
        "護岸設計", "堤防設計", "水門設計",
        "床止め設計", "水制設計",
    ],
    "水理解析・シミュレーション": [
        "水理計算", "水理解析", "不等流計算", "不定流計算",
        "洪水シミュレーション", "氾濫シミュレーション",
        "背水計算", "水面形", "二次元解析",
        "iRIC", "Nays2DFlood", "HEC-RAS",
    ],
    "河床変動解析": [
        "河床変動", "河床変動計算", "土砂輸送",
        "移動床", "河床低下", "河床材料",
        "河床形態", "掃流砂", "浮遊砂",
    ],
    "河川測量・調査": [
        "河川測量", "縦横断測量", "深浅測量",
        "河床材料調査", "流量観測", "水位観測",
        "河道台帳", "定期縦横断",
    ],
    "河道内管理": [
        "河道内樹木", "樹木伐採", "阻害率",
        "河道の維持管理", "堆積土砂",
    ],
}

# ========================================
# 全国 河川事務所 一覧
# ========================================

# --- 北海道開発局 開発建設部 ---
HOKKAIDO_RIVER_OFFICES = [
    {"name": "札幌開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/sp/index.html"},
    {"name": "小樽開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/ot/index.html"},
    {"name": "函館開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/hk/index.html"},
    {"name": "旭川開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/as/index.html"},
    {"name": "室蘭開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/mr/index.html"},
    {"name": "釧路開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/ks/index.html"},
    {"name": "帯広開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/ob/index.html"},
    {"name": "網走開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/ab/index.html"},
    {"name": "留萌開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/rm/index.html"},
    {"name": "稚内開発建設部", "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/wk/index.html"},
]

# --- 東北地方整備局 河川事務所 ---
TOHOKU_RIVER_OFFICES = [
    {"name": "岩木川河川事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/iwaki/"},
    {"name": "青森河川国道事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/aomori/"},
    {"name": "岩手河川国道事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/iwate/"},
    {"name": "北上川下流河川事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/karyuu/"},
    {"name": "秋田河川国道事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/akita/"},
    {"name": "湯沢河川国道事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/yuzawa/"},
    {"name": "山形河川国道事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/yamagata/"},
    {"name": "最上川河川事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/mogami/"},
    {"name": "福島河川国道事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/fukushima/"},
    {"name": "北上川上流河川事務所", "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/jouryuu/"},
]

# --- 関東地方整備局 河川事務所 ---
KANTO_RIVER_OFFICES = [
    {"name": "利根川上流河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/tonejo/"},
    {"name": "利根川下流河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/tonege/"},
    {"name": "江戸川河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/edogawa/"},
    {"name": "荒川上流河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/arajo/"},
    {"name": "荒川下流河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/arage/"},
    {"name": "京浜河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/keihin/"},
    {"name": "甲府河川国道事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/kofu/"},
    {"name": "渡良瀬川河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/watarase/"},
    {"name": "下館河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/shimodate/"},
    {"name": "常陸河川国道事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/hitachi/"},
    {"name": "霞ヶ浦河川事務所", "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/kasumi/"},
]

# --- 北陸地方整備局 河川事務所 ---
HOKURIKU_RIVER_OFFICES = [
    {"name": "羽越河川国道事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/uetsu/"},
    {"name": "新潟河川事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/niigata/"},
    {"name": "信濃川河川事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/shinano/"},
    {"name": "信濃川下流河川事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/shinage/"},
    {"name": "阿賀川河川事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/agagawa/"},
    {"name": "湯沢砂防事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/yusabo/"},
    {"name": "金沢河川国道事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/kanazawa/"},
    {"name": "富山河川国道事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/toyama/"},
    {"name": "黒部河川事務所", "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/kurobe/"},
]

# --- 中部地方整備局 河川事務所 ---
CHUBU_RIVER_OFFICES = [
    {"name": "木曽川上流河川事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/kisojyo/"},
    {"name": "木曽川下流河川事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/kisokaryu/"},
    {"name": "庄内川河川事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/shonai/"},
    {"name": "豊橋河川事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/toyohashi/"},
    {"name": "浜松河川国道事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/hamamatsu/"},
    {"name": "沼津河川国道事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/numazu/"},
    {"name": "静岡河川事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/shizukawa/"},
    {"name": "天竜川上流河川事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/tenjyo/"},
    {"name": "飯田国道事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/iida/"},
    {"name": "越美山系砂防事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/etumi/"},
    {"name": "多治見砂防国道事務所", "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/tajimi/"},
]

# --- 近畿地方整備局 河川事務所 ---
KINKI_RIVER_OFFICES = [
    {"name": "琵琶湖河川事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/biwako/"},
    {"name": "淀川河川事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/yodogawa/"},
    {"name": "大和川河川事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/yamato/"},
    {"name": "紀の川河川事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/kinokawa/"},
    {"name": "福知山河川国道事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/fukuchiyama/"},
    {"name": "豊岡河川国道事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/toyooka/"},
    {"name": "木津川上流河川事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/kizujyo/"},
    {"name": "猪名川河川事務所", "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/inagawa/"},
]

# --- 中国地方整備局 河川事務所 ---
CHUGOKU_RIVER_OFFICES = [
    {"name": "岡山河川事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/okakawa/"},
    {"name": "福山河川国道事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/fukuyama/"},
    {"name": "三次河川国道事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/miyoshi/"},
    {"name": "太田川河川事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/ootagawa/"},
    {"name": "出雲河川事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/izumokawa/"},
    {"name": "日野川河川事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/hinokawa/"},
    {"name": "鳥取河川国道事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/tottori/"},
    {"name": "山口河川国道事務所", "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/yamaguchi/"},
]

# --- 四国地方整備局 河川事務所 ---
SHIKOKU_RIVER_OFFICES = [
    {"name": "徳島河川国道事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/tokushima/"},
    {"name": "那賀川河川事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/nakagawa/"},
    {"name": "高知河川国道事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/kochi/"},
    {"name": "中筋川総合開発事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/nakasuji/"},
    {"name": "松山河川国道事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/matsuyam/"},
    {"name": "大洲河川国道事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/oozu/"},
    {"name": "香川河川国道事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/kagawa/"},
    {"name": "吉野川河川事務所", "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/yoshino/"},
]

# --- 九州地方整備局 河川事務所 ---
KYUSHU_RIVER_OFFICES = [
    {"name": "遠賀川河川事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/onga/"},
    {"name": "筑後川河川事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/chikugo/"},
    {"name": "武雄河川事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/takeo/"},
    {"name": "長崎河川国道事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/nagasaki/"},
    {"name": "熊本河川国道事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/kumamoto/"},
    {"name": "八代河川国道事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/yatusiro/"},
    {"name": "川辺川ダム砂防事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/kawabe/"},
    {"name": "大分河川国道事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/oita/"},
    {"name": "延岡河川国道事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/nobeoka/"},
    {"name": "宮崎河川国道事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/miyazaki/"},
    {"name": "大隅河川国道事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/osumi/"},
    {"name": "川内川河川事務所", "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/sendai/"},
]

# 全河川事務所を統合
ALL_RIVER_OFFICES = (
    HOKKAIDO_RIVER_OFFICES
    + TOHOKU_RIVER_OFFICES
    + KANTO_RIVER_OFFICES
    + HOKURIKU_RIVER_OFFICES
    + CHUBU_RIVER_OFFICES
    + KINKI_RIVER_OFFICES
    + CHUGOKU_RIVER_OFFICES
    + SHIKOKU_RIVER_OFFICES
    + KYUSHU_RIVER_OFFICES
)

# ========================================
# 公共事業 発注情報ソース
# ========================================

# 各地方整備局の入札・契約情報ページ
PROCUREMENT_SOURCES = [
    # --- 国土交通省 本省 ---
    {"name": "国土交通省 入札・契約情報",
     "region": "全国", "bureau": "国土交通省",
     "url": "https://www.mlit.go.jp/chotatsu/index.html",
     "type": "ministry"},

    # --- 北海道開発局 ---
    {"name": "北海道開発局 入札・契約情報",
     "region": "北海道", "bureau": "北海道開発局",
     "url": "https://www.hkd.mlit.go.jp/ky/jg/giken/index.html",
     "type": "bureau"},

    # --- 東北地方整備局 ---
    {"name": "東北地方整備局 入札・契約情報",
     "region": "東北", "bureau": "東北地方整備局",
     "url": "https://www.thr.mlit.go.jp/bumon/b06111/cp-info/index.html",
     "type": "bureau"},

    # --- 関東地方整備局 ---
    {"name": "関東地方整備局 入札・契約情報",
     "region": "関東", "bureau": "関東地方整備局",
     "url": "https://www.ktr.mlit.go.jp/honkyoku/nyuusatu/index.htm",
     "type": "bureau"},

    # --- 北陸地方整備局 ---
    {"name": "北陸地方整備局 入札・契約情報",
     "region": "北陸", "bureau": "北陸地方整備局",
     "url": "https://www.hrr.mlit.go.jp/bosyu/index.html",
     "type": "bureau"},

    # --- 中部地方整備局 ---
    {"name": "中部地方整備局 入札・契約情報",
     "region": "中部", "bureau": "中部地方整備局",
     "url": "https://www.cbr.mlit.go.jp/architecture/kensetsugijutsu/index.htm",
     "type": "bureau"},

    # --- 近畿地方整備局 ---
    {"name": "近畿地方整備局 入札・契約情報",
     "region": "近畿", "bureau": "近畿地方整備局",
     "url": "https://www.kkr.mlit.go.jp/contract/index.php",
     "type": "bureau"},

    # --- 中国地方整備局 ---
    {"name": "中国地方整備局 入札・契約情報",
     "region": "中国", "bureau": "中国地方整備局",
     "url": "https://www.cgr.mlit.go.jp/contract/index.htm",
     "type": "bureau"},

    # --- 四国地方整備局 ---
    {"name": "四国地方整備局 入札・契約情報",
     "region": "四国", "bureau": "四国地方整備局",
     "url": "https://www.skr.mlit.go.jp/bosyu/index.html",
     "type": "bureau"},

    # --- 九州地方整備局 ---
    {"name": "九州地方整備局 入札・契約情報",
     "region": "九州", "bureau": "九州地方整備局",
     "url": "https://www.qsr.mlit.go.jp/n-contract/index.html",
     "type": "bureau"},
]

# 電子入札・発注情報公開サービス
PROCUREMENT_PORTAL_SOURCES = [
    {"name": "国土交通省 電子入札システム",
     "region": "全国", "bureau": "国土交通省",
     "url": "https://www.e-bisc.go.jp/",
     "type": "portal"},
    {"name": "入札情報サービス(PPI)",
     "region": "全国", "bureau": "国土交通省",
     "url": "https://ppi.epco.go.jp/",
     "type": "portal"},
]
