@echo off
chcp 65001 >nul
echo ========================================
echo   NFC Sheets Logger - スタートアップ登録
echo ========================================
echo.

:: 現在のバッチファイルのディレクトリを取得
set "APP_DIR=%~dp0"
set "EXE_PATH=%APP_DIR%NFCrecord.exe"
set "SHORTCUT_NAME=NFCrecord.lnk"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: EXE の存在確認
if not exist "%EXE_PATH%" (
    echo [エラー] NFCrecord.exe が見つかりません。
    echo このバッチファイルを NFCrecord.exe と同じフォルダに配置してください。
    echo.
    pause
    exit /b 1
)

:: ダウンロードしたファイルの MOTW（Mark of the Web）を解除
:: これにより SmartScreen 警告を回避できる
echo ダウンロードブロックを解除しています...
powershell -Command "Get-ChildItem '%APP_DIR%' -Include '*.exe','*.bat' -Recurse | Unblock-File -ErrorAction SilentlyContinue"
echo.

:: 既存のショートカットを確認
if exist "%STARTUP_DIR%\%SHORTCUT_NAME%" (
    echo [情報] スタートアップに既に登録されています。
    echo 再登録する場合は、先に unregister_startup.bat で解除してください。
    echo.
    pause
    exit /b 0
)

:: PowerShell でショートカットを作成（管理者として実行フラグ付き）
echo スタートアップフォルダにショートカットを作成しています...
echo （keyboard ライブラリに管理者権限が必要なため、管理者として実行します）
powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $sc = $ws.CreateShortcut('%STARTUP_DIR%\%SHORTCUT_NAME%'); ^
     $sc.TargetPath = '%EXE_PATH%'; ^
     $sc.WorkingDirectory = '%APP_DIR%'; ^
     $sc.Description = 'NFC Sheets Logger'; ^
     $sc.Save(); ^
     $bytes = [System.IO.File]::ReadAllBytes('%STARTUP_DIR%\%SHORTCUT_NAME%'); ^
     $bytes[0x15] = $bytes[0x15] -bor 0x20; ^
     [System.IO.File]::WriteAllBytes('%STARTUP_DIR%\%SHORTCUT_NAME%', $bytes)"

if %ERRORLEVEL% neq 0 (
    echo [エラー] ショートカットの作成に失敗しました。
    echo.
    pause
    exit /b 1
)

echo.
echo [成功] スタートアップに登録しました！
echo.
echo   ショートカット: %STARTUP_DIR%\%SHORTCUT_NAME%
echo   対象 EXE:       %EXE_PATH%
echo.
echo 次回の Windows ログイン時から自動的に起動します。
echo.
pause
