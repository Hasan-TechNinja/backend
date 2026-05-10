import asyncio
import json
import logging
import os
import re
from collections.abc import AsyncGenerator
from typing import Any

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from PIL import Image
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configuration - Updated based on the user's specific experimental model list
PRIMARY_MODEL = "gemini-3-flash-preview"
LITE_MODEL = "gemini-3.1-flash-lite"
# These models were verified as 'Available' via scratch/list_models.py
MODELS_TO_TRY = [
    "gemini-3-flash-preview", 
    "gemini-3.1-flash-lite", 
    "gemini-2.5-flash", 
    "gemini-2.0-flash",
    "gemini-flash-latest"
]

# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types

# Initialize SDK client (requires GEMINI_API_KEY in env)
client = genai.Client(api_key=os.getenv("GIMINIAPI_KEY"))

# ---------------------------------------------------------------------------
# 1. Mock Product Catalog
# ---------------------------------------------------------------------------
PRODUCT_CATALOG = [
    {
        "id": 1,
        "title": "Glowmi Elara Regenerative Barrier Serum",
        "sub_title": "Adaptive Barrier Repair & Deep Hydration",
        "price": 89.00,
        "size_ml": 30,
        "discount_percent": 0,
        "category": "Serum",
        "stock": 120,
        "key_ingredients": ["Ceramide Complex", "Hyaluronic Acid", "Squalane", "Niacinamide"],
        "target_skin_type": ["Oily", "Dry", "Combination", "Normal", "Sensitive"],
        "key_benefits": "Barrier strengthening, deep hydration, soothes redness",
        "description": "Inspired by desert flora's water retention, Elara strengthens the skin barrier while delivering multi-depth hydration. Perfect for recovering from harsh GCC climates.",
        "how_to_use": "Apply 2-3 drops to clean, damp skin morning and night. Pat gently until absorbed.",
        "image_url": "https://placehold.co/400x400/1a1a2e/ffffff?text=Elara+Serum"
    },
    {
        "id": 2,
        "title": "Glowmi Desert Bloom Gentle Cleansing Gel",
        "sub_title": "Purifying & Non-Stripping Wash",
        "price": 38.00,
        "size_ml": 150,
        "discount_percent": 0,
        "category": "Cleanser",
        "stock": 250,
        "key_ingredients": ["Desert Rose Extract", "Glycerin", "Panthenol"],
        "target_skin_type": ["Oily", "Dry", "Combination", "Normal", "Sensitive"],
        "key_benefits": "Gently removes impurities without stripping moisture.",
        "description": "A pH-balanced gel cleanser that washes away the day's dust and pollutants while keeping the skin's moisture barrier intact.",
        "how_to_use": "Massage gently onto damp skin for 30 seconds, then rinse with lukewarm water.",
        "image_url": "https://placehold.co/400x400/1a1a2e/ffffff?text=Desert+Bloom+Cleanser"
    },
    {
        "id": 3,
        "title": "Glowmi Solar Veil SPF 50 Mineral Sunscreen",
        "sub_title": "Invisible Broad-Spectrum Protection",
        "price": 45.00,
        "size_ml": 50,
        "discount_percent": 0,
        "category": "Sunscreen",
        "stock": 300,
        "key_ingredients": ["Zinc Oxide", "Titanium Dioxide", "Antioxidant Complex"],
        "target_skin_type": ["Oily", "Dry", "Combination", "Normal", "Sensitive"],
        "key_benefits": "UVA/UVB protection, zero white cast, pollution defense",
        "description": "Essential defense against the intense GCC sun. This lightweight mineral formula protects without clogging pores or leaving a white cast.",
        "how_to_use": "Apply generously as the final step in your morning routine. Reapply every 2 hours if outdoors.",
        "image_url": "https://placehold.co/400x400/1a1a2e/ffffff?text=Solar+Veil+SPF+50"
    },
    {
        "id": 4,
        "title": "Glowmi Celestial Glow Brightening Serum",
        "sub_title": "Illuminate & Firm",
        "price": 98.00,
        "size_ml": 50,
        "discount_percent": 0,
        "category": "Serum",
        "stock": 80,
        "key_ingredients": ["Vitamin C", "Tranexamic Acid", "Licorice Root"],
        "target_skin_type": ["Oily", "Dry", "Combination", "Normal", "Sensitive"],
        "key_benefits": "Fades dark spots, evens skin tone, provides antioxidant protection",
        "description": "A potent brightening serum that targets hyperpigmentation and dullness, revealing a luminous, even complexion.",
        "how_to_use": "Apply 1-2 pumps to clean skin every morning. Follow with moisturizer and sunscreen.",
        "image_url": "https://placehold.co/400x400/1a1a2e/ffffff?text=Celestial+Glow+Serum"
    },
    {
        "id": 5,
        "title": "Glowmi Lunar Restore Overnight Sleeping Mask",
        "sub_title": "Renew & Plump While You Sleep",
        "price": 78.00,
        "size_ml": 50,
        "discount_percent": 0,
        "category": "Sleeping Mask",
        "stock": 150,
        "key_ingredients": ["Peptides", "Centella Asiatica", "Squalane"],
        "target_skin_type": ["Dry", "Normal", "Combination"],
        "key_benefits": "Intense overnight hydration, skin repair, plumping",
        "description": "Works with your skin's natural nighttime repair process to deliver intense hydration and visibly plump the skin by morning.",
        "how_to_use": "Apply a generous layer as the final step of your evening routine 2-3 times a week. Leave on overnight.",
        "image_url": "https://placehold.co/400x400/1a1a2e/ffffff?text=Lunar+Restore+Mask"
    },
    {
        "id": 6,
        "title": "Glowmi Hydra Dew Lightweight Moisturizer",
        "sub_title": "Weightless Hydration for Hot Climates",
        "price": 52.00,
        "size_ml": 50,
        "discount_percent": 0,
        "category": "Moisturizer",
        "stock": 200,
        "key_ingredients": ["Aloe Water", "Green Tea Extract", "Hyaluronic Acid"],
        "target_skin_type": ["Oily", "Combination"],
        "key_benefits": "Oil control, lightweight hydration, cooling effect",
        "description": "A refreshing gel-cream that provides essential moisture without the heavy, greasy feel—ideal for oily skin in hot, humid weather.",
        "how_to_use": "Apply a dime-sized amount to face and neck morning and night.",
        "image_url": "https://placehold.co/400x400/1a1a2e/ffffff?text=Hydra+Dew+Moisturizer"
    }
]

# ---------------------------------------------------------------------------
# 2. Safety Constants & Rules
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

# ---------------------------------------------------------------------------
# 3. Pydantic Schemas for Structured Outputs
# ---------------------------------------------------------------------------
class RoutineStep(BaseModel):
    product_id: int = Field(description="The ID of the recommended product from the catalog.")
    step_number: int = Field(description="The order of this step (e.g., 1, 2, 3).")
    usage_instructions: str = Field(description="Specific instructions on how and when to use.")

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
# 4. Helper Functions
# ---------------------------------------------------------------------------
def _resolve_language(text: str) -> str:
    """Detects primary language based on Arabic characters."""
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    if arabic_chars > len(text) * 0.1:  # Natively handles mixed text if mostly Arabic
        return "ar"
    return "en"

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

def _get_product_by_id(product_id: int) -> dict | None:
    for p in PRODUCT_CATALOG:
        if p["id"] == product_id:
            return p
    return None

def _build_sliding_window(chat_history: list, window_size: int = 10) -> list:
    return chat_history[-window_size:] if len(chat_history) > window_size else chat_history

def _build_system_prompt(
    user_profile: dict,
    summary_anchor: str,
    is_pregnant: bool,
    is_for_friend: bool,
    detected_language: str,
) -> str:
    base_prompt = f"""You are the Glowmi AI Skincare Concierge.
Brand Identity: Glowmi unites advanced skin science with adaptive hydration, inspired by the resilience of the desert.
Tone: Intelligent, warm, premium, trust-building. Never pushy, never overly medical.

Anti-Templating Rules:
1. DO refer to the user by their full name occasionally to build a personal connection (use the Registration Data), but do NOT say hello in every single message.
2. Do NOT append medical disclaimers unless dealing with a specific severe condition.

Core Logic:
- Intake Profile (Routine Context): Skin Type: {user_profile.get('skin_type')}, Age: {user_profile.get('age')}, Concerns: {', '.join(user_profile.get('concerns', []))}
- Registration Data (Chat Context): {user_profile.get('signup_data', 'Not provided')}
- Live Skin State: Pay attention to temporary states mentioned in chat (e.g., dehydrated, inflamed). The temporary state OVERRIDES the static skin type for current recommendations.
- GCC Climate: Autonomously factor in Saudi Arabian climate (extreme heat, dry weather, heavy AC, dust) when explaining.

Output Flow:
(A) Acknowledge concern -> (B) Explain reason using GCC context -> (C) Recommend skincare approach -> (D) Recommend Glowmi Product -> (E) Add gentle caution if needed.

If the user EXPLICITLY asks for a complete, step-by-step skincare routine, do NOT write out the routine in markdown. Instead, just acknowledge their request and include this exact marker at the end of your response: [[GENERATE_ROUTINE]]
Our system will intercept this marker and automatically generate a structured visual routine for them.

Closed-World Rule: You MUST ONLY recommend products from the Glowmi Catalog provided below. Do not recommend Cerave, Paula's Choice, or any other brands.

Product Catalog:
{json.dumps(PRODUCT_CATALOG, indent=2)}

Recommendation Format:
When you recommend a product from the catalog, you MUST embed a marker exactly like this in your text: [[PRODUCT:id]] (where id is the integer ID of the product).
Example: "I highly recommend the [[PRODUCT:1]] to help with..."
Do not add any other markdown around the marker. The system will convert this marker into a beautiful UI card.

Long-term Memory Anchor:
{summary_anchor}
"""

    if is_pregnant:
        base_prompt += "\nCRITICAL SAFETY: The user is PREGNANT or NURSING. You MUST NOT recommend any products containing Retinol, BHA/Salicylic Acid, Benzoyl Peroxide, or Hydroquinone. Check the key_ingredients of products before recommending."

    if is_for_friend:
        base_prompt += "\nNOTICE: The user is currently asking for advice for SOMEONE ELSE. Do NOT use the user's static profile data for this response."

    lang_instruction = "Respond entirely in Arabic." if detected_language == "ar" else "Respond entirely in English."
    base_prompt += f"\n\nLanguage Instruction: {lang_instruction}"
    
    return base_prompt

# ---------------------------------------------------------------------------
# 5. Core Engine Functions
# ---------------------------------------------------------------------------

async def stream_chat_assistant(
    user_profile: dict,
    chat_history: list,
    current_prompt: str,
    summary_anchor: str = "",
    image: Image.Image | None = None,
) -> AsyncGenerator[str | ChatMetadata, None]:
    """
    Streams markdown responses and yields a final ChatMetadata object.
    """
    detected_lang = _resolve_language(current_prompt)
    is_pregnant = _detect_pregnancy_context(current_prompt, chat_history, summary_anchor)
    is_for_friend = _detect_friend_context(current_prompt)
    is_emergency = _detect_medical_emergency(current_prompt)

    if is_emergency:
        msg = (
            "I'm sorry to hear you're experiencing severe symptoms. Please wash your face with cool water immediately, stop using active products, and consult a dermatologist. I cannot provide medical advice for severe reactions."
            if detected_lang == "en" else
            "يؤسفني سماع أنك تعاني من هذه الأعراض. يرجى غسل وجهك بالماء البارد فوراً، والتوقف عن استخدام المنتجات النشطة، واستشارة طبيب جلدية. لا يمكنني تقديم نصيحة طبية للحالات الشديدة."
        )
        yield msg
        yield ChatMetadata(
            product_references=[],
            is_for_friend=is_for_friend,
            full_response=msg,
            detected_language=detected_lang
        )
        return

    system_instruction = _build_system_prompt(
        user_profile, summary_anchor, is_pregnant, is_for_friend, detected_lang
    )

    contents = []
    window = _build_sliding_window(chat_history, 10)
    for msg in window:
        role = "user" if msg["role"] == "user" else "model"
        
        msg_parts = []
        if "image" in msg and msg["image"]:
            import io
            img_byte_arr = io.BytesIO()
            fmt = msg["image"].format if msg["image"].format else 'PNG'
            msg["image"].save(img_byte_arr, format=fmt)
            msg_parts.append(types.Part.from_bytes(data=img_byte_arr.getvalue(), mime_type=f"image/{fmt.lower()}"))
            
        msg_parts.append(types.Part.from_text(text=msg["content"]))
        contents.append(types.Content(role=role, parts=msg_parts))

    # Add current prompt and optional image
    parts = []
    if image:
        import io
        img_byte_arr = io.BytesIO()
        fmt = image.format if image.format else 'PNG'
        image.save(img_byte_arr, format=fmt)
        parts.append(types.Part.from_bytes(data=img_byte_arr.getvalue(), mime_type=f"image/{fmt.lower()}"))
    parts.append(types.Part.from_text(text=current_prompt))
    
    contents.append(types.Content(role="user", parts=parts))

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7,
    )

    full_text = ""
    last_exception = None
    for model_id in MODELS_TO_TRY:
        try:
            response_stream = client.models.generate_content_stream(
                model=model_id,
                contents=contents,
                config=config,
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    full_text += chunk.text
            # If successful, break the retry loop
            break
        except Exception as e:
            last_exception = e
            logging.warning(f"Stream failed with {model_id}: {e}")
            continue
    else:
        error_msg = f"\n\n[Error communicating with AI: {str(last_exception)}]"
        yield error_msg
        full_text += error_msg

    # Post-process the full text to extract markers
    product_refs = []
    marker_pattern = r'\[\[PRODUCT:(\d+)\]\]'
    
    for match in re.finditer(marker_pattern, full_text):
        try:
            pid = int(match.group(1))
            if not any(r.product_id == pid for r in product_refs):
                product_refs.append(ProductReference(product_id=pid, context="Mentioned in chat"))
        except ValueError:
            pass

    # Clean the text
    def replace_marker(match):
        pid = int(match.group(1))
        prod = _get_product_by_id(pid)
        return f"**{prod['title']}**" if prod else ""
        
    clean_text = re.sub(marker_pattern, replace_marker, full_text).replace('  ', ' ')
    
    triggers_routine = False
    if "[[GENERATE_ROUTINE]]" in clean_text:
        triggers_routine = True
        clean_text = clean_text.replace("[[GENERATE_ROUTINE]]", "").strip()

    yield ChatMetadata(
        product_references=product_refs,
        is_for_friend=is_for_friend,
        full_response=clean_text,
        detected_language=detected_lang,
        triggers_routine=triggers_routine
    )


def _post_filter_routine(routine_data: RoutineSchema, summary_anchor: str) -> RoutineSchema:
    is_pregnant = _detect_context_keywords(summary_anchor, PREGNANCY_KEYWORDS_EN + PREGNANCY_KEYWORDS_AR)
    if not is_pregnant:
        return routine_data

    def filter_steps(steps: list[RoutineStep]):
        for step in steps:
            prod = _get_product_by_id(step.product_id)
            if prod:
                ingredients_text = " ".join(prod.get("key_ingredients", [])).lower()
                if any(bad_ing in ingredients_text for bad_ing in PREGNANCY_UNSAFE_INGREDIENTS):
                    logging.warning(f"[SAFETY FILTER] Removed product {step.product_id} due to pregnancy unsafe ingredients.")
                    step.product_id = -1 # Or handle appropriately in UI
        return [s for s in steps if s.product_id != -1]

    routine_data.morning_routine = filter_steps(routine_data.morning_routine)
    routine_data.evening_routine = filter_steps(routine_data.evening_routine)
    return routine_data


async def generate_routine(user_profile: dict, chat_history: list, summary_anchor: str = "", image: Image.Image | None = None) -> RoutineSchema | None:
    system_instruction = _build_system_prompt(
        user_profile, summary_anchor, 
        _detect_context_keywords(summary_anchor, PREGNANCY_KEYWORDS_EN + PREGNANCY_KEYWORDS_AR), 
        False, "en"
    )

    prompt_content = ["Based on my profile, current skin state from our chat, and the GCC climate, please generate my perfect Glowmi skincare routine."]
    if image:
        import io
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format or 'PNG')
        img_bytes = img_byte_arr.getvalue()
        mime_type = f"image/{image.format.lower()}" if image.format else "image/png"
        prompt_content.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.4,
        response_mime_type="application/json",
        response_schema=RoutineSchema,
    )

    for model_id in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt_content,
                config=config,
            )
            if response.text:
                data = json.loads(response.text)
                routine = RoutineSchema(**data)
                return _post_filter_routine(routine, summary_anchor)
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
- Long-term traits and detected sensitivities.
- Pregnancy status (if mentioned).
- Recent skin states.
- DO NOT include details specifically asked for a friend (flagged in context).

Current Anchor: {current_anchor}
User Profile Base: {json.dumps({k: v for k, v in user_profile.items() if k != 'photo'})}

Recent Conversation:
"""
    for msg in _build_sliding_window(chat_history, 5):
        prompt += f"{msg['role']}: {msg['content']}\n"

    try:
        response = client.models.generate_content(
            model=LITE_MODEL,
            contents=prompt
        )
        return response.text or current_anchor
    except Exception as e:
        logging.error(f"Error updating anchor: {e}")
        return current_anchor


async def generate_suggestions(user_profile: dict, chat_history: list, summary_anchor: str = "") -> list[str]:
    prompt = f"""
Based on the user's profile and recent chat, generate 3-4 short, contextual follow-up questions the user might want to ask next.
Return ONLY a JSON list of strings.
Profile: {json.dumps({k: v for k, v in user_profile.items() if k != 'photo'})}
"""
    config = types.GenerateContentConfig(
        temperature=0.7,
        response_mime_type="application/json",
        response_schema=list[str],
    )
    try:
        response = client.models.generate_content(
            model=LITE_MODEL,
            contents=prompt,
            config=config
        )
        if response.text:
            return json.loads(response.text)
    except Exception as e:
        logging.error(f"Error generating suggestions: {e}")
    return ["How do I build a routine?", "What are the benefits of Vitamin C?", "Sunscreen recommendations"]
