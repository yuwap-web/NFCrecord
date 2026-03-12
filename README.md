# NFC Sheets Logger

SONY RC-380 NFC カードリーダーを使用して、カードタッチを自動的に Google Sheets に記録するシステムです。

## 概要

薬局での処方箋に関する電話問い合わせを記録するために設計されています。NFC カードをリーダーにタッチするだけで、タイムスタンプと対応内容が自動的にスプレッドシートに記録されます。

### 動作フロー

```
カードタッチ → 入力待ち（5秒）→ 記録 → カード取り外し → 次の待機
```

1. NFC カードをリーダーにタッチ
2. 5秒以内にキーを押して対応内容を選択：
   - **キー1**: 変更あり
   - **キー2**: 変更なし
   - **キー3**: 疑義照会（患者番号入力ダイアログが表示）
   - **5秒タイムアウト**: 自動的に「変更あり」で記録
3. Google Sheets に自動記録
4. カードを取り外して次の記録へ

**1回のタッチ = 1件の記録**が保証されます（状態マシンによる制御）。

## 必要な環境

| 項目 | 要件 |
|---|---|
| OS | Windows 10 以上 |
| NFC リーダー | SONY RC-380（USB接続） |
| Google アカウント | 個人アカウント（gmail.com）で OK、**Workspace 不要** |
| オプション | Stream Deck（ボタン入力用） |

## クイックスタート

### 1. EXE のダウンロード

[GitHub Releases](https://github.com/yuwap-web/NFCrecord/releases) から最新の `NFCrecord.exe` をダウンロード

### 2. フォルダ構成

以下の構成でフォルダを作成してください：

```
C:\NFCrecord\
├── NFCrecord.exe              ← ダウンロードした EXE
├── register_startup.bat       ← スタートアップ登録（任意）
├── unregister_startup.bat     ← スタートアップ解除（任意）
└── config\
    ├── config.yaml            ← 設定ファイル
    └── credentials.json       ← Google サービスアカウントの鍵
```

### 3. config.yaml の作成

`config\config.yaml` を以下の内容で作成してください。`spreadsheet_id` はご自身のスプレッドシートの ID に変更してください。

```yaml
google_sheets:
  spreadsheet_id: "あなたのスプレッドシートID"
  sheet_name: "NFC Logs"
  columns:
    - 日時
    - 問い合わせ内容
    - 変更の有無
    - 備考

nfc:
  reader_name: "SONY RC-380"
  poll_interval: 0.5

input:
  key_mappings:
    "1": "変更あり"
    "2": "変更なし"
    "3": "疑義照会"
  timeout_seconds: 5
  default_on_timeout: "変更あり"

gui:
  window_size: [600, 400]
  theme: "DarkBlue3"
  log_lines: 10
```

> **スプレッドシート ID の確認方法**: Google Sheets の URL `https://docs.google.com/spreadsheets/d/{この部分}/edit` の `{この部分}` がIDです。

### 4. Google Sheets API の設定

詳細は [セットアップガイド](setup/README_SETUP.md) を参照してください。

1. Google Cloud Console でプロジェクトを作成
2. Google Sheets API を有効化
3. サービスアカウントを作成し、JSON キーをダウンロード
4. ダウンロードした JSON を `config\credentials.json` として配置
5. スプレッドシートをサービスアカウントの email と共有（エディタ権限）

### 5. SONY RC-380 ドライバのインストール

1. SONY 公式サイトから RC-380 ドライバをダウンロード
2. インストール後、RC-380 を USB 接続
3. デバイスマネージャーで「PaSoRi」が表示されることを確認

### 6. 起動

`NFCrecord.exe` をダブルクリックして起動

## Windows 起動時の自動実行

Windows ログイン時に自動的に起動させることができます。

### 登録

`register_startup.bat` をダブルクリックするだけで完了です。

```
C:\NFCrecord\
├── NFCrecord.exe
├── register_startup.bat      ← ダブルクリックで登録
├── unregister_startup.bat    ← ダブルクリックで解除
└── config\
    ├── config.yaml
    └── credentials.json
```

> Windows のスタートアップフォルダ（`shell:startup`）にショートカットが作成されます。

### 解除

`unregister_startup.bat` をダブルクリックすると自動起動を解除できます。

## 操作方法

### GUI の状態表示

| 状態 | 色 | 意味 |
|---|---|---|
| カード待機中... | 緑 | カードタッチを待っています |
| カード検出 → 入力待ち | 黄 | キー1/2/3 を押してください |
| 疑義照会 → 患者番号入力 | 黄 | 患者番号を入力してください |
| 記録完了！カードを取り外してください | 水色 | カードをリーダーから離してください |
| タイムアウト → 変更ありで記録 | オレンジ | 5秒経過、デフォルト値で記録 |

### キー入力

| キー | 動作 | スプレッドシートの記録 |
|---|---|---|
| **1** | 変更あり | 変更の有無 = "変更あり" |
| **2** | 変更なし | 変更の有無 = "変更なし" |
| **3** | 疑義照会 | 変更の有無 = "疑義照会"、備考 = "患者番号: XXXXX" |
| タイムアウト | 5秒無操作 | 変更の有無 = "変更あり"（デフォルト） |

> **キーの追加**: `config.yaml` の `key_mappings` にキーを追加するだけで、新しい選択肢を増やせます（疑義照会のような特殊動作を除く）。

### スプレッドシートの記録例

| 日時 | 問い合わせ内容 | 変更の有無 | 備考 |
|---|---|---|---|
| 2026-03-12 14:30:00 | 処方箋内容について確認 | 変更あり | |
| 2026-03-12 14:31:00 | 処方箋内容について確認 | 変更なし | |
| 2026-03-12 14:32:00 | 処方箋内容について確認 | 疑義照会 | 患者番号: 12345 |

## 設定のカスタマイズ

### キーの追加（config.yaml のみ）

```yaml
input:
  key_mappings:
    "1": "変更あり"
    "2": "変更なし"
    "3": "疑義照会"
    "4": "その他"        # ← 追加するだけで動作します
```

### タイムアウト時間の変更

```yaml
input:
  timeout_seconds: 10       # 5秒 → 10秒に変更
  default_on_timeout: "変更なし"  # デフォルト値を変更
```

## プロジェクト構成

```
NFCrecord/
├── src/
│   ├── main.py              # GUI エントリーポイント（FreeSimpleGUI）
│   ├── config.py            # 設定管理（YAML読み込み）
│   ├── nfc_reader.py        # NFC リーダー制御（状態ベース検出）
│   ├── sheets_api.py        # Google Sheets API 連携
│   ├── input_handler.py     # キーボード / Stream Deck 入力
│   └── event_processor.py   # 状態マシンによるイベント制御
├── setup/
│   ├── setup_credentials.py # セットアップウィザード
│   └── README_SETUP.md      # セットアップガイド
├── config/
│   ├── config.yaml          # 設定ファイル
│   └── credentials.json     # Google 認証情報（※Git管理外）
├── .github/
│   └── workflows/
│       └── build-windows-exe.yml  # GitHub Actions ビルド
├── requirements.txt         # Python 依存パッケージ
└── README.md                # このファイル
```

## アーキテクチャ

### 状態マシン

```
IDLE（カード待機）
  ↓ カードタッチ（1回だけ検出）
WAITING_INPUT（入力待ち）
  ├─ キー1/2 or タイムアウト → 記録 → WAIT_REMOVAL
  └─ キー3（疑義照会）→ WAITING_PATIENT_NUM → 患者番号入力 → 記録 → WAIT_REMOVAL
WAIT_REMOVAL（カード取り外し待ち）
  ↓ カード取り外し
IDLE（次のカード待機）
```

### マルチスレッド構成

```
┌────────────────────────────────┐
│   メインスレッド（GUI）         │
│   FreeSimpleGUI ウィンドウ     │
└───────────┬────────────────────┘
            │ コールバック
   ┌────────┼──────────┐
   ▼        ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│NFC     │ │入力    │ │Sheets  │
│リーダー │ │ハンドラ │ │API     │
│スレッド │ │スレッド │ │スレッド │
└───┬────┘ └───┬────┘ └────────┘
    │          │
    └────┬─────┘
         ▼
   ┌──────────────┐
   │EventProcessor│
   │（状態マシン） │
   └──────────────┘
```

## トラブルシューティング

### NFC リーダーが認識されない

- USB 接続を確認
- RC-380 ドライバが正しくインストールされているか確認
- デバイスマネージャーで「PaSoRi」が表示されるか確認
- 別の USB ポートを試す

### Google Sheets に書き込めない

- `credentials.json` が `config/` フォルダに存在するか確認
- スプレッドシート ID が正しいか確認
- サービスアカウントの email でスプレッドシートが共有されているか確認
- Google Sheets API が有効か確認

### キーボード入力が反応しない

- Windows で管理者権限が必要な場合があります
- EXE を右クリック → 「管理者として実行」を試す

### SmartScreen 警告が表示される

GitHub からダウンロードしたファイルは Windows SmartScreen によりブロックされる場合があります。

- **方法1**: `register_startup.bat` を実行すると、同じフォルダ内の EXE と BAT のブロックを自動解除します
- **方法2**: ファイルを右クリック → プロパティ → 「ブロックの解除」にチェック → OK

### EXE が起動しない / 設定エラー

- `config` フォルダが EXE と同じ階層にあるか確認
- ファイル名が正しいか確認（`config.yaml`、`credentials.json`）
- Windows のファイル拡張子表示を有効にして確認
- EXE と同じフォルダに生成される `debug.log` を確認

## 開発

### ビルド

GitHub Actions により、`main` ブランチへの push で自動的に Windows EXE がビルドされ、GitHub Releases に公開されます。

### 依存パッケージ

- **FreeSimpleGUI** - GUI フレームワーク（PySimpleGUI 4.x 互換の無料フォーク）
- **pyscard** - PC/SC スマートカードインターフェース
- **google-api-python-client** - Google Sheets API
- **keyboard** - キーボードホットキー
- **PyYAML** - 設定ファイル読み込み
- **PyInstaller** - Windows EXE ビルド

## セキュリティ

- `credentials.json` は Git 管理外です（`.gitignore` に記載）
- サービスアカウントの権限は指定したスプレッドシートのみに限定されます
- NFC カードの UID は FeliCa の仕様上、読み取りごとにランダムな値が返されるため、個人の追跡には使用できません

## ライセンス

MIT License
