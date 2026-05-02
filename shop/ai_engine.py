"""
Glowmi AI Engine
================

Single-file async AI service layer for the Glowmi premium luxury skincare
platform. Powered by `google-genai` with Pydantic structured outputs,
pregnancy-safety gating, closed-world catalog enforcement, bilingual EN/AR
routing, and a compressed-anchor + sliding-window memory model.

This module is intentionally Django-agnostic. The Django layer is expected to
build the `user_profile` dict (hydrated from `account.User` + `account.Profile`
plus a future intake form) and the `product_catalog` list (serialized from
`product.Product` + `product.ProductImage`), then `await` the public functions.


Public API
----------
    async generate_routine(user_profile, product_catalog,
                           user_image_b64=None) -> dict
    async chat_assistant(user_input, chat_history, summary_anchor,
                         user_profile, product_catalog,
                         user_image_b64=None) -> dict
    async update_summary_anchor(old_anchor, new_messages,
                                language="en") -> str


Expected `user_profile` shape (TypedDict: `GlowmiUserProfile`)
-------------------------------------------------------------
Required (spec):
    language           : "en" | "ar"
    is_pregnant        : bool
    skin_type          : str
    concerns           : list[str]

Registration-derived (auto-populated from `account.Profile`):
    full_name          : str
    gender             : str
    age                : int              # derived from date_of_birth
    account_tenure_days: int

Optional intake fields (recommended future `Profile` additions):
    allergies          : list[str]        # e.g. ["fragrance", "essential oils"]
    climate            : str              # e.g. "Riyadh arid", "Jeddah humid"
    sensitivity_level  : "low" | "medium" | "high"
    current_products   : list[str]

Every prompt builder reads whichever fields are present and silently skips the
rest, so Django can ship MVP with just the spec-required fields and enrich
progressively without touching this module.


Expected `product_catalog` item shape
-------------------------------------
    id           : int
    name         : str                    # English name
    name_ar      : str | None             # Arabic name (optional)
    type         : str                    # e.g. "Serum", "Sunscreen"
    ingredients  : str                    # comma-separated
    benefits     : str
    safety       : str                    # e.g. "Pregnancy safe"
    price        : float
    image_url    : str
    product_url  : str
    how_to_use   : str | None             # Optional: exact application instructions
    size         : str | None             # Optional: e.g. "50ml"
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
from datetime import date, datetime
from typing import Any, Literal, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRIMARY_MODEL: str = "gemini-3-flash-preview"
FALLBACK_MODEL: str = "gemini-3.1-flash-lite-preview"

MAX_SLIDING_WINDOW: int = 15  # used in _memory_block for long-term cap
MAX_CHAT_HISTORY_TOKENS: int = 10  # slice applied in chat_assistant before prompt

# Ingredients / actives that must never be recommended during pregnancy.
# The LLM also receives this list in the system prompt; this client-side copy
# is used for defensive post-filtering and for the safe-fallback path.
PREGNANCY_UNSAFE_KEYWORDS: tuple[str, ...] = (
    "retinol",
    "retinal",
    "retinaldehyde",
    "retinoid",
    "retinyl",
    "tretinoin",
    "adapalene",
    "tazarotene",
    "isotretinoin",
    "hydroquinone",
    "salicylic acid",  # >2% unsafe; we block all topical SA to be safe
    "benzoyl peroxide",
    "kojic acid",
    "chemical peel",
    "glycolic acid",  # high-dose AHA - conservative block
    "arbutin",  # conservative: some sources caution during pregnancy
)

EMERGENCY_KEYWORDS_EN: tuple[str, ...] = (
    "burning",
    "burns",
    "stinging",
    "peeling",
    "severe redness",
    "swelling",
    "swollen",
    "rash",
    "blister",
    "allergic reaction",
    "itching badly",
    "hives",
)

EMERGENCY_KEYWORDS_AR: tuple[str, ...] = (
    "حرقة",
    "يحرق",
    "حرق",
    "تقشير شديد",
    "احمرار",
    "تورم",
    "منتفخ",
    "طفح",
    "بثور",
    "حساسية شديدة",
    "حكة شديدة",
)

_ARABIC_BLOCK_RE = re.compile(r"[\u0600-\u06FF]")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class RoutineStep(BaseModel):
    """A single step (AM or PM) of a recommended routine."""

    step: str = Field(description="e.g. Cleanser, Serum, Moisturizer, Sunscreen")
    product_id: int | None = Field(
        default=None,
        description="Catalog product id, or null when no safe product exists.",
    )
    product_name: str = Field(
        description="Product name, or 'None Recommended' (AR: 'لا يوجد توصية')."
    )
    rationale: str = Field(
        description="Explanation in the customer's language (EN or AR)."
    )
    medical_disclaimer: bool = Field(
        description="True when a professional consult is advised."
    )
    image_url: str | None = None
    product_url: str | None = None
    price: float | None = None


class RoutineResponse(BaseModel):
    am_routine: list[RoutineStep]
    pm_routine: list[RoutineStep]


class GlowmiUserProfile(TypedDict, total=False):
    """Documented shape of the user_profile dict. Django builds this."""

    language: Literal["en", "ar"]  # Optional. If provided, overrides auto-detection.
    is_pregnant: bool
    skin_type: str
    concerns: list[str]
    full_name: str
    gender: str
    age: int
    account_tenure_days: int
    allergies: list[str]
    climate: str
    sensitivity_level: Literal["low", "medium", "high"]
    current_products: list[str]
    additional_details: str


# ---------------------------------------------------------------------------
# Lazy client init
# ---------------------------------------------------------------------------

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Instantiate the genai client on first use.

    Supports both `GEMINI_API_KEY` (spec-preferred) and `GIMINIAPI_KEY`
    (already present in the project .env).
    """
    global _client
    if _client is None:
        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GIMINIAPI_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "Gemini API key missing. Set GEMINI_API_KEY in .env."
            )
        _client = genai.Client(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Language routing
# ---------------------------------------------------------------------------


def _resolve_language(
    user_profile: dict[str, Any], user_input: str | None = None
) -> Literal["en", "ar"]:
    """Pick the output language.

    Priority:
      1. Explicit `language` in user_profile ("en" or "ar").
      2. Arabic characters detected in the user's latest input.
      3. Default "en".
    """
    lang = user_profile.get("language")
    if lang in ("en", "ar"):
        return lang

    if user_input and _ARABIC_BLOCK_RE.search(user_input):
        return "ar"

    return "en"


def _derive_age(date_of_birth: date | datetime | str | None) -> int | None:
    """Convert a DOB (date, datetime, or ISO-8601 string) to integer years."""
    if date_of_birth is None:
        return None
    if isinstance(date_of_birth, str):
        try:
            date_of_birth = date.fromisoformat(date_of_birth[:10])
        except ValueError:
            return None
    if isinstance(date_of_birth, datetime):
        date_of_birth = date_of_birth.date()
    today = date.today()
    years = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return max(years, 0)


# ---------------------------------------------------------------------------
# Emergency pre-flight
# ---------------------------------------------------------------------------


def _is_emergency(user_input: str, language: Literal["en", "ar"]) -> bool:
    if not user_input:
        return False
    text = user_input.lower()
    if language == "ar":
        return any(kw in user_input for kw in EMERGENCY_KEYWORDS_AR)
    return any(kw in text for kw in EMERGENCY_KEYWORDS_EN)


def _emergency_response(language: Literal["en", "ar"]) -> str:
    if language == "ar":
        return (
            "نتوقف هنا من أجل سلامتك. يرجى إيقاف استخدام جميع منتجات العناية "
            "بالبشرة فوراً، واغسلي بشرتك بماء فاتر فقط دون أي مطهّر، وتجنّبي "
            "التعرض للشمس. إذا استمر الحرقان أو التقشير أو التورّم لأكثر من "
            "ساعة، أو إذا ازداد سوءاً، يجب عليكِ استشارة طبيب الجلدية فوراً. "
            "صحّتكِ وسلامتكِ أهم بكثير من أي روتين. عائلة Glowmi تهتم بكِ."
        )
    return (
        "Let's pause here for your safety. Please stop using all skincare "
        "products immediately, gently rinse your skin with cool water (no "
        "cleanser), and avoid sun exposure. If the burning, peeling, or "
        "swelling continues for more than an hour or worsens, please consult "
        "a dermatologist right away. Your wellbeing matters far more than "
        "any routine. The Glowmi family is here for you."
    )


# ---------------------------------------------------------------------------
# Prompt builders (pure functions, unit-testable without Gemini)
# ---------------------------------------------------------------------------


def _brand_persona_block(language: Literal["en", "ar"]) -> str:
    if language == "ar":
        return (
            "أنتِ مساعدة Glowmi الذكية للعناية بالبشرة. Glowmi علامة سعودية "
            "فاخرة أسّسها ShahRukh Ali و Noreen Ali.\n"
            "قصة العلامة: «مستوحاة من صمود الصحراء، تؤمن Glowmi بأن البشرة "
            "تملك ذكاءها الخاص — القدرة على التكيّف والحماية والتجدد. تجمع "
            "Glowmi بين علم البشرة المتقدم والترطيب التكيّفي.»\n\n"
            "قواعد النبرة:\n"
            "- صبورة، ذكية، داعمة، راقية.\n"
            "- لستِ بائعة ضغط؛ أنتِ مستشارة موثوقة.\n"
            "- إذا سأل العميل عن منتجات «رخيصة»، أعيدي صياغة القيمة: "
            "«تركّز Glowmi على تركيبات عالية الأداء ومركّزة، مما يجعلها "
            "استثماراً طويل الأمد لبشرتكِ.»\n"
            "- افتراض العالم المغلق: لا توصي أبداً بمنتجات أو علامات ليست "
            "في كتالوج Glowmi. إذا ذكر العميل علامة أخرى (مثل CeraVe)، "
            "اقترحي بلطف أقرب بديل من Glowmi. إذا لم يوجد بديل آمن، اقترحي "
            "روتيناً بسيطاً وموعداً مع طبيب الجلدية."
        )
    return (
        "You are the Glowmi skincare concierge. Glowmi is a premium luxury "
        "skincare brand from Saudi Arabia, founded by ShahRukh Ali and "
        "Noreen Ali.\n"
        "Brand story: \"Inspired by the resilience of the desert, Glowmi "
        "believes skin holds its own intelligence — the ability to adapt, "
        "protect, and renew. Glowmi unites advanced skin science with "
        "adaptive hydration.\"\n\n"
        "Tone rules:\n"
        "- Patient, intelligent, supportive, premium.\n"
        "- You are a trusted advisor, never a pushy salesperson.\n"
        "- If the customer asks for something 'cheap', reframe the value: "
        "\"Glowmi focuses on high-performance, concentrated formulations, "
        "making it a long-term investment in your skin.\"\n"
        "- Closed-world assumption: NEVER recommend products or brands that "
        "are not in the provided Glowmi catalog. If the customer mentions "
        "an outside brand (e.g. CeraVe), gracefully suggest the closest "
        "Glowmi alternative. If no safe Glowmi product exists, suggest a "
        "minimal routine and a dermatologist consult."
    )


def _profile_block(
    user_profile: dict[str, Any], language: Literal["en", "ar"]
) -> str:
    """Render every present profile field. Missing fields are skipped."""
    parts: list[str] = []
    ar = language == "ar"
    header = "## ملف العميل" if ar else "## Customer Profile"
    parts.append(header)

    def add(label_en: str, label_ar: str, value: Any) -> None:
        if value is None or value == "" or value == []:
            return
        label = label_ar if ar else label_en
        parts.append(f"- {label}: {value}")

    add("Name", "الاسم", user_profile.get("full_name"))
    add("Gender", "النوع", user_profile.get("gender"))
    add("Age", "العمر", user_profile.get("age"))
    add("Skin type", "نوع البشرة", user_profile.get("skin_type"))
    add("Concerns", "الاهتمامات", user_profile.get("concerns"))
    add("Pregnant", "حامل", user_profile.get("is_pregnant"))
    add("Allergies", "حساسية من", user_profile.get("allergies"))
    add("Climate", "المناخ", user_profile.get("climate"))
    add(
        "Sensitivity level",
        "مستوى الحساسية",
        user_profile.get("sensitivity_level"),
    )
    add(
        "Currently using",
        "تستخدم حالياً",
        user_profile.get("current_products"),
    )
    add(
        "Account tenure (days)",
        "عضو منذ (أيام)",
        user_profile.get("account_tenure_days"),
    )
    add(
        "Additional details/goals",
        "تفاصيل إضافية / أهداف",
        user_profile.get("additional_details"),
    )

    if ar:
        parts.append(
            "استخدمي هذه المعلومات لتخصيص الردود. إذا كان للعميلة اسم، "
            "حيّيها به باحترام."
        )
    else:
        parts.append(
            "Use this profile to personalize every response. If the customer "
            "has a name, greet them warmly by name."
        )
    return "\n".join(parts)


def _safety_block(
    user_profile: dict[str, Any], language: Literal["en", "ar"]
) -> str:
    parts: list[str] = []
    ar = language == "ar"
    parts.append("## قواعد السلامة" if ar else "## Safety Rules")

    if user_profile.get("is_pregnant"):
        block_list = ", ".join(PREGNANCY_UNSAFE_KEYWORDS)
        if ar:
            parts.append(
                "العميلة حامل. يُحظر تماماً التوصية بأي منتج يحتوي على أيٍّ "
                f"من المكوّنات التالية: {block_list}. إذا لم يتوفر منتج آمن "
                "أثناء الحمل لخطوة مطلوبة، فاضبطي `product_id=null`، "
                "و`product_name='لا يوجد توصية'`، واشرحي السبب باحترام، "
                "واقترحي استشارة طبيبة الجلدية."
            )
        else:
            parts.append(
                "The customer is pregnant. HARD-BLOCK any product containing "
                f"any of: {block_list}. If no pregnancy-safe product exists "
                "for a required step, set `product_id=null`, "
                "`product_name='None Recommended'`, explain why in a warm "
                "tone, and suggest a dermatologist consult."
            )

    allergies = user_profile.get("allergies") or []
    if allergies:
        alist = ", ".join(str(a) for a in allergies)
        if ar:
            parts.append(
                f"العميلة تعاني من حساسية من: {alist}. لا توصي بأي منتج "
                "يحتوي على هذه المكونات؛ اذكري السبب بلطف."
            )
        else:
            parts.append(
                f"The customer is allergic to: {alist}. Never recommend any "
                "product containing these ingredients; mention the reason "
                "gently."
            )

    if not user_profile.get("is_pregnant") and not allergies:
        parts.append(
            "لا توجد قيود سلامة إلزامية لهذه العميلة."
            if ar
            else "No mandatory safety restrictions for this customer."
        )

    parts.append(
        "اذكري دائماً أن هذه توصيات عامة وليست استشارة طبية."
        if ar
        else "Always note that recommendations are general guidance, not "
        "medical advice."
    )
    return "\n".join(parts)


def _catalog_block(
    catalog: list[dict[str, Any]], language: Literal["en", "ar"]
) -> str:
    header = "## كتالوج Glowmi (العالم المغلق)" if language == "ar" else (
        "## Glowmi Catalog (closed-world)"
    )
    body = json.dumps(catalog, ensure_ascii=False, indent=2)
    suffix = (
        "\nلا تخرجي عن هذا الكتالوج. إذا لم يوجد ما يناسب، قولي ذلك بصدق."
        if language == "ar"
        else "\nDo not invent products outside this catalog. If nothing "
        "fits, say so honestly."
    )
    return f"{header}\n{body}{suffix}"


def _memory_block(
    summary_anchor: str | None,
    sliding_window: list[dict[str, str]],
    language: Literal["en", "ar"],
) -> str:
    ar = language == "ar"
    parts: list[str] = []
    if summary_anchor:
        parts.append(
            "## الذاكرة طويلة الأمد" if ar else "## Long-term summary"
        )
        parts.append(summary_anchor)

    # sliding_window is already pre-sliced by the caller (last 10 messages)
    recent = sliding_window[-MAX_SLIDING_WINDOW:] if sliding_window else []
    if recent:
        parts.append("## الرسائل الأخيرة" if ar else "## Recent messages")
        for turn in recent:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            label = "العميلة" if (ar and role == "user") else (
                "المساعدة" if ar else role.capitalize()
            )
            parts.append(f"{label}: {content}")

    if parts:
        parts.append(
            "قاعدة التعارض: إذا تعارضت الرسائل الأخيرة مع الملف الثابت، "
            "اعتمدي على أحدث معلومة من العميلة."
            if ar
            else "Conflict rule: if recent chat or live intake data conflicts "
            "with the static user_profile, prioritize the most recent input."
        )
    return "\n".join(parts)


def _someone_else_block(language: Literal["en", "ar"]) -> str:
    """Inject the 'Someone Else' exception and is_for_friend JSON flag rules."""
    if language == "ar":
        return (
            "## استثناء 'لشخص آخر'\n"
            "إذا طلبت العميلة نصيحة عناية بالبشرة لصديقة أو أحد أفراد الأسرة، "
            "اطلبي تفاصيل ذلك الشخص تحديداً (نوع بشرته، مخاوفه، عمره، إلخ). "
            "لا تبني توصياتك على ملف العميلة الأصلي. "
            "عندما يخص الحوار الحالي شخصاً آخر وليس العميلة نفسها، يجب أن يحتوي "
            'ردّكِ على الحقل: \'is_for_friend\': true. '
            "وإذا كان الحوار للعميلة نفسها، اضبطي "
            '\'is_for_friend\': false.'
        )
    return (
        "## 'Someone Else' Exception\n"
        "If the user is asking for skincare advice for a friend or family "
        "member, ask for that person's specific details (skin type, concerns, "
        "age, etc.). Do NOT base the friend's advice on the main user's "
        "user_profile. When the current conversation is about someone other "
        "than the main user, your response JSON MUST include "
        "'is_for_friend': true. When it is about the main user, set "
        "'is_for_friend': false."
    )


def _build_system_instruction(
    user_profile: dict[str, Any],
    catalog: list[dict[str, Any]],
    language: Literal["en", "ar"],
    include_memory: bool = False,
    summary_anchor: str | None = None,
    sliding_window: list[dict[str, str]] | None = None,
    include_friend_exception: bool = False,
) -> str:
    blocks = [
        _brand_persona_block(language),
        _profile_block(user_profile, language),
        _safety_block(user_profile, language),
        _catalog_block(catalog, language),
    ]
    if include_memory:
        mem = _memory_block(summary_anchor, sliding_window or [], language)
        if mem:
            blocks.append(mem)
    if include_friend_exception:
        blocks.append(_someone_else_block(language))
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Gemini wrapper with fallback
# ---------------------------------------------------------------------------


async def _call_with_fallback(
    *,
    system_instruction: str,
    contents: str | list[Any],
    response_schema: type[BaseModel] | None = None,
    temperature: float = 0.7,
) -> genai_types.GenerateContentResponse | None:
    """Try PRIMARY_MODEL, fall back to FALLBACK_MODEL, return None on total failure."""
    client = _get_client()

    config_kwargs: dict[str, Any] = {
        "system_instruction": system_instruction,
        "temperature": temperature,
    }
    if response_schema is not None:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema

    config = genai_types.GenerateContentConfig(**config_kwargs)

    for model_id in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            response = await client.aio.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )
            return response
        except genai_errors.APIError as exc:
            print(f"[ai_engine] {model_id} APIError: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            print(f"[ai_engine] {model_id} unexpected error: {exc!r}")
            continue
    return None


# ---------------------------------------------------------------------------
# Safe fallbacks
# ---------------------------------------------------------------------------


def _safe_routine_fallback(language: Literal["en", "ar"]) -> dict[str, Any]:
    if language == "ar":
        rationale = (
            "نعتذر، لم نتمكن من إنشاء روتين مخصّص الآن. نوصي بروتين بسيط: "
            "منظّف لطيف ومرطب وواقٍ من الشمس، مع استشارة طبيب الجلدية."
        )
        none_name = "لا يوجد توصية"
    else:
        rationale = (
            "We couldn't build a personalized routine right now. Please try "
            "a minimal routine (gentle cleanser, moisturizer, sunscreen) and "
            "consult a dermatologist."
        )
        none_name = "None Recommended"

    def step(name: str) -> dict[str, Any]:
        return {
            "step": name,
            "product_id": None,
            "product_name": none_name,
            "rationale": rationale,
            "medical_disclaimer": True,
            "image_url": None,
            "product_url": None,
            "price": None,
        }

    return {
        "am_routine": [step("Cleanser"), step("Moisturizer"), step("Sunscreen")],
        "pm_routine": [step("Cleanser"), step("Moisturizer")],
    }


def _safe_chat_fallback(
    language: Literal["en", "ar"],
    old_anchor: str = "",
) -> dict[str, Any]:
    """Return the safe fallback dict when Gemini is unavailable."""
    if language == "ar":
        message = (
            "نعتذر، نواجه حالياً ضغطاً عالياً. يمكنكِ إعادة المحاولة بعد "
            "لحظات، ونحن هنا لمساعدتكِ متى شئتِ. عائلة Glowmi."
        )
    else:
        message = (
            "We are experiencing high traffic at the moment. Please try again "
            "in a moment; we're here whenever you're ready. — The Glowmi family."
        )
    return {
        "response": message,
        "updated_summary_anchor": old_anchor,
        "is_for_friend": False,
    }


# ---------------------------------------------------------------------------
# Base64 Image Helper
# ---------------------------------------------------------------------------


def _decode_base64_image(b64_str: str) -> genai_types.Part | None:
    if not b64_str:
        return None
    try:
        # Strip data URL scheme if present (e.g., "data:image/jpeg;base64,...")
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        image_bytes = base64.b64decode(b64_str)
        return genai_types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    except Exception as exc:
        print(f"[ai_engine] base64 decode error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_routine(
    user_profile: dict[str, Any],
    product_catalog: list[dict[str, Any]],
    user_image_b64: str | None = None,
) -> dict[str, Any]:
    """Generate a personalized AM/PM skincare routine.

    Returns a dict matching `RoutineResponse.model_dump()`. Never raises.
    """
    language: Literal["en", "ar"] = _resolve_language(user_profile)

    if "age" not in user_profile and "date_of_birth" in user_profile:
        derived = _derive_age(user_profile["date_of_birth"])
        if derived is not None:
            user_profile = {**user_profile, "age": derived}

    system_instruction = _build_system_instruction(
        user_profile=user_profile,
        catalog=product_catalog,
        language=language,
    )

    if language == "ar":
        user_task = (
            "ابني روتيناً صباحياً ومسائياً مخصّصاً لهذه العميلة باستخدام "
            "المنتجات من كتالوج Glowmi فقط. أعيدي النتيجة ككائن JSON بنفس "
            "المخطط المطلوب، واكتبي جميع التفسيرات باللغة العربية الراقية. "
            "التزمي بجميع قيود السلامة."
        )
    else:
        user_task = (
            "Build a personalized AM and PM routine for this customer using "
            "ONLY products from the Glowmi catalog. Return a JSON object "
            "matching the required schema. Write all rationales in English. "
            "Respect every safety rule."
        )

    contents: list[Any] = [user_task]
    if user_image_b64:
        image_part = _decode_base64_image(user_image_b64)
        if image_part:
            contents.insert(0, image_part)
            if language == "ar":
                contents.append("الرجاء تحليل الصورة المرفقة لبشرة العميلة وأخذها في الاعتبار عند بناء الروتين.")
            else:
                contents.append("Please analyze the attached photo of the customer's skin and take it into account when building the routine.")

    response = await _call_with_fallback(
        system_instruction=system_instruction,
        contents=contents,
        response_schema=RoutineResponse,
        temperature=0.4,
    )

    if response is None:
        return _safe_routine_fallback(language)

    parsed: RoutineResponse | None = None
    try:
        if getattr(response, "parsed", None) is not None:
            parsed = response.parsed  # SDK already validated against schema
        else:
            raw = response.text or ""
            parsed = RoutineResponse.model_validate_json(raw)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ai_engine] routine parse error: {exc}")
        return _safe_routine_fallback(language)

    if not isinstance(parsed, RoutineResponse):
        try:
            parsed = RoutineResponse.model_validate(parsed)
        except (ValidationError, TypeError) as exc:
            print(f"[ai_engine] routine coerce error: {exc}")
            return _safe_routine_fallback(language)

    return _post_filter_routine(parsed, user_profile, product_catalog, language)


def _post_filter_routine(
    routine: RoutineResponse,
    user_profile: dict[str, Any],
    catalog: list[dict[str, Any]],
    language: Literal["en", "ar"],
) -> dict[str, Any]:
    """Defensive: if the LLM slipped a pregnancy-unsafe product through,
    overwrite that step with a safe 'None Recommended' placeholder. Also
    hydrate image_url/product_url/price from the catalog in case the model
    omitted them.
    """
    catalog_by_id: dict[int, dict[str, Any]] = {
        int(p["id"]): p for p in catalog if "id" in p
    }
    is_pregnant = bool(user_profile.get("is_pregnant"))
    allergies_lower = [
        str(a).lower() for a in (user_profile.get("allergies") or [])
    ]

    none_name = "لا يوجد توصية" if language == "ar" else "None Recommended"

    def ingredients_of(pid: int | None) -> str:
        if pid is None:
            return ""
        prod = catalog_by_id.get(int(pid))
        return str(prod.get("ingredients", "")).lower() if prod else ""

    def is_unsafe(pid: int | None) -> tuple[bool, str]:
        ing = ingredients_of(pid)
        if not ing:
            return False, ""
        if is_pregnant:
            for kw in PREGNANCY_UNSAFE_KEYWORDS:
                if kw in ing:
                    return True, kw
        for a in allergies_lower:
            if a and a in ing:
                return True, a
        return False, ""

    def hydrate(step: RoutineStep) -> dict[str, Any]:
        data = step.model_dump()
        unsafe, reason = is_unsafe(step.product_id)
        if unsafe:
            if language == "ar":
                reason_text = (
                    f"تم استبعاد المنتج لاحتوائه على {reason}، وهو غير مناسب "
                    "في هذه المرحلة. ننصح باستشارة طبيبة الجلدية."
                )
            else:
                reason_text = (
                    f"This product was removed because it contains "
                    f"'{reason}', which is not suitable for you right now. "
                    "Please consult a dermatologist."
                )
            data.update(
                {
                    "product_id": None,
                    "product_name": none_name,
                    "rationale": reason_text,
                    "medical_disclaimer": True,
                    "image_url": None,
                    "product_url": None,
                    "price": None,
                }
            )
            return data

        if step.product_id is not None:
            prod = catalog_by_id.get(int(step.product_id))
            if prod:
                data["image_url"] = data.get("image_url") or prod.get("image_url")
                data["product_url"] = data.get("product_url") or prod.get(
                    "product_url"
                )
                if data.get("price") is None and prod.get("price") is not None:
                    try:
                        data["price"] = float(prod["price"])
                    except (TypeError, ValueError):
                        pass
        return data

    return {
        "am_routine": [hydrate(s) for s in routine.am_routine],
        "pm_routine": [hydrate(s) for s in routine.pm_routine],
    }


class _ChatResponse(BaseModel):
    """Structured envelope returned by the chat assistant Gemini call."""

    response: str = Field(description="The assistant's reply to the user.")
    is_for_friend: bool = Field(
        default=False,
        description=(
            "True when the current conversation is about skincare advice for "
            "a friend or family member, not the registered user."
        ),
    )


async def chat_assistant(
    user_input: str,
    chat_history: list[dict],
    summary_anchor: str,
    user_profile: dict[str, Any],
    product_catalog: list[dict[str, Any]],
    user_image_b64: str | None = None,
) -> dict[str, Any]:
    """Conversational concierge with layered memory.

    Parameters
    ----------
    user_input:
        The user's latest message.
    chat_history:
        Full conversation history as a list of dicts
        ``[{"role": "user"|"assistant", "content": "..."}]``.
        Internally sliced to the last ``MAX_CHAT_HISTORY_TOKENS`` messages
        before being passed to Gemini to save tokens.
    summary_anchor:
        Rolling compressed memory string from previous sessions.
    user_profile:
        Standard Python dict built by the Django layer.
    product_catalog:
        List of product dicts from the Django layer.
    user_image_b64:
        Optional base-64 encoded image of the user's skin.

    Returns
    -------
    dict with keys:
        ``response``              – the assistant's reply (str)
        ``updated_summary_anchor`` – new compressed memory string (str)
        ``is_for_friend``         – True when advice is for a 3rd party (bool)

    Never raises — falls back gracefully on any Gemini error.
    """
    language: Literal["en", "ar"] = _resolve_language(user_profile, user_input)

    # Emergency pre-flight — return structured dict even for emergencies
    if _is_emergency(user_input, language):
        return {
            "response": _emergency_response(language),
            "updated_summary_anchor": summary_anchor,
            "is_for_friend": False,
        }

    if "age" not in user_profile and "date_of_birth" in user_profile:
        derived = _derive_age(user_profile["date_of_birth"])
        if derived is not None:
            user_profile = {**user_profile, "age": derived}

    # --- Slice chat history to last MAX_CHAT_HISTORY_TOKENS messages ---
    windowed_history: list[dict] = (
        chat_history[-MAX_CHAT_HISTORY_TOKENS:] if chat_history else []
    )

    system_instruction = _build_system_instruction(
        user_profile=user_profile,
        catalog=product_catalog,
        language=language,
        include_memory=True,
        summary_anchor=summary_anchor,
        sliding_window=windowed_history,
        include_friend_exception=True,
    )

    # Instruct the model to always return structured JSON
    if language == "ar":
        prefix = (
            "رسالة العميلة الحالية: "
        )
        json_instruction = (
            "\n\nيجب أن يكون ردّكِ دائماً كائن JSON بالتنسيق التالي:\n"
            '{"response": "<ردّكِ الكامل هنا>", "is_for_friend": <true|false>}'
        )
    else:
        prefix = "Customer's current message: "
        json_instruction = (
            "\n\nYou MUST always reply with a JSON object in this exact format:\n"
            '{"response": "<your full reply here>", "is_for_friend": <true|false>}'
        )

    contents: list[Any] = [prefix + user_input + json_instruction]
    if user_image_b64:
        image_part = _decode_base64_image(user_image_b64)
        if image_part:
            contents.insert(0, image_part)

    response = await _call_with_fallback(
        system_instruction=system_instruction,
        contents=contents,
        response_schema=_ChatResponse,
        temperature=0.7,
    )

    if response is None:
        return _safe_chat_fallback(language, old_anchor=summary_anchor)

    # --- Parse structured response ---
    chat_parsed: _ChatResponse | None = None
    try:
        if getattr(response, "parsed", None) is not None:
            chat_parsed = response.parsed
        else:
            raw = (response.text or "").strip()
            chat_parsed = _ChatResponse.model_validate_json(raw)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ai_engine] chat parse error: {exc}")
        # Attempt graceful recovery: treat raw text as the reply
        raw_text = ""
        try:
            raw_text = (response.text or "").strip()
        except Exception:  # noqa: BLE001
            pass
        return {
            "response": raw_text or _safe_chat_fallback(language, summary_anchor)["response"],
            "updated_summary_anchor": summary_anchor,
            "is_for_friend": False,
        }

    is_for_friend: bool = bool(getattr(chat_parsed, "is_for_friend", False))
    reply_text: str = (getattr(chat_parsed, "response", "") or "").strip()

    if not reply_text:
        return _safe_chat_fallback(language, old_anchor=summary_anchor)

    # --- Summary anchor update (background) ---
    # If is_for_friend, do NOT pollute the main user's memory with friend data.
    if is_for_friend:
        updated_anchor = summary_anchor
    else:
        # Fire-and-return: generate the updated anchor from the new exchange
        new_exchange = windowed_history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": reply_text},
        ]
        updated_anchor = await update_summary_anchor(
            old_anchor=summary_anchor,
            new_messages=new_exchange,
            language=language,
        )

    return {
        "response": reply_text,
        "updated_summary_anchor": updated_anchor,
        "is_for_friend": is_for_friend,
    }


async def update_summary_anchor(
    old_anchor: str,
    new_messages: list[dict[str, str]],
    language: Literal["en", "ar"] = "en",
) -> str:
    """Compress (old_anchor + new_messages) into an updated rolling summary.

    Called by Django when `len(sliding_window) > MAX_SLIDING_WINDOW`.
    Preserves: stated concerns, allergies, pregnancy status, past
    recommendations, tone preferences. Falls back to `old_anchor` on any
    failure — the app never loses state.
    """
    if not new_messages:
        return old_anchor or ""

    transcript_parts: list[str] = []
    for turn in new_messages:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        transcript_parts.append(f"{role}: {content}")
    transcript = "\n".join(transcript_parts)

    if language == "ar":
        system_instruction = (
            "أنتِ مُلخِّصة ذاكرة لمساعدة Glowmi. مهمتكِ دمج الملخص القديم مع "
            "الرسائل الجديدة في ملخص موجز (≤ 400 كلمة) يحتفظ بـ: الاهتمامات "
            "المذكورة، الحساسيات، حالة الحمل، التوصيات السابقة، وتفضيلات "
            "النبرة. اكتبي الملخص بالعربية الراقية فقط."
        )
        user_text = (
            f"الملخص القديم:\n{old_anchor or '(لا يوجد)'}\n\n"
            f"الرسائل الجديدة:\n{transcript}\n\n"
            "أنتجي الملخص المحدّث."
        )
    else:
        system_instruction = (
            "You are a memory summarizer for the Glowmi assistant. Merge "
            "the old anchor with the new messages into a concise running "
            "summary (≤ 400 words) preserving: stated concerns, allergies, "
            "pregnancy status, past recommendations, and tone preferences. "
            "Respond with the summary only — no preamble."
        )
        user_text = (
            f"Old anchor:\n{old_anchor or '(none)'}\n\n"
            f"New messages:\n{transcript}\n\n"
            "Produce the updated anchor."
        )

    client = _get_client()
    config = genai_types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2,
    )
    try:
        response = await client.aio.models.generate_content(
            model=FALLBACK_MODEL,
            contents=user_text,
            config=config,
        )
        text = (response.text or "").strip()
        return text or (old_anchor or "")
    except genai_errors.APIError as exc:
        print(f"[ai_engine] summary APIError: {exc}")
        return old_anchor or ""
    except Exception as exc:  # noqa: BLE001
        print(f"[ai_engine] summary unexpected error: {exc!r}")
        return old_anchor or ""


# ---------------------------------------------------------------------------
# End of Module
# ---------------------------------------------------------------------------
