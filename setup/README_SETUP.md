# NFC Sheets Logger - Setup Guide

このガイドでは、NFC Sheets Logger を Windows PC にセットアップする手順を説明します。

## 前提条件

- Windows 10 以上
- インターネット接続
- **Google アカウント**（個人アカウントで OK、Workspace 不要）
- SONY RC-380 NFC リーダー

## ステップ 1: Google Cloud プロジェクトの作成

> **重要**：以下のサービスはすべて無料です。Workspace 契約は不要です。
> - 個人の Google アカウント（gmail.com など）でご利用ください
> - 無料枠：毎月 100 万セルの読み書きが可能

### 1.1 Google Cloud Console にアクセス

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 個人の Google アカウント（gmail.com など）でサインイン

### 1.2 新しいプロジェクトを作成

1. ページ上部のプロジェクトセレクターをクリック
2. 「新しいプロジェクト」をクリック
3. プロジェクト名を入力（例：`NFCrecord`）
4. 「作成」をクリック

### 1.3 Sheets API を有効化

1. 左側のメニューから「API とサービス」 → 「ライブラリ」を選択
2. 検索ボックスで「Google Sheets API」を検索
3. 結果をクリック
4. 「有効にする」をクリック

## ステップ 2: サービスアカウントの作成

### 2.1 サービスアカウント認証情報を作成

1. 左側のメニュー「API とサービス」 → 「認証情報」をクリック
2. 「+ 認証情報を作成」をクリック
3. 「サービスアカウント」を選択

### 2.2 サービスアカウントの詳細を入力

1. サービスアカウント名を入力（例：`nfc-logger`）
2. サービスアカウント ID はそのままでも OK
3. 「作成して続行」をクリック

### 2.3 キーを作成

1. 「キーを作成」をクリック
2. 「JSON」を選択
3. 「作成」をクリック
4. JSON ファイルが自動ダウンロードされます
   - このファイル名は通常 `service_account_name-xxxxx.json` 形式です
   - **このファイルは安全に保管してください**

### 2.4 ダウンロードしたファイルを確認

1. ダウンロードフォルダで JSON ファイルを確認
2. メモ帳で開いて、以下の情報を確認：
   - `"client_email": "..."` ← この値が必要です

## ステップ 3: Google Sheets の準備

### 3.1 新しいスプレッドシートを作成

1. [Google Sheets](https://docs.google.com/spreadsheets) にアクセス
2. 「空白のスプレッドシート」をクリック
3. 名前を入力（例：`処方箋確認ログ`）
4. URL から スプレッドシート ID をコピー
   - URL 形式：`https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/...`
   - `{SPREADSHEET_ID}` の部分をコピーしておきます

### 3.2 スプレッドシートを共有

1. 右上の「共有」ボタンをクリック
2. Step 2.4 で確認した `client_email` を入力
3. 「エディタ」権限を選択
4. 「共有」をクリック

## ステップ 4: アプリケーションのセットアップ

### 4.1 Windows に Python をインストール

1. [python.org](https://www.python.org/) にアクセス
2. Python 3.11 以上をダウンロード
3. インストーラを実行
   - **重要**：「Add Python to PATH」にチェックを入れる

### 4.2 NFCrecord アプリケーションをダウンロード

1. [GitHub Releases](https://github.com/yourusername/NFCrecord/releases) にアクセス
2. 最新バージョンの `NFCrecord.exe` をダウンロード
3. ドキュメントフォルダなど、わかりやすい場所に保存

### 4.3 セットアップスクリプトを実行

1. コマンドプロンプトを開く（Windows キー + `cmd` キーを同時押し）
2. NFCrecord フォルダに移動
   ```
   cd 保存したフォルダへのパス
   ```
3. Python がインストールされているか確認
   ```
   python --version
   ```

4. 必要なライブラリをインストール
   ```
   pip install -r requirements.txt
   ```

5. セットアップスクリプトを実行
   ```
   python setup/setup_credentials.py
   ```

6. スクリプトに従って情報を入力：
   - JSON 認証情報ファイルのパス
   - スプレッドシート ID

## ステップ 5: SONY RC-380 ドライバのインストール

### 5.1 ドライバのダウンロード

1. SONY 公式サイトから RC-380 ドライバをダウンロード
2. インストーラを実行
3. 画面の指示に従ってインストール

### 5.2 接続テスト

1. RC-380 を USB で Windows PC に接続
2. Windows がデバイスを認識するまで待機
3. デバイスマネージャーで「PaSoRi」が表示されることを確認

## ステップ 6: アプリケーションの起動

### 方法 1: Windows EXE から起動（推奨）

```
NFCrecord.exe をダブルクリック
```

### 方法 2: コマンドラインから起動

```
python src/main.py
```

## 動作確認

1. アプリケーションウィンドウが開く
2. 「Status」セクションで接続状態が表示される
   - NFC リーダー：✓ Ready
   - キーボード：✓ Ready
   - Stream Deck（オプション）：✓ Ready または ✗ Not available

3. NFC カードをリーダーに近づける
4. 5 秒以内に「1」キーを押す（または Stream Deck ボタン 1）
5. Google Sheets にログが記録される

## トラブルシューティング

### Q: NFC リーダーが認識されない

**A:**
- USB 接続を確認
- RC-380 ドライバが正しくインストールされているか確認
- Windows デバイスマネージャーで「PaSoRi」を確認
- 別の USB ポートを試す

### Q: Google Sheets に書き込めない

**A:**
- Google Sheets ID が正しいか確認
- サービスアカウント email でスプレッドシートが共有されているか確認
- credentials.json ファイルが `config/` フォルダに存在するか確認

### Q: キーボード入力が反応しない

**A:**
- Windows がキーボード入力のために管理者権限を必要とする場合がある
- コマンドプロンプトを「管理者として実行」で開きなおす

### Q: Stream Deck が認識されない

**A:**
- Stream Deck ソフトウェアをインストール
- USB 接続を確認
- アプリは Stream Deck なしでもキーボード入力で動作します

## サポート

質問や問題がある場合：
1. [GitHub Issues](https://github.com/yourusername/NFCrecord/issues) で報告
2. エラーメッセージをスクリーンショットで添付

## セキュリティに関する注意

- `credentials.json` は絶対に他人と共有しないでください
- GitHub などに `credentials.json` をコミットしないでください
- Windows ファイアウォールで必要に応じてアプリケーションを許可してください
