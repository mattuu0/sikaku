# sikaku

基本情報技術者試験(FE)の過去問を表示・採点する Web アプリ (FastAPI + 静的フロント)。
IPA の公開ページから過去問/解答 PDF を取得して解析する **updater** を、1日1回自動実行します。

## 構成

[Dockerfile](Dockerfile) のターゲットごとに、2 つの別イメージをビルドします (依存関係も別)。

| ターゲット | ghcr.io のイメージ | 役割 |
|---|---|---|
| `web` | `ghcr.io/<owner>/launchs-7207b262-269e-4265-b4f8-c2d430c28ba8` | Web / API (`uvicorn`, ポート 11188) |
| `updater` | `ghcr.io/<owner>/sikaku-updater` | 起動時 + 24時間ごとに IPA から取得・解析 (`update_loop.sh`) |

web と updater は **ボリュームを共有** します (updater が書き、web が読む)。

## ローカル実行

```sh
docker compose up -d --build
# http://localhost:11188
```

初回は updater が PDF を取得し終わるまで (数分) 問題一覧が空です。進捗は `docker compose logs -f updater`。

依存関係は uv で管理 (`pyproject.toml` / `uv.lock`)。

```sh
uv sync            # ローカル開発用 .venv
uv add <package>   # 依存追加 (uv.lock も更新される)
```

## デプロイ時の設定

### ボリューム

| コンテナ内パス | 用途 | 対象 |
|---|---|---|
| `/app/extractor/datas` | 取得した PDF、解析結果 (`config.json`, `*/data.json`)、HTTP キャッシュ (`.webcache`) | web / updater **両方に同じボリュームをマウント** |

- web は読み取り専用 (`:ro`) で構わない。updater は書き込み可。
- マウントしないとコンテナ再作成のたびにデータが消え、再取得になる。
- ボリュームが空のあいだ `/get_fe_mondais` は問題を返せない (updater の初回完了まで)。

### 環境変数

| 変数 | 対象 | 既定値 | 説明 |
|---|---|---|---|
| `UPDATE_INTERVAL_SECONDS` | updater | `86400` | 更新間隔(秒) |
| `IPA_PAGE_URL` | updater | `https://www.ipa.go.jp/shiken/about/menjo-fe.html` | 過去問一覧ページ。取得に失敗した場合は同梱の `extractor/ipa_fe_html.html` にフォールバック |

ポートは `11188` (コンテナ内)。

### フロントの API URL

`static/config.js` の `base_url` は固定値です。デプロイ先の URL に合わせて変更してください。

### launchs へのデプロイ

launchs の webhook は 1 deploy = 1 イメージです。次の 2 つを作成してください。

1. **web**: web イメージ、ポート 11188、ボリューム → `/app/extractor/datas`
2. **updater**: `sikaku-updater` イメージ (コマンド指定は不要)、同じボリュームを `/app/extractor/datas` にマウント

## CI/CD (GitHub Actions)

[.github/workflows/deploy.yml](.github/workflows/deploy.yml)

| ブランチ | 動作 |
|---|---|
| `develop` | web / updater の 2 イメージをビルドして ghcr.io に push (タグ: `develop`, コミット SHA)。デプロイはしない |
| `main` (リリース) | 2 イメージを push (タグ: `latest`, SHA) → web を launchs に反映 |
| Pull Request | ビルドのみ (push しない) |

運用: 開発は `develop` に、リリース時に `develop` → `main` をマージ。

### 事前準備

1. リポジトリの Settings > Secrets and variables > Actions に登録
   - `LAUNCHS_URL`: `https://www.launchs.org`
   - `LAUNCHS_TOKEN`: launchs の「自動デプロイ(webhook)」で発行したトークン
2. 初回実行後、ghcr.io のパッケージ `launchs-7207b262-269e-4265-b4f8-c2d430c28ba8` と `sikaku-updater` を **Public** にする (launchs は非公開イメージを取得できない)

launchs への反映は web 用の webhook のみです。updater も自動で更新したい場合は、同様の webhook をもう 1 つ `deploy` ジョブに追加してください (`needs.build.outputs.updater_image` が使えます)。
