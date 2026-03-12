# NFC Sheets Logger - Android 版（Apps Script + GitHub Pages）

PC 版と同じスプレッドシートに記録する、Android スマホ向け Web アプリです。

## 構成

```
GitHub Pages (docs/index.html)     ← フロントエンド（NFC読取 + UI）
        ↓ fetch (GET)
Apps Script (Code.gs)              ← API（スプレッドシート書き込み）
        ↓
スプレッドシート (NFC Logs)         ← PC版と共有
```

> Apps Script の iframe 制限により、Web NFC API は GitHub Pages から直接実行します。

## セットアップ手順

### 1. Apps Script を設定（API エンドポイント）

対象のスプレッドシートを開き：

```
メニュー → 拡張機能 → Apps Script
```

#### Code.gs を貼り付け

1. 左側の `コード.gs`（または `Code.gs`）をクリック
2. 中身をすべて削除
3. `apps-script/Code.gs` の内容をコピー＆ペースト
4. 保存（Ctrl+S）

> index.html は Apps Script 側には **不要** です（GitHub Pages を使用するため）。

#### 権限の承認

1. 上部のドロップダウンで `appendRecord` を選択
2. **▶ 実行** をクリック
3. 「権限を確認」→ アカウント選択 → 「詳細」→「○○に移動」→「許可」

#### デプロイ

1. **「デプロイ」→「新しいデプロイ」**
2. 歯車アイコン → **「ウェブアプリ」**
3. 設定：
   - 次のユーザーとして実行: **自分**
   - アクセスできるユーザー: **全員**
4. 「デプロイ」→ **URL をコピー**

> ⚠️ 「全員」に設定する必要があります（GitHub Pages からのアクセスのため）。
> URL を知っている人のみアクセス可能で、できることは行の追加のみです。

### 2. GitHub Pages を有効化

GitHub リポジトリの設定：

```
Settings → Pages → Source: Deploy from a branch
Branch: main, Folder: /docs → Save
```

数分後に以下の URL でアクセス可能になります：

```
https://yuwap-web.github.io/NFCrecord/
```

### 3. Android でホーム画面に追加

1. Android の **Chrome** で上記 URL を開く
2. **初回**: Apps Script の URL を入力して「保存して開始」
3. Chrome メニュー（︙）→ **「ホーム画面に追加」**

## 使い方

```
1. ホーム画面のアイコンをタップ
2. 「NFC スキャン開始」ボタンをタップ（初回のみ）
3. → 以降は常時 NFC 待機状態 ←
4. 受話器の NFC タグにスマホをかざす
5. ボタンで入力を選択：
   - 変更あり
   - 変更なし
   - 疑義照会（→ 患者番号入力）
6. 5秒無操作 →「変更あり」で自動記録
7. 記録完了 → 自動的に NFC 待機に戻る
```

> 「NFC スキャン開始」は **アプリ起動時に1回タップするだけ** です。
> 以降はずっと待機状態で、タグにかざすたびに自動検出します。

## 動作要件

| 項目 | 要件 |
|------|------|
| スマホ | Android（NFC 搭載） |
| ブラウザ | Chrome 89 以上 |
| NFC タグ | NDEF 対応の汎用 NFC タグ（NTAG213 等） |

> iOS の Safari は Web NFC 非対応です。Android Chrome のみです。

## PC 版との共存

- 同じスプレッドシート、同じシート（NFC Logs）に記録
- PC 版と Android 版の同時使用 OK
- 互いに干渉しない（どちらも末尾に行を追加するだけ）

## Apps Script コード更新時

1. Apps Script エディタで保存
2. 「デプロイ」→「デプロイを管理」
3. 鉛筆アイコン → バージョンを「新バージョン」に変更
4. 「デプロイ」をクリック

## フロントエンド（HTML）更新時

`docs/index.html` を編集して `main` ブランチに push するだけ。
GitHub Pages が自動的に更新されます。
