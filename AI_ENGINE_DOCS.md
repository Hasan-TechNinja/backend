# Glowmi AI Engine — Backend Integration Guide

> **Audience:** Backend Django developer.  
> **File you need:** `product/ai_engine.py` — drop it in, call it, done.  
> **No Django ORM, no database, no Celery** inside the engine. You bring the data, the engine does the thinking.

---

## How it works in one sentence

You build two plain Python objects from your database — a **user profile dict** and a **product catalog list** — then `await` one of the two public functions. That's it.

```
Django view
  │
  ├─ build user_profile dict  (from account.User / account.Profile)
  ├─ build product_catalog list (from product.Product queryset)
  │
  └─▶ await generate_routine(...)  →  dict  (AM/PM routine)
       await chat_assistant(...)   →  dict  (reply + memory + flag)
```

---

## 1. Setup

### Environment variable

Add **one** of these to your `.env`:

```env
GEMINI_API_KEY=your_key_here
```

The engine also checks `GIMINIAPI_KEY` and `GOOGLE_API_KEY` as fallbacks (useful if you already have one of those set).

### Python dependencies

```bash
pip install google-genai pydantic python-dotenv
```

### Import

```python
from product.ai_engine import generate_routine, chat_assistant, update_summary_anchor
```

---

## 2. Data you need to build

### `user_profile` — plain dict

Build this from your DB models. Every field is optional except `language`, `skin_type`, and `concerns` — but pass as many as you have because the AI uses them all.

```python
user_profile = {
    # --- Core (pass these at minimum) ---
    "language":         "en",           # "en" or "ar"
    "skin_type":        "combination",  # "oily", "dry", "combination", "sensitive", "normal"
    "concerns":         ["dullness", "uneven tone"],  # list of strings

    # --- From account.Profile ---
    "full_name":        "Noor Al-Farsi",
    "gender":           "female",
    "age":              29,             # OR pass "date_of_birth" (ISO string) and engine derives age
    "account_tenure_days": 120,

    # --- From intake form / extended profile ---
    "allergies":        ["fragrance"],  # engine hard-blocks these in the routine
    "climate":          "Riyadh arid",
    "sensitivity_level": "medium",      # "low", "medium", "high"
    "current_products": ["vitamin C serum"],
    "additional_details": "Wants a minimal, fast morning routine.",

    # --- Pregnancy (important!) ---
    # Do NOT set is_pregnant from a toggle or checkbox.
    # Let the user mention it in chat — the AI picks it up via dynamic override.
    # Only set this to True if your Profile model has a confirmed, verified field.
    "is_pregnant": False,
}
```

> **Pregnancy note:** If `is_pregnant` is `True`, the engine automatically hard-blocks retinol, salicylic acid, BHA, hydroquinone, and other pregnancy-unsafe actives from ALL routine recommendations. This is enforced both in the AI prompt AND as a post-filter on the returned data.

### `product_catalog` — list of dicts

Serialize your `product.Product` queryset into this shape. The AI will **only** recommend products from this list (closed-world assumption).

```python
product_catalog = [
    {
        "id":          1,                 # int — used to link steps back to DB records
        "name":        "Glowmi Celestial Glow Brightening Serum",
        "name_ar":     "سيروم Glowmi التفتيح السماوي",  # optional
        "type":        "Serum",           # e.g. "Cleanser", "Moisturizer", "Sunscreen"
        "ingredients": "Niacinamide, Tranexamic Acid, Alpha Arbutin",
        "benefits":    "Brightening, barrier support",
        "safety":      "Pregnancy-caution (contains Alpha Arbutin)",
        "price":       289.0,
        "image_url":   "https://cdn.glowmi.net/products/1.jpg",
        "product_url": "https://glowmi.net/shop/celestial-glow-serum",
        # optional extras:
        "how_to_use":  "Apply 2-3 drops on clean skin before moisturizer.",
        "size":        "30ml",
    },
    # ... more products
]
```

---

## 3. Public functions

### A. `generate_routine` — AM/PM skincare routine

```python
routine = await generate_routine(
    user_profile=user_profile,
    product_catalog=product_catalog,
    user_image_b64=None,   # optional: base64 string of a skin photo
)
```

**Returns a dict** — always. Never raises. If Gemini fails, you get a safe generic fallback with `product_id: None` on every step.

```json
{
  "am_routine": [
    {
      "step":               "Cleanser",
      "product_id":         4,
      "product_name":       "Glowmi Oasis Gentle Cream Cleanser",
      "rationale":          "Gentle daily cleanse without stripping.",
      "medical_disclaimer": false,
      "image_url":          "https://cdn.glowmi.net/products/4.jpg",
      "product_url":        "https://glowmi.net/shop/oasis-cleanser",
      "price":              169.0
    },
    ...
  ],
  "pm_routine": [ ... ]
}
```

**Key points:**
- `product_id` matches `id` in your catalog — use it to link to your DB record.
- `product_id` is `null` when no safe product exists (e.g. every serum contains a blocked ingredient for a pregnant user).
- `medical_disclaimer: true` means the AI is suggesting a doctor visit for that step.
- The engine post-filters results — even if Gemini recommends a pregnancy-unsafe product, the filter strips it out.

---

### B. `chat_assistant` — conversational concierge

This is the main chat endpoint. It needs the user's message, the conversation history, and the rolling memory anchor.

```python
result = await chat_assistant(
    user_input="What should I use for sudden breakouts on my chin?",
    chat_history=[
        {"role": "user",      "content": "My T-zone has been oily this week."},
        {"role": "assistant", "content": "Noted — let me keep that in mind."},
    ],
    summary_anchor="Returning customer Noor (Riyadh). Allergic to fragrance.",
    user_profile=user_profile,
    product_catalog=product_catalog,
    user_image_b64=None,   # optional: base64 skin photo
)
```

**Returns a dict** — always. Never raises.

```python
{
    "response":               "For breakouts on your chin...",  # str: the AI's reply
    "updated_summary_anchor": "Noor (Riyadh). Oily T-zone ...", # str: new compressed memory
    "is_for_friend":          False,  # bool: True if user asked about a friend
}
```

**What your view needs to do with this:**

```python
# Save these back to the DB/session after every message:
chat_session.summary_anchor = result["updated_summary_anchor"]
chat_session.save()

# Append the exchange to your chat history storage:
chat_history.append({"role": "user",      "content": user_input})
chat_history.append({"role": "assistant", "content": result["response"]})
```

**The `is_for_friend` flag:**

When this is `True`, the user is asking for advice for a friend or family member. In this case:
- The engine has already asked the friend's details via the `response`.
- `updated_summary_anchor` returns the **old** anchor unchanged — friend data is never saved to the main user's memory.
- You should **not** save any profile updates triggered by this conversation turn.

```python
if not result["is_for_friend"]:
    chat_session.summary_anchor = result["updated_summary_anchor"]
    chat_session.save()
# if is_for_friend: do nothing with the anchor
```

---

### C. `update_summary_anchor` — memory compression (optional, manual use)

The `chat_assistant` function already calls this internally and returns the updated anchor. You only need to call this directly if you want to compress memory outside of a chat turn (e.g., a background Celery task).

```python
new_anchor = await update_summary_anchor(
    old_anchor="Noor (Riyadh). Allergic to fragrance. Prefers minimal routine.",
    new_messages=[
        {"role": "user",      "content": "I've started using retinol."},
        {"role": "assistant", "content": "Since you're pregnant, I'd recommend stopping that."},
    ],
    language="en",   # "en" or "ar"
)
# Returns a string — the compressed memory summary.
# Falls back to old_anchor if Gemini fails.
```

---

## 4. Memory model explained

The engine uses a two-layer memory system. Your DB/session needs to store two things per user:

| What to store | Type | Purpose |
|---|---|---|
| `summary_anchor` | `str` | Long-term compressed memory (≤ 400 words). The AI always reads this. |
| `chat_history` | `list[dict]` | Recent raw messages. The engine internally uses only the **last 10** for the prompt. You can store more, but only 10 are sent to Gemini. |

**Recommended model fields:**

```python
# In a ChatSession model (or on account.Profile):
summary_anchor = models.TextField(default="", blank=True)
# chat_history stored in session, Redis, or a related ChatMessage model
```

**Flow per message:**

```
User sends message
    │
    ▼
chat_assistant(user_input, chat_history[-10:], summary_anchor, ...)
    │
    ▼
Returns: { response, updated_summary_anchor, is_for_friend }
    │
    ├─ Save updated_summary_anchor to DB (if not is_for_friend)
    └─ Append {user, assistant} messages to chat_history
```

---

## 5. Django view example (async)

```python
# userapi/views.py
import json
from django.http import JsonResponse
from asgiref.sync import sync_to_async

from product.ai_engine import generate_routine, chat_assistant
from product.models import Product
from account.models import Profile


# ── Helper: build profile dict from DB ────────────────────────────────────────
async def _build_profile(user) -> dict:
    profile = await Profile.objects.aget(user=user)
    return {
        "language":           profile.language or "en",
        "full_name":          user.get_full_name(),
        "gender":             profile.gender,
        "age":                profile.age,         # or pass date_of_birth
        "skin_type":          profile.skin_type,
        "concerns":           profile.concerns,    # list field
        "allergies":          profile.allergies,
        "climate":            profile.climate,
        "sensitivity_level":  profile.sensitivity_level,
        "account_tenure_days": (user.date_joined - today).days,
        "is_pregnant":        False,  # let the AI infer from chat
    }


# ── Helper: build catalog from DB ─────────────────────────────────────────────
async def _build_catalog() -> list:
    return [
        p async for p in Product.objects.filter(is_active=True).values(
            "id", "name", "name_ar", "type",
            "ingredients", "benefits", "safety",
            "price", "image_url", "product_url",
        )
    ]


# ── Routine endpoint ───────────────────────────────────────────────────────────
async def routine_view(request):
    user_profile  = await _build_profile(request.user)
    product_catalog = await _build_catalog()

    routine = await generate_routine(
        user_profile=user_profile,
        product_catalog=product_catalog,
    )
    return JsonResponse(routine)


# ── Chat endpoint ──────────────────────────────────────────────────────────────
async def chat_view(request):
    body        = json.loads(request.body)
    user_input  = body["message"]
    image_b64   = body.get("image_b64")       # optional base64 skin photo

    # Load session memory
    chat_history   = request.session.get("chat_history", [])
    summary_anchor = request.session.get("summary_anchor", "")

    user_profile    = await _build_profile(request.user)
    product_catalog = await _build_catalog()

    result = await chat_assistant(
        user_input=user_input,
        chat_history=chat_history,
        summary_anchor=summary_anchor,
        user_profile=user_profile,
        product_catalog=product_catalog,
        user_image_b64=image_b64,
    )

    # Update session memory (skip anchor update if friend conversation)
    chat_history.append({"role": "user",      "content": user_input})
    chat_history.append({"role": "assistant", "content": result["response"]})
    request.session["chat_history"] = chat_history[-30:]  # keep last 30 in session

    if not result["is_for_friend"]:
        request.session["summary_anchor"] = result["updated_summary_anchor"]

    return JsonResponse({
        "reply":         result["response"],
        "is_for_friend": result["is_for_friend"],
    })
```

---

## 6. Built-in safety behaviours (you get these for free)

| Behaviour | What triggers it | What happens |
|---|---|---|
| **Emergency intercept** | User says "burning", "peeling", "swelling", "rash", etc. | Returns a stop-and-see-a-doctor message **instantly**, no Gemini call made |
| **Pregnancy safety** | `is_pregnant: True` in profile | Retinol, BHA, hydroquinone, etc. are blocked in the AI prompt AND post-filtered from the returned routine |
| **Allergy filter** | `allergies` list in profile | Products containing those ingredients are replaced with `product_id: null` |
| **Closed-world** | Any mention of competitor brands | AI redirects to nearest Glowmi equivalent |
| **Gemini failure fallback** | API timeout / error | Returns safe generic routine or polite "high traffic" message — **never raises an exception** |
| **"Someone Else" logic** | User mentions a friend or family member | AI asks for friend's details, does not use main user's profile, `is_for_friend: True` is returned |

---

## 7. Language handling

You don't need to do anything special. The engine auto-detects the language:

1. If `user_profile["language"]` is `"ar"` → responds in Arabic.
2. If the user's message contains Arabic characters → overrides to Arabic.
3. Default is English.

**Dynamic override:** If the user says something in chat that contradicts their static profile (e.g., profile says dry skin but user says "my skin is very oily this week"), the AI prioritises the **most recent message**. This is by design.

---

## 8. Image upload (optional)

Both functions accept an optional `user_image_b64` parameter. Pass a base64-encoded JPEG/PNG of the user's skin and the AI will analyse it alongside the text.

```python
import base64

with open("skin_photo.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

routine = await generate_routine(
    user_profile=user_profile,
    product_catalog=product_catalog,
    user_image_b64=image_b64,
)
```

The engine handles the `data:image/jpeg;base64,...` data-URL prefix automatically — strip it or don't, both work.

---

## 9. Quick reference

```python
# All three imports you need:
from product.ai_engine import generate_routine, chat_assistant, update_summary_anchor

# generate_routine
result: dict = await generate_routine(
    user_profile: dict,
    product_catalog: list[dict],
    user_image_b64: str | None = None,
)
# → { "am_routine": [...], "pm_routine": [...] }

# chat_assistant
result: dict = await chat_assistant(
    user_input: str,
    chat_history: list[dict],   # [{"role": "user"|"assistant", "content": "..."}]
    summary_anchor: str,
    user_profile: dict,
    product_catalog: list[dict],
    user_image_b64: str | None = None,
)
# → { "response": str, "updated_summary_anchor": str, "is_for_friend": bool }

# update_summary_anchor (usually called automatically by chat_assistant)
new_anchor: str = await update_summary_anchor(
    old_anchor: str,
    new_messages: list[dict],
    language: str = "en",
)
# → str (compressed memory text, ≤ 400 words)
```

---

## 10. What the engine does NOT handle (your responsibility)

| Task | You need to handle |
|---|---|
| Storing `chat_history` | Session, Redis, or a `ChatMessage` DB model |
| Storing `summary_anchor` | `ChatSession` or `Profile` field |
| Auth & permissions | Django auth / JWT |
| Rate limiting | DRF throttling or API gateway |
| Image upload from client | Parse multipart form, encode to base64, pass the string |
| Serving the catalog | Django queryset → list of dicts (see Section 2) |
