# 世界遊記 LLM Wiki

**網站**：<https://youping13.github.io/world-tour-llm-wiki/>

用 [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 的做法，讓 AI 把旅行資料——行程規劃、GPX 軌跡、旅途日記——「編譯」成一個以地圖為主、互相連結的旅遊百科。規則全部寫在 [`AGENTS.md`](AGENTS.md)，任何 AI 讀完就知道怎麼繼續新增旅程、景點與日記。

核心想法：**計畫**和**實際**是兩種來源。地圖上虛線是計畫路線、實線是 GPX 實際路線；景點的形狀代表它的狀態（照計畫去了、改期、臨時加、沒去、待確認）。

## 三層結構

| 層 | 位置 | 誰寫 |
| --- | --- | --- |
| 原始資料 | `raw/`（行程、過濾後的日記；GPX 與照片原檔不進 git） | 我放，AI 只讀 |
| Wiki | `wiki/`（國家、行政區、城市、旅程、日程、景點、筆記；`index.md`、`log.md`） | AI 維護 |
| 規則 | `AGENTS.md` | 我和 AI 一起改 |

網站 `site/` 由 `scripts/build.py` 從 `wiki/` 產生，push 到 `main` 後 GitHub Actions 自動部署。

## 目前內容

- `2026-08-japan` 日本東日本縱走（已完成）：原版行程、日記、GPX、44 個車站、12 個都道府縣
- 照片：360p、清掉所有中繼資料（`scripts/photos.py`）
- `2027-06-iceland` 冰島環島（規劃中）：AI 產生的行程

## 怎麼用

```bash
uv run scripts/tracks.py <trip>     # GPX → 公開軌跡（刪國外段、去頭尾 500 m）
uv run scripts/stations.py <trip>   # GPX × 車站資料 → 車站候選
uv run scripts/lint.py              # 健檢：0 錯誤才算完成
uv run scripts/build.py             # 產生網站到 site/
python -m http.server -d site       # 本機預覽 http://localhost:8000
```


## 檔案結構

```text
world-tour-llm-wiki/
├─ AGENTS.md          規則（schema），AI 每次開工先讀
├─ CLAUDE.md          一行 @AGENTS.md，讓 Claude 自動讀到規則
├─ pyproject.toml     uv 相依套件
├─ raw/               原始資料：我放，AI 只讀
│  ├─ plans/<trip>/       行程 plan-vN.md；含私人資訊的原檔叫 *.private.*（不進 git）
│  ├─ journal/<trip>/     過濾後的日記（只有移動、景點、天氣）
│  ├─ gpx/<trip>/         GPX 原檔（不進 git）
│  ├─ photos/             照片原檔（不進 git），放進來＝同意公開，處理完刪除
│  └─ regions/            行政區大圓圖片原檔（不進 git），處理完刪除
├─ wiki/              AI 寫的百科：index.md、log.md、overview.md、countries/ regions/ cities/ trips/ days/ places/ notes/
├─ assets/            script 產生的公開檔：tracks/（處理過的 GPX）、photos/（360p、清過中繼資料）、regions/（行政區圖片）
├─ scripts/           tracks / stations / photos / geocode / lint / build
├─ templates/         網站外觀：page.html、static/style.css、static/app.js
├─ .github/workflows/ push 後自動 lint → build → 部署
├─ reports/           給我看的待問清單、車站比對（不進 git）
├─ .cache/            下載的車站資料（不進 git）
└─ site/              build 產物（不進 git，由 Actions 產生）
```

分工：`raw/` 我負責，`wiki/` AI 負責，`AGENTS.md` 一起改，網站全自動產生。wiki 頁是 AI 依 `AGENTS.md` 直接寫的 Markdown，沒有自動 ingest 的 script。

## 維護

每次開一個 AI 對話，第一句都先說：

```
讀 AGENTS.md、wiki/index.md、wiki/log.md 最後 5 筆，然後：
```

### 規劃新旅程

1. 行程放 `raw/plans/<YYYY-MM-主題>/plan-v1.md`（或請 AI 依 `AGENTS.md` 8.1 模板產生）
2. 對 AI 說：`ingest <trip> 的 plan`
3. AI 先摘要給我確認，再建頁、跑 lint、build

### 旅行回來

1. GPX 放 `raw/gpx/<trip>/`
2. 對 AI 說：`這是 <trip> 的日記，依 AGENTS.md 6.2 過濾存檔：`，再貼上原始日記
3. 對 AI 說：`跑 tracks.py 和 stations.py，然後 ingest <trip> 的 journal`
4. 回答 AI 給的車站比對（`reports/<trip>-stations.md`）與待確認清單，它才會寫頁

### 加照片

1. 把願意公開的照片放 `raw/photos/`，檔名寫景點名（例：`淨土之濱.jpg`）
2. 對 AI 說：`跑 photos.py --delete-raw，把照片掛到景點頁`（360p、清中繼資料、刪原檔）

### 加行政區圖片（地圖上的大圓）

1. 圖片放 `raw/regions/<region>.jpg`，例 `kyoto-pref.jpg`（slug 見 `wiki/index.md` 的「都道府縣／縣市／州」）
2. 對 AI 說：`跑 photos.py --regions --delete-raw，把 icon 填進行政區頁`
3. 沒給圖片的行政區會顯示文字（例：京都）

### 回答「待確認」

`uv run scripts/lint.py` 最後會列出待問。直接告訴 AI，例如：

```
新宿：有去，從新宿站出來逛了一小時
銀山溫泉：沒去
```

AI 會改成 visited 或 skipped，證據記 `percy`。

### 改規則、改外觀

- 改規則：說「AGENTS.md 第 X 節改成…」，AI 改完記一筆 `schema` log
- 改外觀：改 `templates/static/style.css` 或 `templates/page.html`

### 注意

1. 不要手改 `site/`，每次 build 都會覆蓋。內容改 `wiki/`，外觀改 `templates/`。
2. 原始日記、含飯店或花費的行程不要直接放進 `raw/`，交給 AI 過濾；原檔要留的話檔名加 `.private`。
3. push 前跑一次 `uv run scripts/lint.py`。Actions 也會跑，有錯誤就不會部署。

完整範例見 `AGENTS.md` 第 13 節。

## 授權與資料來源

- 地圖：[Leaflet](https://leafletjs.com/)（BSD-2）、© [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors
- 車站資料：[open-data-jp-railway-stations](https://github.com/piuccio/open-data-jp-railway-stations)（ekidata），只在本機比對用
- 冰島行程參考 [Nordic Visitor — Iceland Ring Road in 8 Days](https://www.nordicvisitor.com/iceland/self-drive-tours/iceland-ring-road-in-8-days/2270/) 修改
