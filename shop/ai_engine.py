import io
import json
import logging
import os
import re
from collections.abc import AsyncGenerator

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from PIL import Image
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types

from .catalog import get_catalog_product

# Load environment variables
load_dotenv()

LITE_MODEL = "gemini-3.1-flash-lite"
# Tried in order until one succeeds
MODELS_TO_TRY = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

client = genai.Client(
    api_key=os.getenv("GIMINIAPI_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
)

PRODUCT_MARKER = re.compile(r"\[\[PRODUCT:(\d+)\]\]")
ROUTINE_MARKER = "[[GENERATE_ROUTINE]]"

# ---------------------------------------------------------------------------
# 1. Safety Constants & Rules
# ---------------------------------------------------------------------------
PREGNANCY_UNSAFE_INGREDIENTS = [
    "retinol", "retinoid", "tretinoin", "adapalene",
    "salicylic acid", "bha", "benzoyl peroxide", "hydroquinone",
    "chemical sunscreen", "arbutin", "high-dose vitamin a"
]

PREGNANCY_KEYWORDS_EN = [
    "pregnant", "pregnancy", "expecting", "nursing", "breastfeeding",
    "having a baby", "trimester", "maternity"
]
PREGNANCY_KEYWORDS_AR = [
    "حامل", "حمل", "مرضعة", "رضاعة", "أتوقع طفلاً", "حوامل"
]

FRIEND_KEYWORDS_EN = [
    "my friend", "my mother", "my mom", "my sister", "someone else",
    "for a friend", "husband", "brother", "wife"
]
FRIEND_KEYWORDS_AR = [
    "صديقتي", "أمي", "أختي", "شخص آخر", "لصديق", "زوجي", "أخي", "زوجتي", "لصديقتي"
]

EMERGENCY_KEYWORDS_EN = [
    "severe burning", "peeling skin", "swelling", "bleeding",
    "extreme pain", "blisters", "severe allergic reaction"
]
EMERGENCY_KEYWORDS_AR = [
    "حروق شديدة", "تقشر الجلد", "تورم", "نزيف",
    "ألم شديد", "بثور", "رد فعل تحسسي شديد"
]

GREETINGS_EN = {
    "hi", "hii", "hello", "hey", "hey there", "hi there", "hello there", "good morning",
    "good afternoon", "good evening", "salam", "salaam", "assalamualaikum", "assalamu alaikum",
}
GREETINGS_AR = {
    "مرحبا", "مرحباً", "اهلا", "أهلا", "أهلاً", "هلا", "السلام عليكم", "سلام", "صباح الخير", "مساء الخير",
}

# ---------------------------------------------------------------------------
# 2. Pydantic Schemas for Structured Outputs
# ---------------------------------------------------------------------------
class RoutineStep(BaseModel):
    product_id: int = Field(description="The ID of the recommended product from the catalog.")
    step_number: int = Field(description="The order of this step (e.g., 1, 2, 3).")
    step: str = Field(description="Short name of the step, e.g. 'Cleanser', 'Serum', 'Moisturizer', 'Sunscreen'.")
    rationale: str = Field(description="One or two short sentences on why this product suits the user's concerns.")
    usage_instructions: str = Field(description="Specific instructions on how and when to use.")
    medical_disclaimer: bool = Field(default=False, description="True only if this step needs a dermatologist's input.")

class RoutineSchema(BaseModel):
    morning_routine: list[RoutineStep] = Field(description="Steps for the morning routine.")
    evening_routine: list[RoutineStep] = Field(description="Steps for the evening routine.")
    reasoning: str = Field(description="A brief paragraph explaining why this routine was curated.")

class ProductReference(BaseModel):
    product_id: int
    context: str

class ChatMetadata(BaseModel):
    product_references: list[ProductReference]
    is_for_friend: bool
    full_response: str
    detected_language: str
    triggers_routine: bool = False

# ---------------------------------------------------------------------------
# 3. Helper Functions
# ---------------------------------------------------------------------------
def _resolve_language(text: str, fallback: str = "en") -> str:
    """Arabic if the text is mostly Arabic, English if it has Latin letters, otherwise the fallback."""
    arabic_chars = sum(1 for c in text if '؀' <= c <= 'ۿ')
    if arabic_chars > len(text) * 0.1:
        return "ar"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return fallback if fallback in ("en", "ar") else "en"

def _detect_context_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)

def _detect_pregnancy_context(prompt: str, chat_history: list, anchor: str) -> bool:
    full_context = f"{anchor} {prompt} " + " ".join(
        m.get("content", "") for m in chat_history if isinstance(m.get("content"), str)
    )
    return (_detect_context_keywords(full_context, PREGNANCY_KEYWORDS_EN) or
            _detect_context_keywords(full_context, PREGNANCY_KEYWORDS_AR))

def _detect_friend_context(prompt: str) -> bool:
    return (_detect_context_keywords(prompt, FRIEND_KEYWORDS_EN) or
            _detect_context_keywords(prompt, FRIEND_KEYWORDS_AR))

def _detect_medical_emergency(prompt: str) -> bool:
    return (_detect_context_keywords(prompt, EMERGENCY_KEYWORDS_EN) or
            _detect_context_keywords(prompt, EMERGENCY_KEYWORDS_AR))

def _is_greeting(prompt: str) -> bool:
    normalized = re.sub(r"[!.,؟?\s]+", " ", prompt.strip().lower()).strip()
    return normalized in GREETINGS_EN or normalized in GREETINGS_AR

def _first_name(user_profile: dict) -> str:
    full_name = (user_profile.get("full_name") or "").strip()
    return full_name.split()[0] if full_name else ""

def _greeting_reply(user_profile: dict, language: str) -> str:
    name = _first_name(user_profile)
    if language == "ar":
        hello = f"أهلاً {name}." if name else "أهلاً بك."
        return (
            f"{hello} مرحباً بك في Glowmi Skin Intelligence.\n\n"
            "لأفهم بشرتك بشكل أفضل، بماذا تود أن أساعدك اليوم؟\n\n"
            "- حب الشباب والبثور\n- البقع الداكنة\n- الجفاف\n- الحساسية\n- الخطوط الدقيقة\n- نصائح عامة للعناية بالبشرة\n\n"
            "يمكنك أيضاً وصف ما تشعر به بكلماتك."
        )
    hello = f"Hello {name}." if name else "Hello."
    return (
        f"{hello} Welcome to Glowmi Skin Intelligence.\n\n"
        "To help me understand your skin better, what would you like support with today?\n\n"
        "- Acne & Breakouts\n- Dark Spots\n- Dryness\n- Sensitivity\n- Fine Lines\n- General Skincare Advice\n\n"
        "You may also describe your concern in your own words."
    )

def _build_sliding_window(chat_history: list, window_size: int = 10) -> list:
    return chat_history[-window_size:] if len(chat_history) > window_size else chat_history

def _image_part(image: Image.Image) -> types.Part:
    buffer = io.BytesIO()
    fmt = image.format or "PNG"
    image.save(buffer, format=fmt)
    return types.Part.from_bytes(data=buffer.getvalue(), mime_type=f"image/{fmt.lower()}")

def _catalog_for_prompt(product_catalog: list) -> str:
    slim = [
        {k: p.get(k) for k in ("id", "name", "category", "sub_title", "skin_type", "ingredients", "benefits", "size", "price", "in_stock")}
        for p in product_catalog
    ]
    return json.dumps(slim, ensure_ascii=False, indent=1)

def _known_profile_lines(user_profile: dict) -> str:
    """Only facts the user actually gave us. Missing facts are listed as unknown so the model never invents them."""
    facts = {
        "Name": user_profile.get("full_name"),
        "Skin type": user_profile.get("skin_type"),
        "Age": user_profile.get("age"),
        "Gender": user_profile.get("gender"),
        "Concerns": ", ".join(user_profile.get("concerns") or []),
        "Allergies / ingredients to avoid": ", ".join(user_profile.get("allergies") or []),
        "Additional details": user_profile.get("additional_details"),
    }
    return "\n".join(f"- {label}: {value if value else 'unknown (do not assume)'}" for label, value in facts.items())

def _chat_system_prompt(
    user_profile: dict,
    product_catalog: list,
    summary_anchor: str,
    is_pregnant: bool,
    is_for_friend: bool,
    language: str,
) -> str:
    prompt = f"""You are Glowmi Skin Intelligence, the skincare consultant of Glowmi, a luxury, science-backed Saudi skincare brand.
You behave like a calm, warm, knowledgeable skincare consultant in a premium boutique, never like a product-pushing chatbot.
Never call yourself an AI, a bot, or an assistant. Never mention "AI".

Consultation rules (follow strictly):
1. Understand before advising. Before recommending any product you must know: the main concern, the skin type, and an approximate age range. Optional: current routine, sensitivities, allergies.
2. If any of those are unknown, ask for ONE missing detail only. One simple question per message.
3. While gathering information keep replies short and human: 1 to 3 short sentences. No reports, no lists of tips, no products.
4. Never assume facts the user has not given you: no assumed skin type, age, sensitivity, gender, or location/climate. Only mention climate (heat, sun, AC, dust) if the user brings it up.
5. Once you have enough information, give guidance in short sections (short headings or bullets, no dense paragraphs):
   - what is likely happening and the skincare approach,
   - the Glowmi product(s) that fit and why, tied to the user's concern,
   - how to use them.
   End with one gentle line that this is skincare guidance, not a medical diagnosis.
6. Recommend at most 2 products per reply, only when relevant, and only from the Glowmi catalog below. Never recommend other brands. Skip products where in_stock is false.
7. When you mention a catalog product, write the marker [[PRODUCT:id]] in place of its name (example: "I would suggest [[PRODUCT:3]] because..."). No markdown around the marker.
8. If the user explicitly asks for a complete morning/evening routine AND you already know their concern, skin type and age, reply with one or two sentences and end with the marker {ROUTINE_MARKER}. Do not write the routine yourself.
9. For severe symptoms (bleeding, swelling, intense pain, spreading rash) advise seeing a dermatologist and do not recommend products.
10. Use the user's first name occasionally, not in every message, and do not greet again after the first message.

What the user has told us so far:
{_known_profile_lines(user_profile)}

Long-term memory from earlier conversations:
{summary_anchor or 'None yet.'}

Glowmi catalog:
{_catalog_for_prompt(product_catalog)}
"""
    if is_pregnant:
        prompt += "\nCRITICAL SAFETY: The user is pregnant or nursing. Never recommend products containing retinoids, BHA/salicylic acid, benzoyl peroxide, hydroquinone or arbutin. Check ingredients before recommending."
    if is_for_friend:
        prompt += "\nNOTICE: The user is asking for someone else. Do not use the user's own profile details for this answer; ask about the other person instead."

    prompt += "\n\nLanguage: respond entirely in Arabic." if language == "ar" else "\n\nLanguage: respond entirely in English."
    return prompt

def _routine_system_prompt(user_profile: dict, product_catalog: list, summary_anchor: str, is_pregnant: bool, language: str) -> str:
    prompt = f"""You are Glowmi Skin Intelligence, building a personalised morning and evening skincare routine for a Glowmi customer.

Rules:
- Use ONLY products from the Glowmi catalog below, referenced by their integer id. Never invent ids. Skip products where in_stock is false.
- Base every choice on the user's stated skin type, age, concerns and details. Do not assume anything they did not state.
- Keep each routine focused: 2 to 5 steps, in the correct application order. Do not repeat a product within the same routine unless it is genuinely used morning and night.
- Sunscreen belongs in the morning routine only.
- `step` is a short step name (Cleanser, Serum, Moisturizer, Sunscreen, Mask...).
- `rationale` is one or two short sentences tying the product to the user's concerns.
- Set `medical_disclaimer` to true only for steps where a dermatologist should be consulted.
- `reasoning` is a short, calm paragraph (max 3 sentences) summarising the approach.

User profile:
{_known_profile_lines(user_profile)}

Long-term memory:
{summary_anchor or 'None.'}

Glowmi catalog:
{_catalog_for_prompt(product_catalog)}
"""
    if is_pregnant:
        prompt += "\nCRITICAL SAFETY: The user is pregnant or nursing. Exclude any product containing retinoids, BHA/salicylic acid, benzoyl peroxide, hydroquinone or arbutin."
    prompt += "\nWrite `step`, `rationale`, `usage_instructions` and `reasoning` in Arabic." if language == "ar" else "\nWrite all text in English."
    return prompt

def _product_label(product_catalog: list, product_id: int) -> str:
    product = get_catalog_product(product_catalog, product_id)
    return f"**{product['name']}**" if product else ""

def _replace_markers(text: str, product_catalog: list) -> str:
    return PRODUCT_MARKER.sub(lambda m: _product_label(product_catalog, int(m.group(1))), text)

# ---------------------------------------------------------------------------
# 4. Core Engine Functions
# ---------------------------------------------------------------------------

async def stream_chat_assistant(
    user_profile: dict,
    chat_history: list,
    current_prompt: str,
    product_catalog: list,
    summary_anchor: str = "",
    image: Image.Image | None = None,
    language: str = "en",
) -> AsyncGenerator[str | ChatMetadata, None]:
    """
    Streams markdown text chunks (product markers already replaced by names)
    and finally yields a ChatMetadata object.
    """
    detected_lang = _resolve_language(current_prompt, language)
    is_pregnant = _detect_pregnancy_context(current_prompt, chat_history, summary_anchor)
    is_for_friend = _detect_friend_context(current_prompt)

    # A plain greeting gets a short welcome, never a recommendation.
    if image is None and _is_greeting(current_prompt):
        msg = _greeting_reply(user_profile, detected_lang)
        yield msg
        yield ChatMetadata(product_references=[], is_for_friend=False, full_response=msg, detected_language=detected_lang)
        return

    if _detect_medical_emergency(current_prompt):
        msg = (
            "I'm sorry you're going through this. Please rinse your face with cool water, pause all active products, and see a dermatologist as soon as possible. Severe reactions need in-person medical care."
            if detected_lang == "en" else
            "يؤسفني ما تمر به. يرجى غسل وجهك بالماء البارد، والتوقف عن استخدام المنتجات النشطة، ومراجعة طبيب جلدية في أقرب وقت. الحالات الشديدة تحتاج إلى رعاية طبية مباشرة."
        )
        yield msg
        yield ChatMetadata(product_references=[], is_for_friend=is_for_friend, full_response=msg, detected_language=detected_lang)
        return

    system_instruction = _chat_system_prompt(
        user_profile, product_catalog, summary_anchor, is_pregnant, is_for_friend, detected_lang
    )

    contents = []
    for msg in _build_sliding_window(chat_history, 10):
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

    parts = []
    if image:
        parts.append(_image_part(image))
    parts.append(types.Part.from_text(text=current_prompt or "Please look at this photo of my skin."))
    contents.append(types.Content(role="user", parts=parts))

    config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.6)

    full_text = ""
    pending = ""  # text held back while a [[...]] marker may still be incomplete
    last_exception = None
    for model_id in MODELS_TO_TRY:
        try:
            stream = await client.aio.models.generate_content_stream(
                model=model_id, contents=contents, config=config
            )
            async for chunk in stream:
                if not chunk.text:
                    continue
                full_text += chunk.text
                pending += chunk.text

                # Emit everything up to an unfinished marker
                cut = pending.rfind("[[")
                if cut != -1 and "]]" not in pending[cut:]:
                    ready, pending = pending[:cut], pending[cut:]
                else:
                    ready, pending = pending, ""
                ready = _replace_markers(ready, product_catalog).replace(ROUTINE_MARKER, "")
                if ready:
                    yield ready
            last_exception = None
            break
        except Exception as e:
            last_exception = e
            logging.warning(f"Stream failed with {model_id}: {e}")
            if full_text:
                # Part of the answer was already sent; don't restart with another model.
                break

    if pending:
        tail = _replace_markers(pending, product_catalog).replace(ROUTINE_MARKER, "")
        if tail:
            yield tail

    if not full_text:
        logging.error(f"All chat models failed: {last_exception}")
        full_text = (
            "I'm sorry, I couldn't respond just now. Please try again in a moment."
            if detected_lang == "en" else
            "عذراً، لم أتمكن من الرد الآن. يرجى المحاولة مرة أخرى بعد قليل."
        )
        yield full_text

    product_refs = []
    for match in PRODUCT_MARKER.finditer(full_text):
        pid = int(match.group(1))
        if get_catalog_product(product_catalog, pid) and not any(r.product_id == pid for r in product_refs):
            product_refs.append(ProductReference(product_id=pid, context="Mentioned in chat"))

    triggers_routine = ROUTINE_MARKER in full_text
    clean_text = _replace_markers(full_text, product_catalog).replace(ROUTINE_MARKER, "").strip()

    yield ChatMetadata(
        product_references=product_refs,
        is_for_friend=is_for_friend,
        full_response=clean_text,
        detected_language=detected_lang,
        triggers_routine=triggers_routine,
    )


def _post_filter_routine(routine_data: RoutineSchema, product_catalog: list, is_pregnant: bool) -> RoutineSchema:
    def filter_steps(steps: list[RoutineStep]):
        kept = []
        for step in steps:
            product = get_catalog_product(product_catalog, step.product_id)
            if not product:
                logging.warning(f"[ROUTINE] Dropped unknown product id {step.product_id}")
                continue
            if is_pregnant:
                ingredients_text = (product.get("ingredients") or "").lower()
                if any(bad in ingredients_text for bad in PREGNANCY_UNSAFE_INGREDIENTS):
                    logging.warning(f"[SAFETY FILTER] Removed product {step.product_id} due to pregnancy unsafe ingredients.")
                    continue
            kept.append(step)
        return kept

    routine_data.morning_routine = filter_steps(routine_data.morning_routine)
    routine_data.evening_routine = filter_steps(routine_data.evening_routine)
    return routine_data


async def generate_routine(
    user_profile: dict,
    product_catalog: list,
    chat_history: list | None = None,
    summary_anchor: str = "",
    image: Image.Image | None = None,
    language: str = "en",
) -> RoutineSchema | None:
    if not product_catalog:
        logging.error("Cannot generate a routine: the product catalog is empty.")
        return None

    is_pregnant = bool(user_profile.get("is_pregnant")) or _detect_pregnancy_context(
        user_profile.get("additional_details") or "", chat_history or [], summary_anchor
    )
    system_instruction = _routine_system_prompt(user_profile, product_catalog, summary_anchor, is_pregnant, language)

    prompt_content = [types.Part.from_text(text="Please build my Glowmi morning and evening routine.")]
    if image:
        prompt_content.append(types.Part.from_text(text="A photo of my skin is attached; use what you can observe, without diagnosing."))
        prompt_content.append(_image_part(image))

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.4,
        response_mime_type="application/json",
        response_schema=RoutineSchema,
    )

    for model_id in MODELS_TO_TRY:
        try:
            response = await client.aio.models.generate_content(
                model=model_id, contents=prompt_content, config=config
            )
            if response.text:
                routine = RoutineSchema(**json.loads(response.text))
                return _post_filter_routine(routine, product_catalog, is_pregnant)
        except Exception as e:
            logging.warning(f"Failed to generate routine with {model_id}: {e}")
            continue

    return None


async def update_summary_anchor(user_profile: dict, chat_history: list, current_anchor: str = "") -> str:
    if not chat_history:
        return current_anchor

    prompt = f"""
Compress the following conversation and current anchor into a succinct <400 word summary anchor.
Focus on:
- Facts the user stated about their skin: type, age, concerns, sensitivities, allergies, current routine.
- Pregnancy status (if mentioned).
- Recent skin states.
- DO NOT include details specifically asked for a friend (flagged in context).
- DO NOT add facts the user did not state.

Current Anchor: {current_anchor}
User Profile Base: {json.dumps({k: v for k, v in user_profile.items() if k != 'photo'}, ensure_ascii=False, default=str)}

Recent Conversation:
"""
    for msg in _build_sliding_window(chat_history, 5):
        prompt += f"{msg['role']}: {msg['content']}\n"

    try:
        response = await client.aio.models.generate_content(model=LITE_MODEL, contents=prompt)
        return response.text or current_anchor
    except Exception as e:
        logging.error(f"Error updating anchor: {e}")
        return current_anchor
