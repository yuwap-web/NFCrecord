@echo off
chcp 65001 >nul
echo ========================================
echo   NFC Sheets Logger - スタートアップ解除
echo ========================================
echo.

set "SHORTCUT_NAME=NFCrecord.lnk"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: ショートカットの存在確認
if not exist "%STARTUP_DIR%\%SHORTCUT_NAME%" (
    echo [情報] スタートアップに登録されていません。
    echo.
    pause
    exit /b 0
)

:: ショートカットを削除
del "%STARTUP_DIR%\%SHORTCUT_NAME%"

if %ERRORLEVEL% neq 0 (
    echo [エラー] ショートカットの削除に失敗しました。
    echo.
    pause
    exit /b 1
)

echo.
echo [成功] スタートアップから解除しました！
echo.
echo 次回の Windows ログイン時から自動起動しなくなります。
echo.
pause
