# Render 部署步驟

本目錄是 Render 專用版本：

- 原始本機版不變
- 這份已補 `gunicorn`
- 已加入 `render.yaml`
- 已針對 HTTPS session 與 PWA 快取做部署調整

## 1. 上傳到 GitHub

建議把整個專案推到 GitHub，並保留 `render/` 目錄。

如果你只想部署 Render 版，也可以單獨把 `render/` 內容放到新的 repo 根目錄。

## 2. 在 Render 建立服務

1. 登入 Render
2. 點 `New +`
3. 選 `Blueprint`
4. 連接你的 GitHub repository
5. Render 會讀取 `render/render.yaml`

如果沒有用 Blueprint，也可以手動建立：

- Runtime: `Python`
- Root Directory: `render`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

## 3. 設定環境變數

`render.yaml` 已預設以下值：

- `FIREBASE_BASE_URL=https://chat-app-136b8-default-rtdb.firebaseio.com`
- `FIREBASE_ROOT=my_pwa_chat`
- `SESSION_COOKIE_SECURE=true`
- `SECRET_KEY` 自動產生

如果你要換自己的 Firebase 專案，只要改這兩個：

- `FIREBASE_BASE_URL`
- `FIREBASE_ROOT`

## 4. Firebase 規則

課堂展示可先用：

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

正式環境不建議全開。

## 5. 手機 PWA 注意事項

這版已做以下處理：

- Flask 回應加上 `Cache-Control: no-store`
- Service Worker 不再快取 `/`、`/board`、`/register`、`/settings`、`/api/*`
- 手機留言板每 5 秒自動刷新一次
- HTTPS 下 session cookie 可設為 secure
- `ProxyFix` 可正確辨識 Render 轉發後的 HTTPS

## 6. 第一次上線後建議測試

1. 用電腦開 Render 網址
2. 註冊一個新帳號
3. 登入後新增留言
4. 用手機同時開啟同一網址
5. 確認手機可登入、可留言、可看到自動刷新
6. 若手機曾安裝舊版 PWA，請先刪除再重新加入主畫面

## 7. 自訂網域

如果你之後買網域：

1. Render 服務頁面進入 `Settings`
2. 找 `Custom Domains`
3. 加入你的網域，例如 `chat.example.com`
4. 到網域商 DNS 後台新增 Render 指定的 `CNAME` 或 `A` 記錄
5. 等待 TLS/HTTPS 生效

## 8. 常見問題

### 手機登入後跳回登入頁

通常是：

- 舊版 PWA 還在快取
- `SESSION_COOKIE_SECURE` 未開而導致 HTTPS 下 cookie 行為不一致
- `SECRET_KEY` 變動太頻繁

### Firebase 連不上

請檢查：

- `FIREBASE_BASE_URL` 是否正確
- Realtime Database 規則是否允許讀寫
- Firebase 專案是否仍可用
