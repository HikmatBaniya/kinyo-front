# Swor API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

---

## Authentication

### Register
`POST /auth/register`

```json
{
  "email": "user@example.com",
  "password": "strongpassword",
  "full_name": "Ram Sharma",
  "organization": "Acme Corp"
}
```

Response: `{ access_token, token_type, user }`

### Login
`POST /auth/login`

```json
{ "email": "user@example.com", "password": "strongpassword" }
```

### Get current user
`GET /auth/me`
Header: `Authorization: Bearer <token>`

---

## Text-to-Speech

### Synthesize (Dashboard — JWT)
`POST /tts/synthesize`
Header: `Authorization: Bearer <token>`

```json
{
  "text": "नमस्ते, यो एउटा परीक्षण हो।",
  "voice_id": null,
  "model_id": "eleven_multilingual_v2",
  "stability": 0.5,
  "similarity_boost": 0.75,
  "style": 0.0,
  "use_speaker_boost": true
}
```

Response: `audio/mpeg` binary stream

### Synthesize (API — X-API-Key)
`POST /tts/synthesize/external`
Header: `X-API-Key: swor_live_xxxx...`

Same body as above.

### List Voices
`GET /tts/voices`
Header: `Authorization: Bearer <token>`

---

## API Keys

### Create key
`POST /keys`
Header: `Authorization: Bearer <token>`

```json
{ "name": "production-app" }
```

Response includes `key` field — **only shown once**.

### List keys
`GET /keys`

### Revoke key
`DELETE /keys/{key_id}`

---

## Usage

### Summary
`GET /usage/summary`
Response: `{ total_requests, total_characters }`

### Logs
`GET /usage/logs?limit=50`

---

## Plans & Limits

| Plan       | Characters/request | Monthly chars |
|------------|--------------------|---------------|
| free       | 5,000              | 5,000         |
| starter    | 5,000              | 100,000       |
| pro        | 5,000              | 500,000       |
| enterprise | 5,000              | 10,000,000    |

---

## Error Codes

| Code | Meaning              |
|------|----------------------|
| 400  | Validation error     |
| 401  | Unauthorized         |
| 403  | Forbidden / disabled |
| 429  | Plan limit exceeded  |
| 502  | ElevenLabs upstream error |
