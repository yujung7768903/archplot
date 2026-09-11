# archplot

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | 日本語

アーキテクチャ図をコードで描くための Claude Code skill です。ノード・境界・エッジを**座標を明示
して**宣言する小さな Python ジェネレーターを書き、それを実行して `.drawio` を生成し、headless
Chromium と同梱の draw.io viewer で PNG をレンダリングします。draw.io Desktop も `xvfb` も
`sudo` も不要です。

クラウドベンダーのアイコンは [`diagrams`](https://github.com/mingrammer/diagrams) パッケージが
同梱する公式アイコン PNG を読み、base64 の data URI として `.drawio` に直接埋め込みます。その
ため単一ファイルで自立します。draw.io 自身の図形は境界ボックス（アカウント・リージョン・VPC・
サブネット）にのみ使います。

> [!NOTE]
> 座標を手で指定するのは意図的な選択です。自動レイアウトではラベルの重なりと無駄な余白を
> 取り除けないため、この skill はレイアウトの自動化を捨ててキャンバスの完全な制御を取ります。
> 自動化されているのは機械的な部分、すなわちエッジの配線です。

## 特徴

- **座標を自分で決める** —— 78x78 のアイコンノードを 20px グリッドに載せ、境界ボックスは中身に
  合わせて詰めます。
- **直交エッジルーター** —— 全ノードを配置したあと、ルーターが接続点を選び 90 度の経路を計算して
  waypoint として固定します。直線 → L → Z → 迂回の順に試し、成立する経路がなければ黙って斜線を
  引くのではなく `RuntimeError` を投げます。アイコンやフロー枠に加え、グループラベルとノード
  キャプションの**文字ボックス**も障害物として扱います。
- **2,440 のベンダーアイコン**、17 系統（執筆時点で `diagrams` が同梱するもの） —— `aws`、`gcp`、`azure`、`k8s`、`onprem`、`saas`、
  `generic`、`programming`、`elastic`、`firebase`、`alibabacloud`、`oci`、`ibm`、
  `digitalocean`、`openstack`、`outscale`、`gis`。
- **Chromium があればどこでもレンダリングできる** —— draw.io viewer を同梱しているため、GUI も
  デスクトップアプリも不要です。draw.io Desktop CLI の export モードが WSL では止まってしまう
  ため、この方式で作られています。
- **agent 向けの作図ルール** —— `SKILL.md` に、AWS のリファレンスアーキテクチャ図 4 枚を突き
  合わせて定めたルール群があり、agent が場当たりでなく一貫して描けます。
- **Confluence への公開（任意）** —— レンダリングした PNG をページに添付し、md5 で検証します。

## はじめかた

### 必要なもの

| 要件 | 備考 |
| --- | --- |
| Python 3 | 標準ライブラリのみ。追加のランタイム依存はありません |
| `pip install diagrams` | ジェネレーターが読むベンダーアイコン PNG を提供します |
| Chromium | `~/.cache/ms-playwright` または `~/.cache/puppeteer` を自動探索し、なければシステムの `chromium` / `chromium-browser` / `google-chrome` |
| Confluence への公開（任意） | 環境変数 `CONFLUENCE_SITE`、`CONFLUENCE_EMAIL`、`CONFLUENCE_API_TOKEN` が必要です |

### インストール

```bash
npx skills add yujung7768903/archplot
```

### 動作確認

どちらのスクリプトも自己点検を備えています。

```bash
python3 scripts/drawio_build.py    # demo OK
python3 scripts/drawio_route.py    # drawio_route: ok
```

## 仕組み

正本はジェネレーターの `.py` ひとつです。`.drawio` と PNG はビルド成果物であり、手で編集しま
せん。おかしく見えたら座標を直して手順 2 からやり直します。

| 手順 | コマンド | 確認できること |
| --- | --- | --- |
| 1. ジェネレーターを書く | `<name>.py` にノード・境界・エッジを座標つきで宣言する | — |
| 2. `.drawio` を生成 | `python3 <name>.py` | 境界数とセル数を出力 |
| 3. PNG をレンダリング | `python3 ~/.claude/skills/archplot/scripts/drawio_render.py <name>.drawio` | キャンバスサイズを出力 |
| 4. PNG を目で見る | 画像を開く | 重なり・切れ・線のもつれは終了コードには出ません |
| 4-1. 拡大して見る | `python3 ~/.claude/skills/archplot/scripts/drawio_crop.py <name>.png <x> <y> <w> <h> --zoom 2` | 全体 1 枚では足りません。縮小すると 1.2px の線が文字の画のように見え、ラベルを貫く線が現れません。各グループ枠の左上（ラベルのある位置）と長いキャプションの周辺を、1 か所ずつ拡大します |
| 5. 公開（任意） | `python3 ~/.claude/skills/archplot/scripts/confluence_publish.py <name>.png --page <id>` | md5 一致を出力 |

## ジェネレーターを書く

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/archplot/scripts"))
from drawio_build import Diagram, icon

d = Diagram("Title")

d.group("g1", "Ops account", 200, 80, 400, 200)          # boundaries before nodes
d.group("g2", "Service account", 200, 360, 900, 230)

d.node("actor", "Operator", 40, 140, icon("onprem/client/user"))   # actors sit outside
d.node("api", "API", 260, 140, icon("aws/compute/ec2"))
d.node("db",  "DB",  480, 140, icon("aws/database/aurora"))

d.edge("e1", "", "actor", "api", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e2", "store", "api", "db", exit=(1, 0.5), entry=(0, 0.5))
d.edge("e3", "callback", "db", "api", exit=(0.5, 0), entry=(1, 0.85), dashed=True,
       waypoints=[(519, 40), (368, 40)], label_pos=0, label_offset=(0, -12))

d.save("out.drawio")
```

skill に組み込まれているレイアウトの指針です。

- アイコンノードは 78x78。座標は 20px グリッドに合わせます。
- 同じ行では `y` をそろえ、列の間隔は均一に保ちます。
- 主たる流れの軸を 1 本決め（左→右 または 上→下）、戻る線は破線で性質を分けます。
- 境界ボックスは中身に合わせて詰めます。余った空間は未完成に見えます。
- ボックス内側の余白は最低 20px、ラベルのある辺は 40px を確保します。
- 同じノードの同じ辺に 3 本以上の線を付けません。キャプションはアイコンの下にあり隠れます。
- キャプションはアイコンの下に中央揃えで描かれ、幅の制限がありません。したがって**キャプション
  がアイコン（78px）より広いノードは、下辺の接続点を使いません** —— その線が文字を縦に貫きます。
- 代わりに流れをそろえます。下りの流れは出発ノードの**横の辺**から出て対象の**上辺**へ入り、
  上りの流れは**上辺**から出て対象の**横の辺**へ入ります。上りの線を受けるノードはその行の端に
  置き、横の辺を空けます。
- 間隔の目安: キャプションが 1 行なら行 160px・列 200px から始めます。3〜5 行のキャプションが
  混ざる場合は行 220px・列 240〜300px が必要です。
- `exit` と `entry` は省略できません。指定しないと draw.io が任意の位置に線を付け、キャプション
  に重なります。

## エッジ配線

エッジが 10 本を超えるか、条件のひし形が混ざったら、`exit` / `entry` / `waypoints` を手で指定
するのをやめて `Panel` を使います。配線は `save()` の時点で計算されます。

```python
from drawio_build import Diagram, icon
from drawio_route import Panel, beside

DIAMOND = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D86613;fontSize=11;"

d = Diagram("Title")
p = Panel(d, "a", 0, 0)                            # id prefix + coordinate offset
p.group("g_vpc", "VPC", 200, 60, 700, 260, kind="vpc")
p.step("q", "Allowed?", 420, 140, DIAMOND, 190, 58)
p.node("api", "API", 260, beside(p, "q"), icon("aws/compute/ec2"))
p.node("db", "DB", 720, beside(p, "q"), icon("aws/database/aurora"))
p.edge("e1", "tool call", "api", "q")              # the router picks points and path
p.edge("e2", "allowed only", "q", "db")
d.save("out.drawio")
```

| ルール | 理由 |
| --- | --- |
| 画像図形は各辺 3 点ずつの 12 接続点のみ。四隅は使いません | 角から出た線はアイコンから浮いて見えます |
| ひし形は 4 頂点と斜辺中央 4 点のみ。斜辺中央は `(x, y, "h"\|"v")` と書いて出る向きまで決めます | `(1, 0.75)` のような外接矩形上の点はひし形の輪郭の外にあり、draw.io が斜辺へ投影するため最初の区間が斜めになります |
| 境界グループやその他の通常図形は辺の中央 4 点。グループ自体もエッジの端点になれます | サブネット全体が送るエッジのため |
| 直線 → L → Z → 迂回の順。両端点が同じ x か同じ y なら直線 | 曲がりは情報ではありません |
| 最初の区間は接続点のある辺が向く方向へ出ます。横の辺から出るなら対象がその横に、上下の辺から出るなら対象がその上下になければなりません。入る側も同じです | そうでないと最初の区間がノードの内側へ食い込みます。これに反すると `RuntimeError` になりますが、メッセージは「障害物に阻まれた」と「方向規則に反した」を区別しません —— まずこの規則を疑ってください |
| グループラベル（枠の左上）やノードキャプション（アイコンの下）を横切る経路は大きく減点されます。避けようがない場合は経路を残したうえで stderr に警告を出します | そうしないと最短経路が文字の中を突き抜けます。警告が出たらノードや枠を動かしてその列を空けてください。縮小した PNG では文字を横切る線がほとんど見えません |
| ひし形の隣のアイコンは `beside(p, cid)` で垂直中心をそろえます | 10px ずれると 4.5px の小さな折れが生じます |
| 入る点は何とも重ねません。出る線と衝突する場合は斜辺中央に固定します（`ep=(0.75, 0.25, "h")`） | 出る線が頂点を失うと斜めになります |
| 同じ 2 ノード間のリクエスト／レスポンス 2 本は `sp=` / `ep=` で車線を固定します | スコアだけではどちらが上を通るか決まりません |
| `off=` は Z の中間線の位置を動かします | ルーターはグループ境界を障害物として見ないため、ボックス内をなぞる経路を自力で避けられません |
| 折れた経路の直線区間は `MIN_SEG`（24px）以上。守れない場合は stderr に警告 | 短い区間は小さな折れに見え、線がノードに張り付いて読めます。2 ノードの間隔を広げてください |
| 成立する経路がなければ `RuntimeError` | 配置を直せという合図です。黙って斜線を引きません |

`drawio_route` を import するとエッジが `edgeStyle=none` に切り替わり、waypoint がそのまま
描かれます。ラベルの背景は白になります。`lp=` でラベルを線上で動かせます。

## アイコン

推測せずに名前を検索してください。パスを誤ると `FileNotFoundError` で即座に失敗します。

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/skills/archplot/scripts')
from drawio_build import find_icon; print(find_icon('mediaconvert'))"
```

結果はそのまま `icon()` に渡します。例: `icon("aws/compute/ec2")`、`icon("gcp/compute/gke")`、
`icon("onprem/client/user")`。

### 境界の種類

`d.group(...)` の `kind=` に渡します。入れ子は アカウント > リージョン > VPC > サブネット の順に
重ねます。

| `kind` | 用途 |
| --- | --- |
| `account`（既定） | アカウント境界 |
| `cloud` | AWS Cloud 全体 |
| `region` | リージョン |
| `vpc` | VPC |
| `subnet` | サブネット |
| `autoscaling` | Auto Scaling グループ |
| `onpremise` | オンプレミス / 社内データセンター |

## 作図ルール

AWS のリファレンスアーキテクチャ図 4 枚を突き合わせて定めたものです。反する理由がなければ
agent はこれに従います。

| ルール | 観察 |
| --- | --- |
| 曲線は使わない。90 度の直交折れ線のみ | 4/4 |
| エッジラベルは 1〜3 語（データの種類・プロトコル・動作 1 語） | 4/4 |
| **1 つのリソースは 1 つのノード** —— prefix が違っても同じバケットなら 1 ノード | ルール |
| ノードラベルはサービス名、役割は括弧内。キャプションはアイコン下に最大 2 行 | 4/4 |
| アクターは 1 種のみ、常にすべての境界の外、エッジにラベルなし | 3/4 |
| 凡例は作らない。線種が 2 種類でも作りません | 4/4 |
| 流れに関わらないリソース（IAM・CloudWatch）はエッジなしで余白に置くか、外します | 3/4 |
| **アイコンがあるものだけがノードになる** | 4/4 |

最後の 1 行が抽象度を保つ仕掛けです。プロトコルや動作にはアイコンがないためエッジラベルへ押し
出され、関数名・URL パス・フィールド名はアイコンもエッジも得られず図から落ちます。例外は AZ
ごとのレプリカだけで、`MySQL (Master)` と `MySQL (Slave)` は実際に別のリソースなのでそれぞれ
ノードになります。

### 図に入れないもの

| 描かないもの | 代わりに |
| --- | --- |
| ストレージのパス・prefix・キーのパターン・ファイル名 | バケット名やキュー名までにとどめます |
| HTTP メソッド・URL パス・クエリパラメーター・ペイロードのフィールド名 | `encode options` のような 1〜3 語。パスは本文へ |
| エッジの通し番号 | 矢印の向きで順序が読めるよう配置します —— リファレンス 4 枚のうち番号を振ったものは 0 枚 |
| IAM ロールの ARN・STS AssumeRole の矢印 | 一切描きません |
| エラー経路・リトライ・タイムアウト・DLQ | 正常系 1 本だけ |
| 関数名・ハンドラー名・テーブルのカラム | サービス名と役割 |

## スクリプト

| ファイル | 役割 |
| --- | --- |
| `scripts/drawio_build.py` | `.drawio` の生成。`Diagram`、`icon()`、`find_icon()`。自己点検: `python3 drawio_build.py` |
| `scripts/drawio_route.py` | エッジ配線。`Panel`、`beside()`。接続点・直交経路・貫通判定を計算します。自己点検: `python3 drawio_route.py` |
| `scripts/drawio_render.py` | headless Chromium と `vendor/viewer-static.min.js` で `.drawio` を PNG に。`--scale` の既定は 2 |
| `scripts/drawio_crop.py` | レンダリングした PNG の一部を拡大します。ラベル貫通の点検用。レンダラーと同じ headless Chromium を使い、PIL も ImageMagick も不要です |
| `scripts/confluence_publish.py` | PNG をページに添付、またはページを作成。md5 で検証します |
| `vendor/viewer-static.min.js` | 同梱の draw.io viewer。デスクトップアプリも `xvfb` も不要になります |
| `reference/*.png` | 作図ルールの根拠にしたリファレンス 4 枚 |

### Confluence への公開

任意で、設定はすべて環境変数で行います —— `CONFLUENCE_SITE`、`CONFLUENCE_EMAIL`、
`CONFLUENCE_API_TOKEN`。

```bash
# refresh the attachment on an existing page (the page body is left alone)
python3 scripts/confluence_publish.py out.png --page <page-id>

# create a page under a parent and attach
python3 scripts/confluence_publish.py out.png --parent <id> --space <KEY> --title "Title"
```

> [!IMPORTANT]
> 同じファイル名で `POST /child/attachment` を再度呼んでも新しいバージョンにはなりません。この
> スクリプトは既存の添付 id を探し、`/{id}/data` へ送ります。別ツールとして存在する理由がこれ
> です。

## トラブルシューティング

| 症状 | 原因 | 対処 |
| --- | --- | --- |
| アイコンで `FileNotFoundError` | アイコンのパスを推測した | `find_icon()` で検索します |
| アイコンの場所が空の四角 | draw.io 自身の図形名を誤って使った | `icon()` を使います。draw.io の図形は境界専用です |
| キャプションが線に隠れる | 1 つのノードの同じ辺に 3 本以上の線を付けた | `exit` / `entry` を他の辺へ分散します |
| ラベル 2 つがつぶれて重なる | 同じ 2 ノード間に線が 2 本ある | 片方に `label_pos` / `label_offset` を設定します |
| 境界やキャプションが画像の端で切れる | キャンバスの余白が足りない | `drawio_render.py` の `PAD` 定数を上げます |
| レンダリングはできるがアイコンが出ない | AWS4 ステンシルを CDN から取得している | ネットワークを確認します |
| Confluence の添付バージョンが上がらない | 同じファイル名で `POST /child/attachment` を再送した | `confluence_publish.py` を使います |

## 作図ツールの選び分け

| 要望 | ツール |
| --- | --- |
| クラウド公式アイコン、アカウント・リージョン・VPC の境界 | この skill |
| 文書本文に埋め込むフロー図・シーケンス図・状態図 | Mermaid ベースの skill —— Confluence と GitHub がそのまま描画します |
| ピクセル単位の制御 | draw.io アプリを開いて手で描きます |

## 表記について

draw.io / diagrams.net、mxGraph、AWS、Google Cloud、Azure、Kubernetes その他すべての製品名・
ロゴ・アイコンは、各所有者の商標です。ベンダーのアイコン素材は
[`diagrams`](https://github.com/mingrammer/diagrams) パッケージが同梱するもので、各ベンダーの
条件に従って利用しています。

**無関係の明示。** 本プロジェクトは draw.io Ltd・draw.io AG・JGraph Ltd とは無関係であり、
いかなる保証・後援も受けていません。`draw.io` は権利者の登録商標です（EU 登録番号
#018062448）。

**同梱の viewer。** `vendor/viewer-static.min.js` は draw.io viewer v31.3.1 の無変更
（unmodified）コピーで、Apache License 2.0 のもとで提供されています。出所:
`https://github.com/jgraph/drawio/blob/v31.3.1/src/main/webapp/js/viewer-static.min.js`。
SHA256 により上流のタグ付きファイルとバイト単位で一致することを確認済みです。

**生成した図の責任は利用者にあります。** ベンダーごとにアイコンの条件は異なり、上流の
`diagrams` パッケージも同梱するアイコン素材のライセンスを公開していません。ベンダーアイコンを
含む図を公開する前に、各ベンダーの実際の記載をまとめた [THIRD-PARTY.md](THIRD-PARTY.md) を
確認してください。

**アイコンは再配布しません。** 本リポジトリはベンダーのアイコンファイルを含みません。実行時に
インストール済みの `diagrams` パッケージから読み込みます。ベンダーアイコンを本リポジトリに
コミットしたり、本リポジトリから再配布したりしないでください。

**アイコンを改変しないでください。** ベンダーアイコンの縦横比や色を変更しないでください ——
ベンダーの商標ガイドラインが求める事項です。

**レンダリング時に外部へリクエストが出ます。** 同梱の viewer は、ステンシル・図形・スタイルを
`viewer.diagrams.net` から取得することがあります。オフラインや閉域網では、draw.io 自身の図形の
一部が空の枠として描かれる場合があります。
