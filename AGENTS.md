# AGENTS.md — 世界遊記 LLM Wiki

> 這份文件是給 AI（Claude、Codex、Cursor…）的工作規則，也是這個 wiki 的 **schema**。
> 每次開始工作前先讀完這份文件、`wiki/index.md`、`wiki/log.md` 最後 5 筆。
> 人類看的簡介在 `README.md`。

---

## 0. 五條最重要的規則

1. **`raw/` 只讀**：AI 不新增、不修改、不刪除、不改檔名 `raw/` 裡的任何東西。例外只有兩個：Percy 貼上日記時，AI 依 6.2 過濾後寫入 `raw/journal/`；照片與行政區圖片處理完後刪掉 `raw/` 原檔（6.4）。
2. **日記只留事實**：wiki 只記**移動方式、景點、天氣**，不寫過程、心得、感想、人物。不可編造；沒有就寫 `> 待補`。
3. **隱私優先於一切**：網站是公開的，第 10 節的規則比任何其他規則優先。
4. **先列 todo 再動手**：每個任務先列出要做的步驟（會動到哪些頁），再開始改。
5. **完成的定義**：`uv run scripts/lint.py` 0 錯誤、`uv run scripts/build.py` 成功、`index.md` 與 `log.md` 已更新（第 12 節）。

---

## 1. 專案目的

把 Percy 的旅行——**行程規劃、實際走的路線（GPX）、旅途日記、照片**——編譯成一個以地圖為主、互相連結的個人旅遊百科，並用 GitHub Pages 公開。

- 範圍是**全世界**：一趟旅程可以跨多個國家，同一個景點可以被多趟旅程造訪。
- 做法照 [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)：不是每次從原始檔重新拼答案，而是由 AI 把原始資料**編譯一次**成持久的 Markdown wiki，之後持續維護（ingest / query / lint）。
- 分工：**Percy** 負責放原始資料、提問、做判斷；**AI** 負責摘要、建頁、交叉連結、歸檔、檢查等所有繁瑣工作。
- 核心概念：**「計畫」和「實際」是兩種來源**，兩者的差異不是錯誤，而是 wiki 要呈現的內容（第 5 節）。

目前的旅程：

| 旅程 | 狀態 | 有的資料 |
| --- | --- | --- |
| `2026-08-japan` 日本（2026-07-30～08-15） | 已完成 | 原版行程 v2（過濾版）、日記（已過濾）、GPX、車站確認 |
| `2027-06-iceland` 冰島（2027-06） | 規劃中 | AI 產生的行程 v1（只有計畫） |

---

## 2. 三層結構

| 層 | 位置 | 內容 | 誰寫 |
| --- | --- | --- | --- |
| Raw sources | `raw/` | 行程、日記、GPX、照片原檔。**事實來源，不可修改** | Percy 放入，AI 只讀（日記例外見第 0 節） |
| Wiki | `wiki/` | AI 產生的 Markdown 頁：國家、行政區、城市、旅程、日程、景點、筆記 | AI 完全負責 |
| Schema | `AGENTS.md` | 結構、模板、流程、規則 | Percy 和 AI 共同演進（改之前要問，第 11 節） |

網站（`site/`）是 wiki 的**產物**，由 `scripts/build.py` 從 `wiki/` + `assets/` 產生，不手改。

---

## 3. 目錄與命名

### 3.1 目錄

```text
world-tour-llm-wiki/
├─ AGENTS.md                        # 本文件（schema）
├─ CLAUDE.md                        # 一行：@AGENTS.md
├─ README.md                        # 專案簡介、網站連結、怎麼用
├─ pyproject.toml                   # uv 專案設定與相依套件
├─ raw/                             # ← Percy 放、AI 只讀
│  ├─ plans/<trip>/plan-vN.*            # 行程；改版 = 新的 plan-v(N+1)，舊版不動
│  │                                    # 原檔含住宿、花費 → plan-vN.private.*（不進 git）＋ AI 過濾版 plan-vN.md
│  ├─ journal/<trip>/YYYY-MM-DD.md      # 每日日記，已過濾成「移動／景點／天氣」（8.2）
│  ├─ gpx/<trip>/*.gpx                  # GPX 軌跡（Geo Tracker 匯出，檔名不拘），.gitignore 排除
│  ├─ photos/<trip>/*                   # 照片原檔，.gitignore 排除；放進來＝同意公開；處理完就刪
│  └─ regions/<region>.*                # 行政區大圓用的圖片（Percy 提供，可省略），處理完就刪
├─ wiki/                            # ← AI 維護
│  ├─ index.md                          # 全部頁面目錄
│  ├─ log.md                            # 只增不改的工作紀錄
│  ├─ overview.md                       # 全部旅程總覽
│  ├─ countries/<cc>.md                 # 國家頁
│  ├─ regions/<region>.md               # 行政區頁：日本都道府縣、台灣縣市、美國州…
│  ├─ cities/<city>.md                  # 城市或地區頁（屬於某個 region）
│  ├─ trips/<trip>.md                   # 旅程頁
│  ├─ days/<trip>/day-NN.md             # 日程頁
│  ├─ places/<city>/<place>.md          # 景點頁（地圖上的每一個點）
│  └─ notes/<slug>.md                   # 查詢結果存回的筆記（比較、整理）
├─ assets/                          # ← 由 scripts 產生，進 git
│  ├─ photos/<place>/YYYYMMDD-NN.webp   # 公開照片（144p、已清中繼資料）
│  ├─ photos/<place>/YYYYMMDD-NN-thumb.webp
│  ├─ regions/<region>.webp             # 行政區大圓圖片（正方形 160 px）
│  └─ tracks/<trip>/YYYY-MM-DD.geojson  # 簡化、去頭尾後的公開軌跡
├─ scripts/
│  ├─ build.py                          # wiki/ + assets/ → site/
│  ├─ geocode.py                        # 查座標（Nominatim）
│  ├─ tracks.py                         # GPX → 公開 geojson ＋ 停留點分析
│  ├─ stations.py                       # GPX × 車站資料 → 車站候選清單
│  ├─ photos.py                         # 照片 144p、WebP、清中繼資料、對應景點；--regions 處理行政區圖片
│  └─ lint.py                           # 機械式檢查
├─ templates/                       # build.py 用的 Jinja2 模板與 CSS/JS
├─ reports/                         # AI 給 Percy 的待問清單（例：車站比對），.gitignore
├─ .cache/                          # 下載的參考資料（例：stations-jp.csv），.gitignore
├─ site/                            # build 產物，.gitignore，由 Actions 部署
└─ .github/workflows/pages.yml
```

### 3.2 命名規則

| 東西 | 規則 | 例子 |
| --- | --- | --- |
| 檔名／slug | 英文小寫 kebab-case，只用 `a-z 0-9 -` | `kiyomizu-dera`、`golden-circle` |
| 旅程 ID `<trip>` | `YYYY-MM-<主題>`，年月取**大部分天數所在的月份** | `2026-08-japan`（7/30～8/15） |
| 國家 `<cc>` | ISO 3166-1 alpha-2，檔名小寫、frontmatter 大寫 | `jp.md`、`country: JP` |
| 行政區 `<region>` | 羅馬拼音＋種類：日本 `-pref`、台灣 `-county`／`-city`、美國 `-state`、其他 `-region` | `kyoto-pref`、`tainan-city`、`california-state` |
| 城市 `<city>` | 當地常用英文名；不是城市的用地區名 | `kyoto`、`south-coast` |
| 景點 `<place>` | 當地原名的羅馬拼音或英文通稱 | `fushimi-inari-taisha` |
| 日程 | `day-NN`，兩位數，第 1 天 = 出發日 | `day-01.md` |
| 頁面標題 | 中文 ＋ 空格 ＋ 當地原名（原名是中文就只寫一次） | `清水寺 Kiyomizu-dera`、`黃金圈 Gullni hringurinn` |
| 日期 | ISO `YYYY-MM-DD`，一律用**當地時間** | `2027-06-14` |

- 唯一例外：日程頁的 slug 是 `<trip>/day-NN`（含斜線），因為日程只在旅程底下才有意義。
- **slug 全站唯一**（跨類型也不能重複）。撞名時在後面加城市或國家：`central-station-stockholm`、`portland-us`。
- 內部連結一律用 `[[slug]]`；日程用 `[[<trip>/day-NN]]`。可以加顯示文字：`[[kiyomizu-dera|清水寺]]`。由 `build.py` 解析成網址。
- 外部連結用一般 Markdown `[文字](https://...)`。

---

## 4. 頁面類型與模板

共七種頁面。**每種頁面的 frontmatter 欄位與段落順序固定**，新增頁面時直接複製下面的模板。

所有頁面共用的必填欄位：`type`、`title`、`slug`、`sources`、`updated`。

- `sources`：這頁內容來自哪些 `raw/` 檔（相對於 repo 根目錄）。
- `updated`：AI 最後修改這頁的日期（不是旅行日期）。

### 4.1 `place` 景點（核心：地圖上每個點）

路徑 `wiki/places/<city>/<place>.md`

```markdown
---
type: place
title: <中文名> <當地原名>
slug: <place>
city: <city>
country: <CC>
lat: <緯度，小數 4~6 位>
lng: <經度>
coord_source: nominatim   # nominatim | manual | gpx
category: landmark        # landmark | religious | museum | nature | viewpoint | food | shopping | activity | station | transport | lodging-area
lines: []                 # 只有 station 用：路線，例 [JR 東海道本線, 小田急江之島線]
trips: [<trip>]
visits:
  - trip: <trip>
    day: <N>              # 計畫中的第幾天；不在計畫就留 null
    planned: <YYYY-MM-DD> # 來自 plan；不在計畫就留 null
    actual: null          # 來自 journal ＋ GPX；未發生留 null
    status: planned       # 大類：planned | visited（5.2）
    detail: upcoming      # 小類：planned → upcoming | skipped | unconfirmed | dropped
                          #       visited → as-planned | moved | added | unconfirmed
    evidence: []          # journal | gpx | percy（第 5 節）
sources: [raw/plans/<trip>/plan-v1.md]
updated: <YYYY-MM-DD>
---

# <中文名> <當地原名>

一句話介紹這是什麼地方（客觀資訊，可用 AI 的一般知識）。

## 計畫

- **<trip>** 第 <N> 天：來自 plan 的安排與理由。（來源：`raw/plans/<trip>/plan-v1.md`）

## 造訪紀錄

> 待補（旅行後由 journal ＋ GPX ingest 填入，不可編造）

## 照片

（由 photos.py 對應後列出，沒有就留這行）

## 相關

- 城市：[[<city>]]
- 日程：[[<trip>/day-NN]]
```

- 同一個景點在同一趟去了兩次 → `visits` 放兩筆。
- 有造訪後，`## 造訪紀錄` 改成每次造訪一個小節，只寫三件事：

  ```markdown
  ### <YYYY-MM-DD>（[[<trip>]]）
  - 移動：<怎麼到的，例：江之電 → 步行>
  - 天氣：<日記有寫才填>
  - 狀態：去過・照計畫，`visited/as-planned`（journal＋gpx）
  ```
- `station` = 火車站、地鐵站、私鐵站（只收**上下車或轉乘**過的，路過不算，見 6.3.1）。slug 用 `<羅馬拼音>-station`，例 `fujisawa-station`；標題 `藤澤站 藤沢駅`。機場、港口、巴士總站用 `transport`。
- `lodging-area` 只能是「區域」（例：`shinjuku-area`），座標取區域中心，**不可以是飯店**（第 10 節）。

### 4.2 `day` 日程

路徑 `wiki/days/<trip>/day-NN.md`

```markdown
---
type: day
title: 第 <N> 天 <當天主要城市或主題>
slug: <trip>/day-NN
trip: <trip>
day: <N>
date: <YYYY-MM-DD>        # 計畫日期
cities: [<city>]
planned: [<place>, <place>]   # 順序 = 計畫路線
actual: []                    # 順序 = 實際路線；未發生留 []
track: null                   # 有 GPX 就填 assets/tracks/<trip>/<date>.geojson
sources: [raw/plans/<trip>/plan-v1.md]
updated: <YYYY-MM-DD>
---

# 第 <N> 天 <主題>

一句話摘要這一天。

## 計畫 vs 實際

| 計畫 | 實際 | status |
| --- | --- | --- |
| 09:00 [[<place>]] | 09:30 [[<place>]] | 去過・照計畫 |
| 13:00 [[<place>]] | — | 計畫・沒去 |
| — | 15:00 [[<place>]] | 去過・臨時加 |

## 當日紀錄

- 移動：<交通方式與順序，例：夜間巴士 → 橫濱站 → JR → 七里濱>
- 天氣：<日記有寫才填>

> 未發生或沒有日記時寫：待補（不可編造）

## 交通與住宿區域

- 交通：<來自 plan / journal>
- 住宿區域：[[<lodging-area>]]

## 相關

- 旅程：[[<trip>]]
- 前一天：[[<trip>/day-NN]]　下一天：[[<trip>/day-NN]]
```

### 4.3 `trip` 旅程

路徑 `wiki/trips/<trip>.md`

```markdown
---
type: trip
title: <旅程名稱，例：冰島環島 2027 夏>
slug: <trip>
countries: [<CC>]
cities: [<city>, <city>]
start: <YYYY-MM-DD>
end: <YYYY-MM-DD>
timezone: <IANA，例 Asia/Tokyo>
status: planned           # planned | ongoing | completed
plan: raw/plans/<trip>/plan-v1.md   # 目前計畫 = 最新版本
plan_versions: [plan-v1.md]
color: "#2a9d8f"          # 地圖上這趟旅程的顏色，不和其他旅程重複
sources: [raw/plans/<trip>/plan-v1.md]
updated: <YYYY-MM-DD>
---

# <旅程名稱>

一段話摘要：去哪、幾天、主題。

## 每日

- [[<trip>/day-01]] <城市> — 一句話
- [[<trip>/day-02]] <城市> — 一句話

## 計畫 vs 實際

（旅行後填：照計畫、改期、沒去、臨時加的景點各有哪些，用 [[連結]] 列出；未發生寫「尚未出發」）

## 計畫的改版

- v1（<YYYY-MM-DD>）：初版。
- v2（<YYYY-MM-DD>）：<改了什麼、為什麼>。

## 相關

- 國家：[[<cc>]]
- 筆記：[[<note>]]
```

### 4.4 `city` 城市或地區

路徑 `wiki/cities/<city>.md`。冰島環島這種「景點不在城市裡」的情況，用 `kind: region`。

```markdown
---
type: city
title: <中文名> <當地原名>
slug: <city>
kind: city                # city | region
region: <region>          # 上層行政區（4.5）
country: <CC>
lat: <中心緯度>
lng: <中心經度>
zoom: 12                  # 地圖預設縮放；region 通常 8~10
trips: [<trip>]
sources: [raw/plans/<trip>/plan-v1.md]
updated: <YYYY-MM-DD>
---

# <中文名> <當地原名>

一句話介紹。

## 景點

### 地標
- [[<place>]] <中文名> — 一句話

### 美食
- [[<place>]] …

## 去過的旅程

- [[<trip>]] 第 N～M 天

## 相關

- 上層：[[<region>]]
- 國家：[[<cc>]]
```

`## 景點` 下的小標題依 `category` 分組，沒有的類別不寫。類別中文名：landmark 地標、religious 寺社與教堂、museum 博物館、nature 自然、viewpoint 展望點、food 美食、shopping 購物、activity 體驗、station 車站、transport 交通、lodging-area 住宿區域。

### 4.5 `region` 行政區（都道府縣／縣市／州）

路徑 `wiki/regions/<region>.md`。國家和城市中間的一層，用在地圖縮小時的大圓標記（9.4）。日本＝都道府縣、台灣＝縣市、美國＝州，其他國家用官方的一級行政區。

```markdown
---
type: region
title: <中文名> <當地原名>
slug: <region>
kind: prefecture          # prefecture（都道府縣）| county（縣）| city（直轄市、省轄市）| state（州）| region（其他）
country: <CC>
label: <地圖大圓上的字，2～3 個字，例：京都>
icon: null                # Percy 有給圖片就填 assets/regions/<region>.webp；沒有就顯示 label
lat: <大圓位置>
lng: <大圓位置>
zoom: 9
cities: [<city>]
trips: [<trip>]
sources: []
updated: <YYYY-MM-DD>
---

# <中文名> <當地原名>

一句話介紹。

收錄 N 個景點與車站，其中 M 個確認去過。

## 城市與地區

- [[<city>]]

## 去過的旅程

- [[<trip>]]

## 相關

- 國家：[[<cc>]]
```

- 新增城市時一定要指定 `region`；該行政區還沒有頁就先建。
- 圖片：Percy 把圖放在 `raw/regions/<region>.(jpg|png)`，跑 `uv run scripts/photos.py --regions` 轉成 `assets/regions/<region>.webp`（置中裁成正方形、清中繼資料），再把 `icon` 填上。

### 4.6 `country` 國家

路徑 `wiki/countries/<cc>.md`

```markdown
---
type: country
title: <中文名> <當地原名>
slug: <cc>
country: <CC>
lat: <中心緯度>
lng: <中心經度>
zoom: 5
trips: [<trip>]
cities: [<city>]
sources: []
updated: <YYYY-MM-DD>
---

# <中文名> <當地原名>

一句話介紹（時區、貨幣、語言等實用資訊可放這裡）。

## 旅程

- [[<trip>]] <YYYY-MM> — 一句話

## 都道府縣／縣市／州

- [[<region>]] — [[<city>]]、[[<city>]]

## 城市與地區

- [[<city>]] — 一句話
```

### 4.7 `note` 筆記（Query 存回的答案）

路徑 `wiki/notes/<slug>.md`。例：`japan-vs-iceland-transport`、`kansai-rainy-day-options`。

```markdown
---
type: note
title: <中文標題>
slug: <slug>
about: [<相關 slug>]
sources: [<引用的 wiki 頁或 raw 檔>]
updated: <YYYY-MM-DD>
---

# <中文標題>

<內容：比較表、整理、建議。每個事實都要用 [[連結]] 指回 wiki 頁>

## 來源

- [[<slug>]]
```

---

## 5. 計畫 vs 實際

### 5.1 兩種來源，都不可改

- **計畫** = `raw/plans/<trip>/plan-vN.*`。行程改了就放 `plan-v(N+1)`，舊版不動。wiki 以**最新版**為目前計畫。
- **實際** = 兩種證據，**必須兩種同時出現才算數**：
  1. `journal`：`raw/journal/<trip>/` 的日記（已過濾）。
  2. `gpx`：`raw/gpx/<trip>/` 的軌跡。
- 只有一種出現 → 不自動判定，小類標 `unconfirmed`，留給 Percy 人工比對。Percy 確認後 `evidence` 加 `percy`，改成正確的小類。
- 照片**不是**判定證據，只用來掛在景點頁上（6.4）。

### 5.2 status：兩大類＋小類

每次造訪用兩個欄位：`status` 是**大類**，只有 `planned`（計畫的）和 `visited`（去過的）；`detail` 是**小類**。大類決定地圖標記的大小，小類決定樣式和角標。

**`planned` 計畫的（地圖上小）**

| detail | 意思 | 判定依據 | 地圖標記 |
| --- | --- | --- | --- |
| `upcoming` | 還沒去 | 只出現在 plan，且日期未到 | 小、白底虛線框 |
| `skipped` | 計畫了但沒去 | journal 寫沒去，且 gpx 沒經過；或 Percy 確認 | 小、灰色＋「×」 |
| `unconfirmed` | 日期過了，不知道有沒有去 | journal、gpx 都沒有 | 小、白底＋橘色「?」 |
| `dropped` | 計畫改版時被拿掉 | 舊版 plan 有、最新版沒有 | 地圖不顯示，只列在旅程頁「計畫的改版」 |

**`visited` 去過的（地圖上大）**

| detail | 意思 | 判定依據 | 地圖標記 |
| --- | --- | --- | --- |
| `as-planned` | 照計畫去了 | plan 有；journal ＋ gpx 都有，日期相同 | 大、實心 |
| `moved` | 去了但不是原定那天 | plan 有；journal ＋ gpx 都有，日期不同 | 大、實心＋藍色「改」 |
| `added` | 計畫外臨時去的 | plan 沒有；journal ＋ gpx 都有 | 大、實心＋綠色「+」 |
| `unconfirmed` | 可能去過，但證據只有一邊 | journal 和 gpx 只有一個有，或兩者矛盾 | 大、白底＋橘色「?」 |

- 網頁與 wiki 表格用中文標籤：`計畫・還沒去`、`計畫・沒去`、`計畫・待確認`、`去過・照計畫`、`去過・改期`、`去過・臨時加`、`去過・待確認`。
- frontmatter 寫英文代碼，例：`status: visited`、`detail: moved`；文字裡寫成 `visited/moved`。

### 5.3 判定規則

| 證據 | 算「有出現」的條件 |
| --- | --- |
| journal | 日記的「景點」寫到這個地方（名稱可對應到 place） |
| gpx | 軌跡在半徑內**停留 ≥ 10 分鐘**；半徑一般 200 m，`nature`、`viewpoint`、`lodging-area` 1 km；`transport` 類路過就算 |

決策表（journal × gpx）：

| journal | gpx | plan 有 | plan 沒有 |
| --- | --- | --- | --- |
| 有 | 有 | `visited/as-planned`；日期不同 `visited/moved` | `visited/added` |
| 有 | 沒有（或那天沒有 GPX 檔） | `visited/unconfirmed` | `visited/unconfirmed` |
| 沒有 | 有 | `visited/unconfirmed` | 不建頁，列入待問 |
| 寫「沒去」 | 沒有 | `planned/skipped` | — |
| 沒有 | 沒有 | 日期未到 `planned/upcoming`；已過 `planned/unconfirmed` | — |

- `unconfirmed` 的每一筆都在 lint 報告「待問」列出：place、日期、journal 怎麼寫、GPX 最近距離與停留時間。**AI 不替 Percy 決定。**
- GPX 停留點對不到任何 place：不自動建頁，列為「可能的計畫外停留（座標、當地時間、時長）」問 Percy。
- 日記寫的名稱不確定（日記裡標「待確認」）：先用 GPX 停留點找候選地點，連同候選一起問 Percy，不自己定案。
- 時間換算：GPX 時間是 UTC，用旅程的 `timezone` 換成當地日期再比對。
- 旅程期間離開 `countries` 的 GPX 段落（例：在台灣家裡到機場）不參與比對，也不公開（第 10 節）。

---

## 6. 操作流程

每個流程開始前：讀 `AGENTS.md` → `wiki/index.md` → `wiki/log.md` 最後 5 筆（`grep "^## \[" wiki/log.md | tail -5`）→ 列 todo。
每個流程結束時：更新 `index.md`、寫 `log.md`、跑 lint 與 build（第 12 節）。

### 6.1 Ingest 行程（plan）

觸發：Percy 說「ingest `<trip>` 的 plan」。

1. 讀最新的 `plan-vN`。接受任何格式（Markdown、PDF、Excel、截圖）；**原檔不轉格式、不改**。
   - 原檔有住宿名稱、訂房連結、花費、電話等私人資訊時：原檔改名 `plan-vN.private.<副檔名>`（`.gitignore` 排除），AI 另外過濾出 `plan-vN.md`（照 8.1 格式，只留景點、交通、時間、住宿區域），wiki 的 `sources` 指向過濾版。
2. 先向 Percy 摘要：幾天、哪些城市、約幾個景點、哪些地名有疑義。Percy 確認後才寫頁。
3. 每個景點：
   - 已有 place 頁（同名或同座標 200 m 內）→ 在 `visits` 加一筆，不重複建頁。
   - 沒有 → 用 `uv run scripts/geocode.py "<原名>, <城市>, <國家>"` 查座標，依 4.1 建頁。查不到就請 Percy 給 Google 地圖座標，`coord_source: manual`。
4. 依序建立或更新：day 頁 → trip 頁 → city 頁 → region 頁 → country 頁 → `overview.md`。
5. 若是 v2 以上：和上一版比較，被拿掉的景點改成 `planned/dropped`，在 trip 頁「計畫的改版」寫改了什麼。
6. 更新 index、log。一份行程通常會動到 20～40 頁，這是正常的。

### 6.2 Ingest 日記（journal）

**步驟 A：存檔（只在 Percy 貼上原始日記時）**

原始日記含有私人內容，而 `raw/` 會進公開 repo，所以**原文不存檔**，只存過濾後的版本：

1. 依日期切成 `raw/journal/<trip>/YYYY-MM-DD.md`，格式照 8.2。
2. **只留**：移動方式（交通工具、路線、轉乘）、景點（含原定但沒去的、因天氣改變的）、天氣。
3. **全部刪掉**：過程、心得、感想、情緒、人物（含姓名與外貌）、花費、與旅遊無關的事（例：比賽、工作）。和旅遊無關的日子只記地點。
4. 地名修成正確寫法（例：「城崎海岸」）；認不出來或可能寫錯的，原文照抄並標「待確認」，不自己猜。
5. 原始日記**不寫入 AI 記憶**、不貼進任何 wiki 頁、不在回覆中引用。

**步驟 B：ingest**

觸發：Percy 說「ingest `<trip>` 的 journal」。必須先有 GPX（6.3）才能判定 status。

1. 讀日記，依日期對應到 day 頁。
2. 依 5.3 決策表，把每個景點的 journal 和 GPX 停留點配對。
3. 先向 Percy 摘要：每天的 status 變化、`unconfirmed` 清單（附 GPX 候選）。等 Percy 回覆再寫頁。
4. 更新 day 頁：`actual` 清單、計畫 vs 實際表格、`## 當日紀錄`。
5. 更新每個相關 place 頁：`visits[].actual`、`status`、`detail`、`evidence`、`## 造訪紀錄`。
6. 更新 trip 頁的「計畫 vs 實際」，`status` 改 `ongoing` 或 `completed`。
7. **不可以**加入日記沒寫的移動方式、天氣或景點；客觀介紹（景點是什麼）放在頁首一句話，不放進造訪紀錄。

### 6.3 Ingest 軌跡（GPX）

1. `uv run scripts/tracks.py <trip>`：
   - 讀 `raw/gpx/<trip>/*.gpx`（Geo Tracker 的檔名日期是 UTC，不可靠，一律看點的時間）。
   - 依 `timezone` 把軌跡切成每天一段；**刪掉不在 trip `countries` 內的點**（台灣出發、回家段）。
   - 停留點：自己算（半徑 200 m 內 ≥ 10 分鐘）；GPX 內 `<wpt>` 的「Stop for ~N min」可當參考。
   - 簡化路線（Douglas–Peucker，容差約 20 m），**去掉每天頭尾各 500 m**（住宿位置）。
   - 輸出 `assets/tracks/<trip>/YYYY-MM-DD.geojson`（公開用）與 `scratch` 停留點清單（不進 git）。
2. 填 day 頁的 `track`；status 判定在 6.2 步驟 B 和 journal 一起做。
3. 沒有 GPX 檔的日子，那天所有景點都是 `unconfirmed`。

#### 6.3.1 車站

日記很少寫車站名，所以車站用「GPX 找候選 → Percy 確認」：

1. 車站資料：日本用 `.cache/stations-jp.csv`（來源 [open-data-jp-railway-stations](https://github.com/piuccio/open-data-jp-railway-stations)，ekidata）；其他國家之後用 OpenStreetMap `railway=station`。資料只放 `.cache/`，不進 git。
2. `uv run scripts/stations.py <trip>`：GPX 在車站 **300 m 內停留 ≥ 4 分鐘**（同站 10 分鐘內的多段合併）→ 候選。
3. AI 依路線替每個候選填「判斷」：`上下車`、`轉乘`、`路過`（列車或巴士停靠，沒下車）、`附近`（在附近活動但沒搭車）。
4. 寫成 `reports/<trip>-stations.md`，一天一張表，最後留「沒偵測到、但可能有搭的」欄位（地下鐵常沒訊號）。
5. Percy 改完回覆後：`上下車`、`轉乘` 建 station 頁，`evidence: [gpx, percy]`；`路過`、`附近` 不建頁。
6. day 頁的 `actual` 要依時間順序放入車站，這樣實際路線會經過車站。

### 6.4 Ingest 照片（photos）

1. Percy 只把**願意公開**的照片放進 `raw/photos/`（可以分 `<trip>/` 子資料夾）。檔名寫景點名最準，例：`淨土之濱.jpg`。
2. `uv run scripts/photos.py --delete-raw`：
   - 對應景點：① 檔名含景點中文名（差一兩個字的錯字也算）→ ② EXIF 的 GPS 找半徑內最近的景點 → ③ 拍攝時間對 GPX 位置。都對不到就列為「未對應」問 Percy，原檔保留。照片只決定掛在哪頁，**不改 status**。
   - **短邊 144 px**（144p，不放大）、WebP 品質 80 ＋ 短邊 96 px 縮圖。
   - **清除全部中繼資料**：重新建一張只有像素的影像再存檔，EXIF（GPS、拍攝時間、相機型號、光圈快門、軟體、廠商私有資料）、XMP、色彩描述檔都不會帶過去。script 會印出每張原檔帶了哪些資訊。
   - 輸出到 `assets/photos/<place>/YYYYMMDD-NN.webp`，處理成功的 **raw 原檔直接刪掉**（省空間；原圖請 Percy 自己在手機或雲端留一份）。
3. 在 place 頁 `## 照片` 列出：`![<景點名>（<日期>）](../../../assets/photos/<place>/YYYYMMDD-NN.webp)`，說明只寫看得到的東西，不編故事。

### 6.5 Query 提問

1. 先讀 `index.md` 找相關頁，再深入讀那些頁。
2. 回答時用 `[[slug]]` 引用頁面；wiki 沒有的資訊要明說「wiki 裡沒有」，可另外用一般知識補充但標註。
3. 如果答案值得留下（比較、清單、規劃建議），問 Percy 要不要存成 `wiki/notes/<slug>.md`，存了就更新 index 與 log（`query`）。

### 6.6 Lint 健檢

1. `uv run scripts/lint.py`（機械式，見 12.2）。
2. AI 讀 wiki 做語意檢查：
   - 同一地方不同名字的重複頁（例：`kiyomizu` 和 `kiyomizu-dera`）。
   - 頁面之間互相矛盾（日期、status、城市歸屬）。
   - 提到但沒有頁的地方或概念。
   - 該互連卻沒連的頁（同城市的景點、同一天的景點）。
   - 日期已過但仍是 `planned/upcoming` 的造訪、所有 `unconfirmed`（待問）。
   - 造訪紀錄或日記裡出現心得、人名等不該有的內容（錯誤，直接刪）。
3. 輸出報告分三段：**錯誤（已修）**、**建議（待 Percy 決定）**、**待問**。記一筆 log（`lint`）。

---

## 7. `index.md` 與 `log.md`

### 7.1 `wiki/index.md`

每頁一行：`- [[slug]] <標題> — <一句摘要>`，依類別分組。每次 ingest 都要更新。

```markdown
# 索引

> 共 <N> 頁 · 最後更新 <YYYY-MM-DD>

## 總覽
- [[overview]] 全部旅程總覽

## 國家
- [[jp]] 日本 — 1 趟旅程、<N> 個城市

## 旅程
- [[<trip>]] <旅程名稱> — <一句>
  - [[<trip>/day-01]] 第 1 天 <主題>

## 都道府縣／縣市／州
- [[<region>]] <中文名> — [[<city>]]、[[<city>]]

## 城市與地區
- [[<city>]] <中文名> — <國家>，<N> 個景點

## 景點
### <城市中文名> [[<city>]]
- [[<place>]] <中文名> — <一句>

## 筆記
- [[<note>]] <標題> — <一句>
```

### 7.2 `wiki/log.md`

只增不改。新的寫在**最下面**。標頭格式固定，方便 `grep "^## \[" wiki/log.md | tail -5`：

```markdown
## [YYYY-MM-DD] <操作> | <標題>
- 新增：[[slug]]、[[slug]]
- 修改：[[slug]]（改了什麼）
- 待問：<問題>
```

`<操作>` 只能是：`init`、`ingest`、`query`、`lint`、`schema`（改 AGENTS.md）、`build`（改網站或 scripts）。

---

## 8. Raw 檔格式建議（給 Percy 與產生行程的 AI）

`raw/` 接受任何格式；以下是**新**資料建議用的模板，讓 ingest 更準。已經有的檔（例如日本的原版行程）保持原樣。

### 8.1 行程 `raw/plans/<trip>/plan-v1.md`

```markdown
---
trip: <YYYY-MM-主題>
version: 1
created: <YYYY-MM-DD>
author: <AI 模型名稱 或 Percy>
start: <YYYY-MM-DD>
end: <YYYY-MM-DD>
timezone: <IANA 時區>
countries: [<CC>]
---

# <旅程名稱> 行程 v1

## 概要
<一段話：主題、交通方式、節奏>

## Day 1 — <YYYY-MM-DD> — <城市或地區>

| 時間 | 地點 | 當地原名 | 類別 | 說明 |
| --- | --- | --- | --- | --- |
| 09:00 | 哈爾格林姆教堂 | Hallgrímskirkja | religious | 抵達後先去，登塔看市景 |

- 交通：<例：租車，Keflavík → Reykjavík 50 分>
- 住宿區域：<只寫區域，例：Reykjavík 市中心>

## Day 2 — …
```

### 8.2 日記 `raw/journal/<trip>/YYYY-MM-DD.md`

Percy 可以照這個格式自己寫，或把原始日記貼給 AI，由 AI 依 6.2 步驟 A 過濾成這個格式。只有三種資訊：

```markdown
---
trip: <trip>
date: <YYYY-MM-DD>
filtered: true   # 依 AGENTS.md 8.2 過濾：只留移動方式、景點、天氣
---

# <YYYY-MM-DD> <城市或地區>

- 移動：
  - <交通工具> → <地點>
- 景點：
  - <地點名稱>（<補充，例：只到入口>）
- 原定：<原本計畫的景點>
- 原定沒去：<地點>（<天氣原因，若有>）
- 改變：<行程怎麼改，例：提前到今天>
- 天氣：<日記有寫才填，沒寫就寫（未記）>
- 待確認：<名稱不確定的地方>
```

### 8.3 軌跡與照片

- GPX：`raw/gpx/<trip>/` 下任意檔名，一天一檔或整趟一檔都可以。
- 照片：`raw/photos/` 下，檔名用景點名最好；保留原始 EXIF（GPS 與時間只在本機用來對應，處理完原檔會刪掉）。
- 行政區圖片：`raw/regions/<region>.jpg`（例 `kyoto-pref.jpg`），任何比例都可以，會置中裁成正方形。

---

## 9. 網站

### 9.1 技術

| 部分 | 選擇 |
| --- | --- |
| 產生器 | Python（uv）＋ `pyyaml`、`markdown`、`jinja2`、`pillow`；`tracks.py`、`stations.py`、`geocode.py` 只用標準庫 |
| 地圖 | Leaflet 1.9.4（放在 `templates/static/leaflet/`）＋ OpenStreetMap 圖磚（免 API key，保留 © OpenStreetMap 標註） |
| 座標 | ingest 時寫進 frontmatter，網頁載入時**不**查座標 |
| 部署 | `.github/workflows/pages.yml`：push 到 `main` → `uv run scripts/build.py` → `actions/deploy-pages` |
| 網址 | `https://youping13.github.io/world-tour-llm-wiki/` |

### 9.2 風格：地圖全幕

- **每一頁都是全螢幕地圖**，頁面內容放在浮在地圖上的**側邊面板**。
  - 桌機：左側面板寬 420 px，可收合。
  - 手機（< 768 px）：底部抽屜，預設高度 45%，可拉到全螢幕。
- 頂列：站名「世界遊記」、搜尋框（搜 `places.json` 的中文名與原名）、「旅程」「索引」兩個連結。
- 深色 / 淺色跟系統設定，也可手動切換；深色模式地圖圖磚套 CSS 濾鏡變暗。
- 字型：Noto Sans TC（Google Fonts），內文 16 px，面板內行高 1.7。
- 不使用 emoji 當裝飾。

### 9.3 每種頁面在地圖上的樣子

| 頁面 | 網址 | 地圖範圍 | 面板內容 |
| --- | --- | --- | --- |
| 首頁 | `/` | 全世界所有景點 | `overview.md`、旅程列表、圖例 |
| 國家 | `/countries/<cc>/` | 該國 | 國家頁 |
| 行政區 | `/regions/<region>/` | 該行政區所有景點 | 行政區頁 |
| 城市 | `/cities/<city>/` | 該城市所有景點 | 城市頁 |
| 旅程 | `/trips/<trip>/` | 旅程全部景點＋計畫線＋實際線 | 旅程頁 |
| 日程 | `/trips/<trip>/day-NN/` | 當天景點＋當天兩條線 | 日程頁 |
| 景點 | `/places/<place>/` | 以景點為中心、zoom 15 | 景點頁＋照片 |
| 筆記 | `/notes/<slug>/` | `about` 裡的景點 | 筆記頁 |
| 索引 | `/wiki/` | 全世界 | `index.md` |

### 9.4 地圖標記與路線

三種東西的顏色**互相分開**：景點看類別、路線看旅程、行政區大圓各自一色。**縮放分工**：縮小（zoom ≤ 8）只看行政區大圓，放大（zoom ≥ 9）才出現景點和車站的小圈圈，避免全部疊在一起。

| 圖層 | 樣式 | 什麼時候出現 |
| --- | --- | --- |
| 行政區大圓 | 直徑 52 px 圓形（zoom 6 縮成 42 px、zoom ≤ 5 縮成 32 px），白框；有 `icon` 顯示圖片，沒有就寫 `label`。有去過的景點 → 實心；只有計畫 → 白底虛線框。點了進行政區頁 | zoom ≤ 8；日程頁、景點頁不顯示 |
| 景點 | 圓形＋類別圖示，**顏色＝類別**（`scripts/common.py` 的 `CATEGORY_COLORS`）。**大小看大類**：`visited` 大（30 px）、`planned` 小（20 px）。**樣式看小類**（5.2 表格最後一欄） | zoom ≥ 9；日程頁、景點頁一直顯示 |
| 車站 | 同景點規則，但是圓角方形、小一號，放在獨立圖層「車站」；彈出卡片多顯示 `lines` | 同景點，可關 |
| 計畫路線 | 旅程顏色、虛線 | 跟著「計畫」勾選 |
| 實際路線 | 旅程顏色、實線（GPX；沒有就用 `actual` 順序連線） | 可關 |

- 類別顏色：landmark 藍、religious 紫、museum 棕、nature 綠、viewpoint 青、food 洋紅、shopping 靛、activity 金、station 灰藍、transport 灰、lodging-area 深棕。旅程顏色（trip 的 `color`）要避開這些顏色。
- 點標記 → 彈出卡片：標題、類別、status、日期、縮圖、「看全文」連結。
- **計畫預設隱藏**：大類是 `planned` 的景點、計畫路線、只有計畫的行政區大圓，都放在「計畫」圖層，**預設不顯示**，右上角勾「計畫（景點、虛線路線）」才出現。例外：畫面範圍內一個去過的地方都沒有（例如還沒出發的旅程頁），就自動勾起來；景點頁自己那個點一定顯示。
- 右上角圖層開關（桌機預設展開、手機收合）：行政區、景點、車站、實際路線、計畫。

### 9.5 日期顯示（隱私）

- `start` 在今天之後的旅程（未發生）：網站上日期**只顯示到月**（`2027-06`），日程頁只寫「第 N 天」。
- 已發生的旅程：顯示完整日期。
- 這條由 `build.py` 處理，wiki 的 Markdown 保留完整日期。

### 9.6 Build 產物

`site/` 結構對應 9.3 的網址，另外：

- `site/data/wiki.json`：所有景點（slug、title、lat、lng、category、visits、縮圖）、旅程、每天的計畫線與實際線。網頁的地圖與搜尋都讀這個檔。

---

## 10. 隱私規則（最高優先）

網站是公開的。AI 在 ingest、寫頁、build 時都要遵守，和其他規則衝突時以這裡為準。

1. **照片**一律清除所有中繼資料（GPS、時間、相機型號…）再放進 `assets/`；GPS 只在本機用來對應景點。
2. `raw/photos/` 原圖不進 git（`.gitignore`）。
3. **GPX** 公開前刪掉旅程國家以外的段落（台灣的家、學校），再去掉每天頭尾各 500 m 並簡化；原始 GPX **不進 git**（含住處位置），公開的只有 `assets/tracks/`。
4. **`raw/` 也會公開**（除了 `raw/photos/`、`raw/gpx/` 與 `*.private.*`）：`raw/journal/` 只能放過濾後的日記，原始日記不進 repo、不進 AI 記憶；含私人資訊的原版行程用 `*.private.*`（6.1）。
5. **住宿**只寫到城市或區域（`lodging-area`），不寫飯店名、地址、房號。
6. **未來日期**在網站上只顯示到月（9.5）。
7. **他人**：不寫任何人名、外貌、不放正臉照、不放聯絡方式。
8. 不放護照、訂位代碼、機票、車票、QR code、信用卡的照片或內容。
9. 照片一律 144p（單張約 5～15 KB），repo 才不會變大；raw 原檔處理完就刪。

---

## 11. AI 修改與新增的規則

| 類別 | 項目 |
| --- | --- |
| **可以直接做** | 新增、修改 `wiki/` 的頁；跑 scripts 產生 `assets/`；修改 `scripts/`、`templates/`、`README.md` |
| **先問 Percy** | 修改 `AGENTS.md`（說明要改什麼、為什麼，同意後改，記 `schema` log）；刪除或改名 wiki 頁（改名要同步改所有 `[[連結]]`）；新增 Python 相依套件；改網站整體風格；git push |
| **不可以** | 動 `raw/`（日記存檔例外，第 0 節）；編造任何造訪紀錄；寫入心得或人物；違反第 10 節；commit `raw/photos/` 或 `site/`；`git push --force`；動 repo 以外的檔案 |

其他：

- 不確定就問，不要猜。尤其是：地名對應不到、status 判定不了、座標查不到。
- 一次 ingest 一份來源；多份來源時一份一份做，每份各寫一筆 log。
- 客觀介紹（「清水寺是…」）可以用 AI 的一般知識，但不能寫成 Percy 的經驗。
- commit 訊息格式：`<操作>: <標題>`，例：`ingest: 2027-06-iceland plan-v1`。

---

## 12. 驗收條件

### 12.1 每個任務完成前

- [ ] `uv run scripts/lint.py` 0 錯誤
- [ ] `uv run scripts/build.py` 成功
- [ ] 新增或修改的頁都有該類型的全部必填欄位
- [ ] `wiki/index.md` 列出所有頁
- [ ] `wiki/log.md` 新增一筆
- [ ] 沒有把 `> 待補` 換成編造的內容；`visited`（除了 `unconfirmed`）都同時有 journal 和 gpx（或 percy）
- [ ] 向 Percy 回報：改了哪些頁、待問清單

### 12.2 `lint.py` 檢查項目

| 檢查 | 等級 |
| --- | --- |
| frontmatter 缺必填欄位、`type` 不在七種之內 | 錯誤 |
| city 沒有 `region`，或 region 頁不存在 | 錯誤 |
| region 的 `icon` 檔不存在，或 `icon` 和 `label` 都沒有 | 錯誤 |
| slug 重複、檔名和 slug 不一致 | 錯誤 |
| place 沒有 `lat`/`lng`，或座標不在 `country` 的範圍內 | 錯誤 |
| `[[連結]]` 指向不存在的頁 | 錯誤 |
| `status` 不是 `planned`／`visited`，或 `detail` 不是該大類的小類 | 錯誤 |
| `visited`（除了 `unconfirmed`）的 `evidence` 不是同時含 `journal`＋`gpx`，也沒有 `percy` | 錯誤 |
| 小類是 `unconfirmed` 的造訪 | 待問 |
| `index.md` 沒列到的頁 | 錯誤 |
| `sources` 指向不存在的 raw 檔 | 錯誤 |
| `lodging-area` 標題像飯店名（含 Hotel、Hostel、旅館…） | 錯誤 |
| 沒有任何頁連到它的孤兒頁 | 警告 |
| 日期已過仍是 `planned/upcoming` | 待問 |
| `assets/photos/` 裡還帶 EXIF 的檔 | 錯誤 |

---

## 13. 範例：新增一趟旅程

以「冰島」為例，示範這份規則怎麼讓 AI 接著做下去。

1. **Percy**：請 AI 依 8.1 模板產生冰島行程，存成 `raw/plans/2027-06-iceland/plan-v1.md`，然後說「ingest 2027-06-iceland 的 plan」。
2. **AI** 讀 AGENTS.md、index、log → 列 todo：
   - 建 `wiki/countries/is.md`
   - 建行政區頁：`capital-region`、`south-region`…（冰島的一級行政區）
   - 建城市／地區頁：`reykjavik`、`golden-circle`、`south-coast`…（`region` 指向上一行）
   - 建約 20 個 place 頁（geocode 查座標）
   - 建 `wiki/days/2027-06-iceland/day-01.md` ～ `day-NN.md`
   - 建 `wiki/trips/2027-06-iceland.md`（`status: planned`、新顏色）
   - 更新 `overview.md`、`index.md`、`log.md`
3. **AI** 摘要行程給 Percy 確認 → 照第 4 節模板建頁 → 所有 place 的 `## 造訪紀錄` 都是 `> 待補`。
4. **AI** 跑 lint、build；網站首頁的世界地圖多出冰島的空心標記與虛線路線，日期只顯示 `2027-06`。
5. **旅行後**：Percy 把 GPX 放進 `raw/gpx/2027-06-iceland/`，把日記貼給 AI → AI 依 6.2 步驟 A 過濾存檔 → 依 6.3、6.2 步驟 B 比對：journal 和 GPX 都有的變實心或星形，只有一邊的變問號並列出來問 Percy。

日本（`2026-08-japan`，已完成）走同樣的流程，只是資料一次到齊：6.2 步驟 A（日記已過濾存檔）→ 6.1（原版行程）→ 6.3（GPX）→ 6.2 步驟 B。
