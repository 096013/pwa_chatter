# my_pwa_chat_render

這是提供 Render 部署使用的版本，原本本機專案保持不變。

## 目錄

```text
render/
├── app.py
├── requirements.txt
├── render.yaml
├── DEPLOY_RENDER.md
├── README.md
├── SYSTEM_SIMULATION.md
├── static/
│   ├── manifest.json
│   ├── style.css
│   └── sw.js
└── templates/
    ├── base.html
    ├── board.html
    ├── login.html
    ├── register.html
    └── settings.html
```

## 本機測試

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FIREBASE_BASE_URL="https://chat-app-136b8-default-rtdb.firebaseio.com/"
$env:FIREBASE_ROOT="my_pwa_chat"
$env:SECRET_KEY="change-me"
python app.py
```

## Render 特色

- 使用 `gunicorn` 啟動 Flask
- 支援 Render 的 `PORT`
- 支援 HTTPS 後的安全 session cookie
- 避免 PWA 快取舊登入頁和舊留言板頁面
