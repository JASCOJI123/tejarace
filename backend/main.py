"""
TEJA RACE - Backend API
Fuel-efficiency gamification for drivers.

Endpoints:
  POST /api/user/register      -> create/update a driver profile
  POST /api/fuel/entry         -> log a fuel purchase + odometer reading
  GET  /api/leaderboard        -> weekly ranking for a city
  GET  /api/profile/{user_id}  -> a driver's own stats + rank
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "teja_race.db")

app = FastAPI(title="TEJA RACE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mini App is served from Telegram's webview
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,   -- Telegram user id
            name        TEXT NOT NULL,
            city        TEXT NOT NULL DEFAULT 'Buxoro',
            car_model   TEXT NOT NULL DEFAULT 'Noma''lum',
            baseline_lp100 REAL NOT NULL DEFAULT 8.0,  -- shahar/model standarti
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS fuel_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            liters      REAL NOT NULL,
            distance_km REAL NOT NULL,     -- shu quyishdan beri bosib o'tilgan masofa
            amount_sum  REAL,              -- ixtiyoriy: qancha pul sarflandi
            created_at  TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        """
    )
    conn.commit()
    conn.close()


class RegisterIn(BaseModel):
    user_id: int
    name: str
    city: str = "Buxoro"
    car_model: str = "Noma'lum"
    baseline_lp100: float = 8.0


class FuelEntryIn(BaseModel):
    user_id: int
    liters: float
    distance_km: float
    amount_sum: float | None = None


@app.on_event("startup")
def _startup():
    init_db()


@app.post("/api/user/register")
def register_user(payload: RegisterIn):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO users (user_id, name, city, car_model, baseline_lp100, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            city=excluded.city,
            car_model=excluded.car_model,
            baseline_lp100=excluded.baseline_lp100
        """,
        (
            payload.user_id,
            payload.name,
            payload.city,
            payload.car_model,
            payload.baseline_lp100,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/fuel/entry")
def add_fuel_entry(payload: FuelEntryIn):
    if payload.distance_km <= 0 or payload.liters <= 0:
        raise HTTPException(400, "Masofa va litr musbat bo'lishi kerak")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE user_id=?", (payload.user_id,)
    ).fetchone()
    if not user:
        conn.close()
        raise HTTPException(404, "Foydalanuvchi topilmadi. Avval ro'yxatdan o'ting.")

    conn.execute(
        """
        INSERT INTO fuel_entries (user_id, liters, distance_km, amount_sum, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload.user_id,
            payload.liters,
            payload.distance_km,
            payload.amount_sum,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()

    lp100 = round((payload.liters / payload.distance_km) * 100, 2)
    saving_pct = round((1 - (lp100 / user["baseline_lp100"])) * 100, 1)
    conn.close()
    return {"ok": True, "lp100": lp100, "saving_pct": saving_pct}


def _week_start_iso():
    now = datetime.utcnow()
    monday = now - timedelta(days=now.weekday())
    return monday.strftime("%Y-%m-%dT00:00:00")


@app.get("/api/leaderboard")
def leaderboard(city: str = "Buxoro", limit: int = 20):
    conn = get_db()
    week_start = _week_start_iso()

    rows = conn.execute(
        """
        SELECT u.user_id, u.name, u.car_model, u.baseline_lp100,
               SUM(f.liters) as total_liters,
               SUM(f.distance_km) as total_km
        FROM users u
        JOIN fuel_entries f ON f.user_id = u.user_id
        WHERE u.city = ? AND f.created_at >= ?
        GROUP BY u.user_id
        HAVING total_km > 0
        """,
        (city, week_start),
    ).fetchall()
    conn.close()

    board = []
    for r in rows:
        lp100 = round((r["total_liters"] / r["total_km"]) * 100, 2)
        saving_pct = round((1 - (lp100 / r["baseline_lp100"])) * 100, 1)
        board.append(
            {
                "user_id": r["user_id"],
                "name": r["name"],
                "car_model": r["car_model"],
                "lp100": lp100,
                "saving_pct": saving_pct,
            }
        )

    # Eng tejamkorlar (eng past L/100km emas -- eng yuqori tejamkorlik %) tepada
    board.sort(key=lambda x: x["saving_pct"], reverse=True)
    for i, entry in enumerate(board, start=1):
        entry["rank"] = i

    return {"city": city, "week_start": week_start, "leaderboard": board[:limit]}


@app.get("/api/profile/{user_id}")
def profile(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(404, "Foydalanuvchi topilmadi")

    week_start = _week_start_iso()
    stats = conn.execute(
        """
        SELECT SUM(liters) as total_liters, SUM(distance_km) as total_km, COUNT(*) as entries
        FROM fuel_entries WHERE user_id=? AND created_at >= ?
        """,
        (user_id, week_start),
    ).fetchone()
    conn.close()

    total_liters = stats["total_liters"] or 0
    total_km = stats["total_km"] or 0
    lp100 = round((total_liters / total_km) * 100, 2) if total_km else None
    saving_pct = (
        round((1 - (lp100 / user["baseline_lp100"])) * 100, 1) if lp100 else None
    )

    return {
        "user_id": user_id,
        "name": user["name"],
        "city": user["city"],
        "car_model": user["car_model"],
        "week_lp100": lp100,
        "week_saving_pct": saving_pct,
        "entries_this_week": stats["entries"] or 0,
    }


@app.get("/")
def health():
    return {"status": "TEJA RACE API ishlayapti"}
