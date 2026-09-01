# 🏁 TEJA RACE

Haydovchilar uchun yonilg'i tejamkorligi o'yini (Telegram Mini App).
Benzin sarfini kiritasiz, tejamkorlik reytingida raqobatlashasiz.

## Tuzilish

```
tejarace/
├── backend/   → FastAPI + SQLite API (va Mini App'ni xizmat qiladi)
├── bot/       → Telegram bot (python-telegram-bot)
└── webapp/    → Frontend (yagona index.html, Mini App)
```

Backend `GET /` da `webapp/index.html` ni ham xizmat qiladi — Mini App va
API bir xil HTTPS manzilda (origin) ishlaydi, shuning uchun alohida sozlash shart emas.

## Lokal ishga tushirish

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8811
```

Keyin brauzerda `http://127.0.0.1:8811` oching. API: `/api/health`, `/api/leaderboard` va h.k.

## Render'ga deploy (production)

1. Bu kod'ni GitHub'ga push qiling.
2. [render.com](https://render.com) da **New → Blueprint** ni tanlang.
3. `JASCOJI123/tejarace` reponi bog'lang — `render.yaml` avtomatik qo'llanadi.
4. Render sizga HTTPS manzil beradi (masalan `https://teja-race.onrender.com`). Shu manzil **WEBAPP_URL** va Mini App manzili bo'ladi.

> Eslatma: Render bepul tier 15 daqiqa harakatsizlikdan keyin uxlaydi va
> SQLite fayli har deploy'da yo'qoladi (demo uchun yetarli). Doimiy-ish va
> ma'lumotlarni saqlash uchun paid plan + PostgreSQL tavsiya etiladi.

## Botni ishga tushirish

`BOT_TOKEN`ni [@BotFather](https://t.me/BotFather)'dan oling, `WEBAPP_URL`ni
Render manziliga qo'ying:

```bash
cd bot
python -m pip install -r requirements.txt
BOT_TOKEN="..." WEBAPP_URL="https://teja-race.onrender.com" python bot.py
```

> Bot `run_polling` orqali ishlaydi — kompyuter yoqilgan bo'lsa ishlaydi.
> Doimiy ishlashi uchun uni alohida server/hosting'ga ko'chirish kerak.
