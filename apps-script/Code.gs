/**
 * NFC Sheets Logger - Apps Script Backend
 *
 * スプレッドシートに紐づけてデプロイする。
 * Android Chrome の Web NFC API と連携し、
 * NFC タッチ → ボタン選択 → スプレッドシート記録 を実現する。
 */

/**
 * Web アプリのエントリーポイント
 * index.html を返す
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('NFC Sheets Logger')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * スプレッドシートに1行追加する
 * フロントエンド（index.html）から google.script.run 経由で呼ばれる
 *
 * @param {string} changeStatus - 変更の有無（"変更あり", "変更なし", "疑義照会"）
 * @param {string} notes - 備考（患者番号など）
 * @return {Object} 結果オブジェクト { success, timestamp }
 */
function appendRecord(changeStatus, notes) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetName = 'NFC Logs';
  var sheet = ss.getSheetByName(sheetName);

  // シートが無ければ作成してヘッダーを追加
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    sheet.appendRow(['日時', '問い合わせ内容', '変更の有無', '備考']);
  }

  var now = Utilities.formatDate(
    new Date(),
    Session.getScriptTimeZone(),
    'yyyy-MM-dd HH:mm:ss'
  );

  sheet.appendRow([
    now,
    '処方箋内容について確認',
    changeStatus,
    notes || ''
  ]);

  return { success: true, timestamp: now };
}
