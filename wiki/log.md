# 工作紀錄

> 只增不改，新的寫在最下面。`grep "^## \[" wiki/log.md | tail -5` 看最近 5 筆。

## [2026-11-10] init | 建立專案與 AGENTS.md 第一版
- 新增：AGENTS.md、CLAUDE.md、raw/ 四個資料夾
- 決定：範圍從歐洲擴大到全世界；網站風格「地圖全幕」；未來日期只顯示到月

## [2026-11-10] schema | 日記只留移動／景點／天氣，journal＋GPX 同時出現才算
- 修改：AGENTS.md 第 0、5、6.2、8.2、10 節；新增 status `unconfirmed`；照片不當證據
- 修改：raw/tracks 改名 raw/gpx

## [2026-11-10] ingest | 2026-08-japan journal 步驟 A（過濾存檔）
- 新增：raw/journal/2026-08-japan/2026-07-31.md ～ 2026-08-15.md（16 個檔）
- 刪除：過程、心得、人物、比賽經過；原始日記不存檔、不進 AI 記憶
- 待問：9 個地名待確認 → Percy 已回覆（平等院沒進去、蒲郡、豐橋綜合動植物公園、常滑、熱田神宮、Resort Shirakami、鵜ノ崎海岸、門脇小學、大船渡線）

## [2026-11-10] schema | 新增車站類別與 6.3.1 車站流程
- 修改：AGENTS.md 4.1（station、lines）、6.3.1、9.4；新增 .cache/、reports/、.gitignore
- 新增：reports/2026-08-japan-stations.md（約 130 筆候選，AI 先填判斷）

## [2026-11-15] schema | 原檔含私人資訊時用 *.private.* 不進 git
- 新增：raw/plans/2026-08-japan/plan-v2.private.pdf（原檔，不公開）、plan-v2.md（AI 過濾版：刪住宿名、訂房連結、花費、電話）
- 修改：.gitignore 加 `*.private.*`；AGENTS.md 6.1 加過濾步驟

## [2026-11-15] build | scripts 與網站
- 新增：scripts/common.py、wikilib.py、tracks.py、stations.py、geocode.py、photos.py、lint.py、build.py
- 新增：templates/page.html、static/style.css、static/app.js、static/leaflet（1.9.4）
- 新增：pyproject.toml、.github/workflows/pages.yml

## [2026-11-15] ingest | 2026-08-japan GPX（tracks.py）
- 新增：assets/tracks/2026-08-japan/2026-07-30 ～ 2026-08-15.geojson（刪台灣段、去頭尾 500 m、簡化 20 m）
- 沒有 GPX 的日子：08-02、08-03、08-04

## [2026-11-15] ingest | 2026-08-japan 車站（Percy 確認）
- Percy 回覆：伏見稻荷是京阪站、千疊敷有下車；其他照 AI 判斷
- 新增：44 個 station 頁（evidence: gpx＋percy）

## [2026-11-15] ingest | 2026-08-japan plan-v2 ＋ journal 步驟 B
- 新增：[[2026-08-japan]]、day-01 ～ day-17、[[jp]]、30 個城市與地區頁、41 個景點頁
- 結果：照計畫 / 改期（[[jodogahama]]、[[matsushima-bay]]）/ 臨時加 / 沒去（[[omuroyama]]、[[oirase-stream]]、[[bandai-azuma-skyline]]、[[jododaira]]）
- 待問：見 lint 報告「待問」（unconfirmed 共 12 筆）

## [2026-11-15] ingest | 2027-06-iceland plan-v1
- 新增：raw/plans/2027-06-iceland/plan-v1.md（AI 參考 Nordic Visitor 8 天環島修改）
- 新增：[[2027-06-iceland]]、day-01 ～ day-08、[[is]]、9 個地區頁、34 個景點頁（全部 planned，座標 coord_source: manual）

## [2026-11-15] schema | 刪除真實姓名與學號
- 修改：AGENTS.md、README.md、[[overview]] 拿掉姓名與學號；git 歷史重建，舊 commit 不保留

## [2026-11-15] ingest | 照片 2 張（360p、清中繼資料）
- 新增：[[jogasaki-coast]]、[[jodogahama]] 的照片（短邊 360 px WebP）
- 拿掉：相機型號、拍攝時間與相機參數、軟體版本、廠商私有資料（兩張都沒有 GPS）
- 刪除：raw/photos 的 2 個原檔

## [2026-11-15] schema | 新增行政區頁與地圖大圓；標記改成依類別上色
- 新增：type `region`（AGENTS.md 4.5）、18 個行政區頁（日本 12 個都道府縣、冰島 6 個地區）
- 修改：所有城市頁加 `region`；地圖標記顏色＝類別、去過的放大；路線顏色＝旅程（日本紅、冰島橘）
- 修改：photos.py 改成 360p，新增 `--delete-raw`、`--regions`

## [2026-11-15] ingest | Percy 確認 12 筆待確認
- 改成去過：[[kansai-airport]]（7/30 過夜）、[[aichi-sky-expo]]（8/2～8/7 每天）、[[aeon-mall-tokoname]]（8/1、8/2 兩天）、[[kamakura-koko-mae-crossing]]
- 改成沒去：[[enoshima-toro]]（白天去江之島，晚上燈籠沒去）、[[lake-towada]]、[[ginzan-onsen]]、[[azuma-kofuji]]、[[zao-fox-village]]、[[matsushima-cruise]]、[[mitsuishizaki]]（只到入口）
- 刪除：新宿景點頁（只是經過；新宿站保留）
- 修改：day-05～day-09 計畫加入愛知國際展示場（原版行程寫「每天」）
- 待問：無

## [2026-11-15] schema | status 改成兩大類＋小類
- 修改：AGENTS.md 4.1、5.2、5.3、9.4、12；`status` 只剩 `planned`／`visited`，新增 `detail`（upcoming、skipped、unconfirmed、dropped／as-planned、moved、added、unconfirmed）
- 修改：所有景點頁的 visits、日程頁與旅程頁的「計畫 vs 實際」改用中文標籤（例：去過・照計畫）
- 修改：lint.py、build.py、地圖標記與圖例

## [2026-11-15] build | 地圖縮放分工
- 修改：zoom ≤ 8 只顯示行政區大圓（越小縮得越小），zoom ≥ 9 才顯示景點與車站；日程頁、景點頁一直顯示景點、不顯示大圓
- 修改：AGENTS.md 9.4

## [2026-11-15] build | 計畫預設隱藏，勾選才顯示
- 修改：`planned` 的景點、計畫路線、只有計畫的行政區放進「計畫」圖層，預設不顯示；畫面裡沒有去過的地方時（例：冰島）自動顯示
- 修改：AGENTS.md 9.4、圖例

## [2026-11-15] build | 照片改成 144p
- 修改：photos.py 短邊 144 px、縮圖 96 px；AGENTS.md 6.4、10
- 修改：[[jogasaki-coast]]、[[jodogahama]] 的照片重新縮成 144p（原檔已刪，從 360p 版縮小）
