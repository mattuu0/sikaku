# sikaku

基本情報技術者試験(FE)の過去問を表示・採点する Web アプリ (FastAPI + 静的フロント)。
IPA の公開ページから過去問/解答 PDF を取得して解析する **updater** を、1日1回自動実行します。

## 構成

[Dockerfile](Dockerfile) のターゲットごとに、2 つの別イメージをビルドします (依存関係も別)。

| ターゲット | ghcr.io のイメージ | 役割 |
|---|---|---|
| `web` | `ghcr.io/<owner>/launchs-7207b262-269e-4265-b4f8-c2d430c28ba8` | Web / API (`uvicorn`, ポート 11188) |
| `updater` | `ghcr.io/<owner>/launchs-f8a14c6a-98b1-4a99-ae28-9035bb88cebf` | 起動時 + 24時間ごとに IPA から取得・解析 (`update_loop.sh`) |

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
2. **updater**: `launchs-f8a14c6a-98b1-4a99-ae28-9035bb88cebf` イメージ (コマンド指定は不要)、同じボリュームを `/app/extractor/datas` にマウント

## CI/CD (GitHub Actions)

[.github/workflows/deploy.yml](.github/workflows/deploy.yml)

| ブランチ | 動作 |
|---|---|
| `develop` | web / updater の 2 イメージをビルドして ghcr.io に push (タグ: `develop`, コミット SHA)。デプロイはしない |
| `main` (リリース) | 2 イメージを push (タグ: `latest`, SHA) → web / updater をそれぞれ launchs に反映 |
| Pull Request | ビルドのみ (push しない) |

運用: 開発は `develop` に、リリース時に `develop` → `main` をマージ。

### 事前準備

1. リポジトリの Settings > Secrets and variables > Actions に登録
   - `LAUNCHS_URL`: `https://www.launchs.org`
   - `WEB_TOKEN`: web の deploy の「自動デプロイ(webhook)」トークン
   - `UPDATER_TOKEN`: updater の deploy の「自動デプロイ(webhook)」トークン
2. 初回実行後、ghcr.io のパッケージ `launchs-7207b262-269e-4265-b4f8-c2d430c28ba8` と `launchs-f8a14c6a-98b1-4a99-ae28-9035bb88cebf` を **Public** にする (launchs は非公開イメージを取得できない)

web と updater はジョブもトークンも別々です (`build-web` → `deploy-web`、`build-updater` → `deploy-updater`)。

## 権利・免責

- 本プロジェクトは個人が学習用に運営する非公式のもので、独立行政法人 情報処理推進機構 (IPA) とは関係ありません。
- 試験問題・解答の著作権は IPA に帰属します。
- 取得先は IPA が一般に公開しているページ (`https://www.ipa.go.jp/shiken/about/menjo-fe.html`) のみです。問題 PDF は IPA の URL へのリンクとして表示し、本サービスでは配布しません。解答は公開されている解答 PDF から採点用に読み取ったデータです。
- 取得は 1 日 1 回、リクエスト間に待機を挟んで行い、IPA のサーバーに負荷をかけないようにしています。
- **免責事項**: 解答の読み取りや採点結果の正確性・完全性は保証しません。正式な問題・解答は必ず IPA の公開ページで確認してください。本サービスの利用により生じたいかなる損害についても、運営者は責任を負いません。予告なく内容の変更やサービスの停止を行うことがあります。
- 掲載内容に問題がある場合は、速やかに対応します。
