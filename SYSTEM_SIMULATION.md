# 點讚聊天室系統模擬

## 1. 專案定位

本專案依照 `W10_點讚-聊天室-firebase-20260430.pdf` 的核心概念，改寫為：

- 後端：Python Flask
- 前端：HTML + CSS + PWA
- 雲端資料：Firebase Realtime Database
- 使用情境：手機瀏覽器加入主畫面後，以 PWA 方式操作

## 2. 對照 PDF 功能

### Screen1：登入

- 使用者輸入帳號與密碼
- 驗證成功後導向留言板

### Screen2：留言板

- 顯示所有留言
- 可新增留言
- 可替任一留言按讚

### Screen3：註冊

- 建立新帳號
- 建立成功後回登入頁

### Screen4：個人設定

- 驗證舊密碼
- 修改新密碼

## 3. Firebase 資料模擬

本版使用較適合網頁開發的結構，概念上對應 PDF 的 `account / password / article / author / like / vote`：

```json
{
  "my_pwa_chat": {
    "users": {
      "amy": {
        "password_hash": "sha256..."
      }
    },
    "messages": {
      "msg_001": {
        "author": "amy",
        "article": "大家好",
        "likes": 1,
        "liked_by": {
          "bob": true
        }
      }
    }
  }
}
```

## 4. 操作流程模擬

### 情境 A：新使用者加入

1. 開啟首頁 `/`
2. 點選「前往註冊」
3. 輸入帳號、密碼、確認密碼
4. 系統寫入 Firebase `users`
5. 畫面跳回登入頁

### 情境 B：登入並留言

1. 使用者在首頁登入
2. 系統驗證 `users/{username}/password_hash`
3. 成功後進入 `/board`
4. 輸入留言並送出
5. 系統寫入 Firebase `messages/{message_id}`

### 情境 C：替文章按讚

1. 在留言板瀏覽一篇文章
2. 點選「按讚」
3. 畫面跳出確認視窗
4. 確認後系統更新：
   - `likes + 1`
   - `liked_by/{username} = true`
5. 若同一人重複按讚，系統阻擋

### 情境 D：修改密碼

1. 進入 `/settings`
2. 輸入舊密碼與新密碼
3. 舊密碼正確才允許更新
4. 系統覆寫 Firebase `users/{username}/password_hash`

## 5. PWA 模擬

- `manifest.json`：提供安裝到主畫面的基本資訊
- `sw.js`：快取首頁與靜態檔案
- 手機上可透過瀏覽器「加入主畫面」近似 App 操作

## 6. 可行性評估

此架構可行，且很適合用 VS Code 開發教學型作品。

優點：

- Python 後端好維護，適合課堂展示
- HTML 畫面比 App Inventor 更容易自訂版面
- PWA 可以直接在手機上以接近 App 的方式使用
- Firebase Realtime Database 很適合留言板這類即時資料

限制：

- 目前版本使用 Flask 輪詢/重新整理方式呈現資料，不是 WebSocket 即時推送
- 若 Firebase 規則完全開放，正式上線會有安全風險
- 若要正式產品化，建議改用 Firebase Authentication 管理登入

## 7. 建議後續擴充

- 加入留言時間格式化
- 加入刪除留言功能
- 改為 AJAX 自動更新留言板
- 改用 Firebase Authentication
- 補上 App icon 與離線頁面
