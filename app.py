import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from urllib import error, request

from flask import Flask, flash, jsonify, redirect, render_template, request as flask_request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=env_flag("SESSION_COOKIE_SECURE", default=False),
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

FIREBASE_BASE_URL = os.getenv(
    "FIREBASE_BASE_URL",
    "https://chat-app-136b8-default-rtdb.firebaseio.com",
).rstrip("/")
FIREBASE_ROOT = os.getenv("FIREBASE_ROOT", "my_pwa_chat")


class FirebaseClient:
    def __init__(self, base_url: str, root: str):
        self.base_url = base_url
        self.root = root.strip("/")

    def _url(self, path: str) -> str:
        clean_path = path.strip("/")
        return f"{self.base_url}/{self.root}/{clean_path}.json"

    def _request(self, method: str, path: str, payload=None):
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(self._url(path), data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=10) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Firebase HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Firebase connection failed: {exc.reason}") from exc

    def get(self, path: str):
        return self._request("GET", path)

    def put(self, path: str, payload):
        return self._request("PUT", path, payload)

    def patch(self, path: str, payload):
        return self._request("PATCH", path, payload)


firebase = FirebaseClient(FIREBASE_BASE_URL, FIREBASE_ROOT)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def current_user() -> str | None:
    return session.get("username")


def load_users() -> dict:
    return firebase.get("users") or {}


def load_messages() -> list[dict]:
    messages = firebase.get("messages") or {}
    result = []
    for message_id, item in messages.items():
        entry = dict(item)
        entry["id"] = message_id
        entry.setdefault("likes", 0)
        entry.setdefault("liked_by", {})
        result.append(entry)
    result.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return result


def get_message(message_id: str) -> dict | None:
    message = firebase.get(f"messages/{message_id}")
    if message:
        message["id"] = message_id
    return message


def create_user(username: str, password: str):
    users = load_users()
    if username in users:
        raise ValueError("帳號已存在")

    firebase.put(
        f"users/{username}",
        {
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def authenticate_user(username: str, password: str) -> bool:
    users = load_users()
    user = users.get(username)
    if not user:
        return False
    return user.get("password_hash") == hash_password(password)


def update_password(username: str, new_password: str):
    firebase.patch(
        f"users/{username}",
        {
            "password_hash": hash_password(new_password),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def create_message(author: str, article: str):
    message_id = uuid.uuid4().hex
    firebase.put(
        f"messages/{message_id}",
        {
            "author": author,
            "article": article,
            "likes": 0,
            "liked_by": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def like_message(username: str, message_id: str):
    message = get_message(message_id)
    if not message:
        raise ValueError("找不到該篇留言")

    liked_by = message.get("liked_by", {})
    if liked_by.get(username):
        raise ValueError("你已經按過讚了")

    firebase.patch(
        f"messages/{message_id}",
        {
            "likes": int(message.get("likes", 0)) + 1,
            "liked_by": {**liked_by, username: True},
        },
    )


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "firebase_base_url": FIREBASE_BASE_URL,
        "firebase_root": FIREBASE_ROOT,
    }


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/", methods=["GET", "POST"])
def login():
    if flask_request.method == "POST":
        username = flask_request.form.get("username", "").strip()
        password = flask_request.form.get("password", "").strip()

        if not username or not password:
            flash("請輸入帳號與密碼", "error")
        else:
            try:
                if authenticate_user(username, password):
                    session.clear()
                    session["username"] = username
                    session.permanent = True
                    flash("登入成功", "success")
                    return redirect(url_for("board"))
                flash("帳號或密碼錯誤", "error")
            except RuntimeError as exc:
                flash(str(exc), "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if flask_request.method == "POST":
        username = flask_request.form.get("username", "").strip()
        password = flask_request.form.get("password", "").strip()
        confirm_password = flask_request.form.get("confirm_password", "").strip()

        if not username or not password:
            flash("帳號與密碼不可空白", "error")
        elif password != confirm_password:
            flash("兩次密碼輸入不一致", "error")
        else:
            try:
                create_user(username, password)
                flash("註冊成功，請重新登入", "success")
                return redirect(url_for("login"))
            except ValueError as exc:
                flash(str(exc), "error")
            except RuntimeError as exc:
                flash(str(exc), "error")

    return render_template("register.html")


@app.route("/board", methods=["GET", "POST"])
def board():
    if not current_user():
        flash("請先登入", "error")
        return redirect(url_for("login"))

    if flask_request.method == "POST":
        article = flask_request.form.get("article", "").strip()
        if not article:
            flash("留言內容不可空白", "error")
        else:
            try:
                create_message(current_user(), article)
                flash("留言成功", "success")
                return redirect(url_for("board"))
            except RuntimeError as exc:
                flash(str(exc), "error")

    try:
        messages = load_messages()
    except RuntimeError as exc:
        flash(str(exc), "error")
        messages = []
    return render_template("board.html", messages=messages)


@app.route("/like/<message_id>", methods=["POST"])
def like(message_id: str):
    if not current_user():
        flash("請先登入", "error")
        return redirect(url_for("login"))

    try:
        like_message(current_user(), message_id)
        flash("按讚成功", "success")
    except (ValueError, RuntimeError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("board"))


@app.get("/api/messages")
def api_messages():
    if not current_user():
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    try:
        messages = load_messages()
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503

    return jsonify({"ok": True, "messages": messages})


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not current_user():
        flash("請先登入", "error")
        return redirect(url_for("login"))

    if flask_request.method == "POST":
        old_password = flask_request.form.get("old_password", "").strip()
        new_password = flask_request.form.get("new_password", "").strip()
        confirm_password = flask_request.form.get("confirm_password", "").strip()

        try:
            if not authenticate_user(current_user(), old_password):
                flash("舊密碼錯誤", "error")
            elif not new_password:
                flash("新密碼不可空白", "error")
            elif new_password != confirm_password:
                flash("新密碼與確認密碼不一致", "error")
            else:
                update_password(current_user(), new_password)
                flash("密碼已更新", "success")
                return redirect(url_for("settings"))
        except RuntimeError as exc:
            flash(str(exc), "error")

    return render_template("settings.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("已登出", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
