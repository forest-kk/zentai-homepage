# 英語版（en/）の訳し方

日本語ページを直したら、同じ作業の中で `en/` の同じ名前のページも直す。このファイルはその訳し方と用語の決まり。

## 手順
1. 日本語ページ（例: `office.html`）で変えた箇所を確かめる（`git diff office.html`）
2. `en/office.html` の対応する箇所だけを英語で同じ内容に直す。日本語ページで増やしたブロック（表・カード・写真）は、英語版にも同じ形で増やす
3. 写真の差し替え（`?v=日付` を含む）や数字・電話番号・郵便番号の変更も、英語版に同じように反映する
4. サイト直下で `python3 tools/build_en.py` → `python3 tools/check_en.py --update` を実行する
5. プレビューで英語版のページも開いて、崩れていないか見る

## 書き方の決まり
- タグ・class・id・data-* 属性・順序は日本語ページと同じにする。変えるのは文字だけ
- ヘッダー・メニュー・フッターは `tools/build_en.py` が自動で作るので、手で直さない
- 英語版のパスは `../media/…` のように1つ上を指す（`build_en.py` が自動で直す）
- 海外の取引先向けの、落ち着いたアメリカ英語。短く平明に。原文にない事実や数字を足さない
- data-split の付いた見出しは短め（1行20〜25文字程度）
- 長い段落の途中の `<br>` は英語では外す（住所の改行は残す）
- 和暦は書かない。年は西暦、月は英語（August 1950）
- 英語版の本文に日本語を1文字も残さない（Googleマップのリンクの住所部分を除く）
- お知らせ・採用情報・働く環境は英語版がない。英語版からのリンクは `../news.html` などの日本語ページへ

## 用語
| 日本語 | 英語 |
|---|---|
| 株式会社フォレスト | FOREST Co., Ltd.（文中の繰り返しは FOREST） |
| 自然とともに、未来へ。 | Growing with nature, into the future. |
| 木材事業部 | Lumber Division |
| 物流・包装事業部 | Logistics & Packaging Division |
| 運送事業部 | Transport Division |
| タイヤ販売事業部 | Tire Sales Division |
| 織布事業部 | Weaving Division |
| ホテル事業部 | Hotel Division |
| 不動産事業部 | Real Estate Division |
| 太陽光発電事業部 | Solar Power Division |
| 会社概要 / 事業紹介 / 拠点・事業所一覧 | Company / Our Business / Locations |
| 安全と環境 / 関連リンク / お問い合わせ | Safety & Environment / Links / Contact |
| お知らせ / 採用情報 / 働く環境 | News / Careers / Working at FOREST |
| 事業所 / 営業倉庫 / 賃貸ビル | Offices / Commercial Warehouses / Rental Buildings |
| 本社 / 工場 / 倉庫 | Head Office / Factory / Warehouse |
| 代表取締役社長 小田 英輝 | Hideki Oda, President & CEO |
| 堂原工場 | Dohara Factory |
| フォレストビル水道町 / 東比恵 | FOREST Building Suidocho / FOREST Building Higashihie |
| FLC山鹿 | FLC Yamaga |
| スーパーホテル熊本・山鹿 | Super Hotel Kumamoto Yamaga |
| 天然温泉「山鹿灯籠の湯」 | Yamaga Toro no Yu natural hot spring |
| タイヤパークフォレスト | Tire Park FOREST |
| 株式会社カリク | Kariku Co., Ltd. |
| 創業 / 設立 | founded / incorporated |
| 資本金 30,000千円 | JPY 30 million |

人名は「名 姓」の順（Futaba Imai）。

## 住所
- 形式: `番地 町名, 市区, 県 郵便番号`（例: `9-26 Suidocho, Chuo-ku, Kumamoto-shi, Kumamoto 860-0844`）
- 地名の読みは推測しない。郵便番号で日本郵便の読み（カナ）を調べてローマ字にする（長音は省く: Ohashidori）
- 使用済みの表記: Kahokumachi Iwano / Kahokumachi Shicho / Sugi / Ohashidori（山鹿市）、Himekatamachi（鳥栖市）、Kamitsumachi（久留米市）、Kubaru、Sakae（合志市）、Yamaguma, Tachiarai-machi, Mii-gun、Higashihie, Hakata-ku, Fukuoka-shi
