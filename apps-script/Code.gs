/**
 * NFC Sheets Logger - Apps Script Backend (API モード)
 *
 * フロントエンドは GitHub Pages でホスティング。
 * この Apps Script は API エンドポイントとしてのみ機能する。
 *
 * デプロイ設定:
 *   - 次のユーザーとして実行: 自分
 *   - アクセスできるユーザー: 全員
 */

/**
 * GET リクエストハンドラ
 * ?action=record&changeStatus=...&notes=... でスプレッドシートに記録
 */
function doGet(e) {
  // action=record: スプレッドシートに記録
  if (e && e.parameter && e.parameter.action === 'record') {
    var result = appendRecord(
      e.parameter.changeStatus || '',
      e.parameter.notes || ''
    );
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // パラメータなし: 使い方を表示
  return ContentService.createTextOutput(JSON.stringify({
    status: 'ok',
    usage: 'GET ?action=record&changeStatus=変更あり&notes=備考'
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * スプレッドシートに1行追加する
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
