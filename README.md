# StandUp Timer

StandUp Timer 是一個 Windows 桌面小工具。它會在系統匣倒數時間，時間到時跳出提醒；暫停時會在螢幕左下角顯示一個小提示，按一下就能繼續。

## 下載使用

需求：Windows。不需要另外安裝 Python。

1. 到 [Releases](https://github.com/break-a-sweat/standuptimer/releases) 下載最新版的 `StandUpTimer.exe`。
2. 雙擊 `StandUpTimer.exe` 啟動。
3. 之後要再打開，雙擊同一個 `StandUpTimer.exe` 即可。

如果程式已經在執行，請先從系統匣右鍵退出，再重新啟動。

`StandUpTimer.exe` 已內建 LXGW WenKai TC Regular 中文字體，別人的電腦不用另外安裝字體也能看到一致的中文提醒外觀。字體依 SIL Open Font License 1.1 發布，授權檔在 `assets/fonts/OFL.txt`。

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
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

啟動：

```powershell
python standup_timer.py
```

測試：

```powershell
pytest -q
```

本機打包 Windows 執行檔：

```powershell
pyinstaller --clean --noconfirm StandUpTimer.spec
```

完成後執行檔會在：

```text
dist\StandUpTimer.exe
```

建立 GitHub Release，例如 `v0.1.0`：

```powershell
git tag v0.1.0
git push origin main v0.1.0
gh release create v0.1.0 dist\StandUpTimer.exe --title "v0.1.0" --notes "Windows executable release."
```

如果沒有 GitHub CLI，也可以在 GitHub 的 Releases 頁面手動建立版本，並上傳 `dist\StandUpTimer.exe`。

## 設定與記錄

設定檔位置：

```text
%APPDATA%\standuptimer\config.json
```

錯誤記錄位置：

```text
%APPDATA%\standuptimer\standuptimer.log
```
