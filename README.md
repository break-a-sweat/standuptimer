# StandUp Timer

StandUp Timer 是一個 Windows 桌面小工具。它會在系統匣倒數時間，時間到時跳出提醒；暫停時會在螢幕左下角顯示一個小提示，按一下就能繼續。

## 最快使用方式

需求：Windows，並且已安裝 Python 3.10 或更新版本。若還沒有 Python，先到 <https://www.python.org/downloads/windows/> 安裝；安裝時建議勾選 `Add python.exe to PATH`。

打開 Windows 的 PowerShell，貼上下面整段指令後按 Enter：

```powershell
$ErrorActionPreference = "Stop"; $app = "$env:USERPROFILE\standuptimer"; $zip = "$env:TEMP\standuptimer.zip"; $tmp = "$env:TEMP\standuptimer-main"; Remove-Item $zip -Force -ErrorAction SilentlyContinue; Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue; Invoke-WebRequest "https://github.com/break-a-sweat/standuptimer/archive/refs/heads/main.zip" -OutFile $zip; Expand-Archive $zip -DestinationPath $env:TEMP -Force; if (Test-Path $app) { Remove-Item $app -Recurse -Force }; Move-Item $tmp $app; py -3 -m pip install --user -r "$app\requirements.txt"; Start-Process -FilePath "pyw" -ArgumentList @("-3", "$app\start.pyw")
```

這段指令會自動下載此專案、安裝需要的套件，然後啟動 StandUp Timer。之後要再打開，可以雙擊：

```text
%USERPROFILE%\standuptimer\start.pyw
```

如果程式已經在執行，請先從系統匣右鍵退出，再重新執行上面的指令。

## 怎麼使用

- 看 Windows 右下角系統匣的 StandUp Timer 圖示。
- 左鍵點圖示可以開始、暫停或繼續倒數。
- 右鍵點圖示可以調整時間、設定是否開機自動啟動、或退出程式。
- 如果 Windows 11 把圖示收進隱藏區，請把它拖到看得到的位置。

## 功能

- 系統匣圖示直接顯示剩餘時間，例如 `23:55`。
- 倒數完成後，會在桌面左下角顯示提醒。
- 暫停時，左下角會顯示小提示，按一下就能繼續。
- 可設定倒數時間。
- 可設定「開機自動啟動」。

## 給開發者

安裝開發環境：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

啟動：

```powershell
python standup_timer.py
```

測試：

```powershell
pytest -v
```

## 設定與記錄

設定檔位置：

```text
%APPDATA%\standuptimer\config.json
```

錯誤記錄位置：

```text
%APPDATA%\standuptimer\standuptimer.log
```
