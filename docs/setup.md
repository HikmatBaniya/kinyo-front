# Backend Setup

## Requirements
- Python 3.11+
- PostgreSQL (prod) or SQLite (dev)

## Dev setup

```bash
# 1. Create and activate venv
python -m venv myvenv
# Windows:
myvenv\Scripts\activate
# Unix:
source myvenv/bin/activate

# 2. Install deps
pip install -r requirements.txt

# 3. Configure env
cp .env.example .env
# Edit .env — set ELEVENLABS_API_KEY and SECRET_KEY

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

## Generate a secret key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Create first migration
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

## Project structure

```
swor-front/
├── app/
│   ├── main.py              # FastAPI app + CORS + routers
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   ├── database.py      # Async SQLAlchemy engine + session
│   │   └── security.py      # JWT + bcrypt
│   ├── models/
│   │   ├── user.py          # User model + Plan enum
│   │   ├── api_key.py       # API key model (hashed storage)
│   │   └── usage_log.py     # Per-request usage tracking
│   ├── schemas/             # Pydantic request/response models
│   ├── services/
│   │   ├── elevenlabs.py    # ElevenLabs HTTP client
│   │   └── api_key.py       # Key generation, hashing, lookup
│   └── api/v1/
│       ├── deps.py          # JWT + API key auth dependencies
│       ├── auth.py          # /auth/* routes
│       ├── tts.py           # /tts/* routes
│       ├── keys.py          # /keys/* routes
│       └── usage.py         # /usage/* routes
├── alembic/                 # DB migrations
├── docs/                    # This folder
├── requirements.txt
├── .env.example
└── alembic.ini
```

## API key flow

1. User registers → gets JWT
2. User hits `POST /keys` → gets `swor_live_xxx...` key (shown once)
3. Key stored as SHA-256 hash — never stored in plaintext
4. External app sends `X-API-Key: swor_live_xxx...` → `/tts/v1/synthesize`
5. Usage logged per request

## ElevenLabs voice

Default voice ID set in `app/services/elevenlabs.py → DEFAULT_NEPALI_VOICE_ID`.
Update with ElevenLabs voice ID that best supports Nepali (use `eleven_multilingual_v2` model).
