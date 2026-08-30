import hashlib
import hmac
import io
import os
import secrets
import sqlite3
import time
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, request, send_from_directory, url_for
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.middleware.proxy_fix import ProxyFix


BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
THUMB_DIR = DATA_DIR / "uploads" / "thumb"
DETAIL_DIR = DATA_DIR / "uploads" / "detail"
DB_PATH = DATA_DIR / "ldg.sqlite3"
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_BYTES = 12 * 1024 * 1024
FEEDBACK_LINK_LIFETIME = timedelta(days=7)
AUTH_FAILURE_LIMIT = 5
AUTH_LOCK_SECONDS = 60
STATIC_GALLERY = (
    {
        "id": "kitchen-electrical-accessories",
        "caption": "Kitchen electrical installation",
        "alt_text": "Neatly installed kitchen sockets and switches above a tiled worktop",
    },
    {
        "id": "hob-and-oven-installation",
        "caption": "Hob and oven installation",
        "alt_text": "Installed electric hob and built-in oven in a finished kitchen",
    },
    {
        "id": "electric-fire-installation",
        "caption": "Electric fire installation",
        "alt_text": "Electric fire installation in progress at a domestic property",
    },
)

Image.MAX_IMAGE_PIXELS = 40_000_000

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def init_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    with db_connect() as database:
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS photos (
                id TEXT PRIMARY KEY,
                thumbnail_filename TEXT NOT NULL,
                detail_filename TEXT NOT NULL,
                caption TEXT NOT NULL DEFAULT '',
                alt_text TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feedback_links (
                token_hash TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                used_at TEXT
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_attempts (
                client_hash TEXT PRIMARY KEY,
                failures INTEGER NOT NULL,
                locked_until INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL
            );
            """
        )


def admin_credentials_configured():
    return bool(os.environ.get("ADMIN_USERNAME") and os.environ.get("ADMIN_PASSWORD"))


def client_auth_hash():
    address = request.remote_addr or "unknown"
    key = os.environ.get("ADMIN_PASSWORD", "ldg-unconfigured").encode()
    return hmac.new(key, address.encode(), hashlib.sha256).hexdigest()


def auth_lock_remaining(client_hash):
    now = int(time.time())
    with db_connect() as database:
        row = database.execute(
            "SELECT locked_until FROM auth_attempts WHERE client_hash = ?", (client_hash,)
        ).fetchone()
    return max(0, row["locked_until"] - now) if row else 0


def record_auth_failure(client_hash):
    now = int(time.time())
    with db_connect() as database:
        database.execute("BEGIN IMMEDIATE")
        row = database.execute(
            "SELECT failures, locked_until FROM auth_attempts WHERE client_hash = ?", (client_hash,)
        ).fetchone()
        failures = 0 if row and row["locked_until"] <= now and row["failures"] >= AUTH_FAILURE_LIMIT else (row["failures"] if row else 0)
        failures += 1
        locked_until = now + AUTH_LOCK_SECONDS if failures >= AUTH_FAILURE_LIMIT else 0
        database.execute(
            "INSERT INTO auth_attempts (client_hash, failures, locked_until, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(client_hash) DO UPDATE SET failures=excluded.failures, "
            "locked_until=excluded.locked_until, updated_at=excluded.updated_at",
            (client_hash, failures, locked_until, now),
        )
    return max(0, locked_until - now)


def clear_auth_failures(client_hash):
    with db_connect() as database:
        database.execute("DELETE FROM auth_attempts WHERE client_hash = ?", (client_hash,))


def valid_admin_credentials():
    auth = request.authorization
    expected_user = os.environ.get("ADMIN_USERNAME", "")
    expected_password = os.environ.get("ADMIN_PASSWORD", "")
    return bool(
        auth
        and admin_credentials_configured()
        and hmac.compare_digest(auth.username or "", expected_user)
        and hmac.compare_digest(auth.password or "", expected_password)
    )


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not admin_credentials_configured():
            return Response("Admin access is not configured.", status=503, mimetype="text/plain")
        client_hash = client_auth_hash()
        remaining = auth_lock_remaining(client_hash)
        if remaining:
            return Response(
                "Too many failed sign-in attempts. Try again in one minute.",
                status=429,
                headers={"Retry-After": str(remaining)},
                mimetype="text/plain",
            )
        if not valid_admin_credentials():
            remaining = record_auth_failure(client_hash)
            if remaining:
                return Response(
                    "Too many failed sign-in attempts. Try again in one minute.",
                    status=429,
                    headers={"Retry-After": str(remaining)},
                    mimetype="text/plain",
                )
            return Response(
                "Authentication required.",
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="LDG site administration"'},
                mimetype="text/plain",
            )
        clear_auth_failures(client_hash)
        return view(*args, **kwargs)

    return wrapped


def admin_csrf_token():
    password = os.environ.get("ADMIN_PASSWORD", "")
    return hmac.new(password.encode(), b"ldg-admin-csrf-v1", hashlib.sha256).hexdigest()


def verify_admin_csrf():
    supplied = request.form.get("csrf_token", "")
    if not hmac.compare_digest(supplied, admin_csrf_token()):
        abort(400, "Invalid form token")


def feedback_token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def feedback_csrf_token(token):
    secret = os.environ.get("ADMIN_PASSWORD", "").encode()
    return hmac.new(secret, f"feedback-csrf:{token}".encode(), hashlib.sha256).hexdigest()


def clean_text(value, maximum):
    normalized = unicodedata.normalize("NFKC", value or "")
    without_controls = "".join(char for char in normalized if char in "\n\t" or unicodedata.category(char)[0] != "C")
    return " ".join(without_controls.split()).strip()[:maximum]


def public_feedback_url(token):
    relative = url_for("feedback_form", token=token)
    configured_base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    return f"{configured_base}{relative}" if configured_base else url_for("feedback_form", token=token, _external=True)


@app.after_request
def secure_response(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
        "font-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    return response


@app.get("/health")
def health():
    return Response("healthy\n", mimetype="text/plain")


@app.get("/api/gallery")
def gallery_api():
    with db_connect() as database:
        rows = database.execute(
            "SELECT id, caption, alt_text FROM photos ORDER BY created_at DESC LIMIT 24"
        ).fetchall()
    uploaded_photos = [
            {
                "id": row["id"],
                "caption": row["caption"],
                "alt_text": row["alt_text"],
                "thumbnail_url": url_for("uploaded_image", kind="thumb", photo_id=row["id"]),
                "detail_url": url_for("uploaded_image", kind="detail", photo_id=row["id"]),
            }
            for row in rows
        ]
    bundled_photos = [
        {
            **photo,
            "thumbnail_url": url_for("public_file", path=f"work/thumb/{photo['id']}.webp"),
            "detail_url": url_for("public_file", path=f"work/detail/{photo['id']}.webp"),
        }
        for photo in STATIC_GALLERY
    ]
    response = jsonify(uploaded_photos + bundled_photos)
    response.headers["Cache-Control"] = "public, max-age=60"
    return response


@app.get("/api/feedback")
def feedback_api():
    with db_connect() as database:
        rows = database.execute(
            "SELECT rating, comment FROM feedback WHERE approved = 1 ORDER BY created_at DESC LIMIT 12"
        ).fetchall()
    response = jsonify([{"rating": row["rating"], "comment": row["comment"]} for row in rows])
    response.headers["Cache-Control"] = "public, max-age=60"
    return response


@app.get("/uploads/<kind>/<photo_id>.webp")
def uploaded_image(kind, photo_id):
    if kind not in {"thumb", "detail"} or not photo_id.isalnum():
        abort(404)
    directory = THUMB_DIR if kind == "thumb" else DETAIL_DIR
    max_age = 86400 if kind == "thumb" else 2592000
    return send_from_directory(directory, f"{photo_id}.webp", max_age=max_age, conditional=True)


@app.route("/feedback/<token>", methods=["GET", "POST"])
def feedback_form(token):
    if len(token) < 32 or len(token) > 128:
        abort(404)
    token_hash = feedback_token_hash(token)
    with db_connect() as database:
        link = database.execute(
            "SELECT created_at, used_at FROM feedback_links WHERE token_hash = ?", (token_hash,)
        ).fetchone()
    if not link:
        abort(404)
    created_at = datetime.fromisoformat(link["created_at"])
    if link["used_at"] or created_at <= datetime.now(timezone.utc) - FEEDBACK_LINK_LIFETIME:
        return render_template("feedback.html", expired=True), 410

    error = None
    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", "0"))
        except ValueError:
            rating = 0
        comment = clean_text(request.form.get("comment", ""), 1000)
        supplied_csrf = request.form.get("csrf_token", "")
        if not hmac.compare_digest(supplied_csrf, feedback_csrf_token(token)):
            abort(400, "Invalid form token")
        if rating not in range(1, 6):
            error = "Please choose a rating from 1 to 5."
        elif len(comment) < 10 or len(comment) > 1000:
            error = "Feedback must be between 10 and 1,000 characters."
        else:
            with db_connect() as database:
                database.execute("BEGIN IMMEDIATE")
                current = database.execute(
                    "SELECT created_at, used_at FROM feedback_links WHERE token_hash = ?", (token_hash,)
                ).fetchone()
                expired = current and datetime.fromisoformat(current["created_at"]) <= datetime.now(timezone.utc) - FEEDBACK_LINK_LIFETIME
                if not current or current["used_at"] or expired:
                    database.rollback()
                    return render_template("feedback.html", expired=True), 410
                now = utc_now()
                database.execute(
                    "INSERT INTO feedback (rating, comment, approved, created_at) VALUES (?, ?, 0, ?)",
                    (rating, comment, now),
                )
                database.execute(
                    "UPDATE feedback_links SET used_at = ? WHERE token_hash = ?", (now, token_hash)
                )
                database.commit()
            return render_template("feedback.html", submitted=True)
    return render_template("feedback.html", error=error, csrf_token=feedback_csrf_token(token))


@app.get("/admin")
@admin_required
def admin_dashboard():
    generated_link = request.args.get("generated_link", "")
    with db_connect() as database:
        photos = database.execute(
            "SELECT id, caption, created_at FROM photos ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        feedback_entries = database.execute(
            "SELECT id, rating, comment, approved, created_at FROM feedback ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    response = render_template(
        "admin.html",
        photos=photos,
        feedback_entries=feedback_entries,
        generated_link=generated_link,
        csrf_token=admin_csrf_token(),
    )
    return Response(response, headers={"Cache-Control": "no-store"})


@app.post("/admin/photos")
@admin_required
def admin_upload_photo():
    verify_admin_csrf()
    uploaded = request.files.get("photo")
    caption = clean_text(request.form.get("caption", ""), 160)
    alt_text = clean_text(request.form.get("alt_text", ""), 180)
    if not uploaded or not uploaded.filename:
        abort(400, "Choose a photo")
    raw = uploaded.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        abort(413, "Photo is larger than 12 MB")
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in ALLOWED_FORMATS:
                abort(415, "Only JPEG, PNG and WebP images are accepted")
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError):
        abort(415, "The uploaded file is not a supported image")

    photo_id = uuid.uuid4().hex
    detail = image.copy()
    detail.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    detail.save(DETAIL_DIR / f"{photo_id}.webp", "WEBP", quality=84, method=6)
    thumb = image.copy()
    thumb.thumbnail((640, 480), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (640, 480), (23, 37, 64))
    canvas.paste(thumb, ((640 - thumb.width) // 2, (480 - thumb.height) // 2))
    canvas.save(THUMB_DIR / f"{photo_id}.webp", "WEBP", quality=76, method=6)

    with db_connect() as database:
        database.execute(
            "INSERT INTO photos (id, thumbnail_filename, detail_filename, caption, alt_text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (photo_id, f"{photo_id}.webp", f"{photo_id}.webp", caption, alt_text, utc_now()),
        )
    return Response(status=303, headers={"Location": url_for("admin_dashboard")})


@app.post("/admin/feedback-links")
@admin_required
def admin_generate_feedback_link():
    verify_admin_csrf()
    token = secrets.token_urlsafe(32)
    with db_connect() as database:
        database.execute(
            "INSERT INTO feedback_links (token_hash, created_at) VALUES (?, ?)",
            (feedback_token_hash(token), utc_now()),
        )
    location = url_for("admin_dashboard", generated_link=public_feedback_url(token))
    return Response(status=303, headers={"Location": location})


@app.post("/admin/feedback/<int:feedback_id>/approve")
@admin_required
def admin_approve_feedback(feedback_id):
    verify_admin_csrf()
    with db_connect() as database:
        database.execute("UPDATE feedback SET approved = 1 WHERE id = ?", (feedback_id,))
    return Response(status=303, headers={"Location": url_for("admin_dashboard")})


@app.get("/")
def index():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.get("/<path:path>")
def public_file(path):
    return send_from_directory(PUBLIC_DIR, path)


init_database()
