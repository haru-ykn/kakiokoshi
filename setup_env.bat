@echo off
echo Gemini APIキーを設定します
echo.
echo あなたのGemini APIキーを入力してください:
set /p GEMINI_API_KEY=
echo.
echo 環境変数を設定しました: GEMINI_API_KEY=%GEMINI_API_KEY%
echo.
echo このセッション中は環境変数が有効です。
echo 永続的に設定するには、システムの環境変数に追加してください。
echo.
pause 