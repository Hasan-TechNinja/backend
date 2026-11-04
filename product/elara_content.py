"""Launch content for ELARA, taken from the original static product page."""

CATEGORY_NAME = "Serums"

PRODUCT = {
    "title": "ELARA",
    "sub_title": "Regenerative Barrier Serum",
    "price": "345.00",
    "size": "30 ml",
    "discount": "0.00",
    "description": (
        "Designed for skin shaped by modern life. ELARA Regenerative Barrier Serum delivers "
        "8 bio-compatible botanical extracts that communicate directly with skin cells to "
        "restore native barrier resilience."
    ),
    "key_ingredients": (
        "Dragon's Blood, Hyaluronic Acid, Vitamin C (Ascorbyl Glucoside), Caffeine, "
        "Cherry Extract, Red Clover Extract, Prickly Pear Extract, Radish Root Ferment"
    ),
    "key_benefits": (
        "Hydrates, Supports the Skin Barrier, Soothes & Comforts, Revives Skin Radiance, "
        "Lightweight & Fast Absorbing, Antioxidant-Rich Formula"
    ),
    "how_to_use": (
        "Morning: apply 2-3 drops onto clean skin, press gently into face and neck, then "
        "follow with daily sun shield. Night: smooth over cleansed skin and allow the active "
        "lipids to penetrate."
    ),
}

IMAGES = {
    "hero": "elara-serum.jpg",
    "ingredients_image": "elara-bio-botanicals.jpg",
    "texture_image": "elara-texture-glow.png",
}

CONTENT = {
    "hero_eyebrow": "Cellular Regeneration",
    "image_badge": "Flagship Formulation",
    "benefits": [
        {"icon": "droplet", "label": "Hydrates"},
        {"icon": "shield", "label": "Supports the Skin Barrier"},
        {"icon": "heart-handshake", "label": "Soothes & Comforts"},
        {"icon": "sparkles", "label": "Revives Skin Radiance"},
        {"icon": "feather", "label": "Lightweight & Fast Absorbing"},
        {"icon": "shield-check", "label": "Antioxidant-Rich Formula"},
    ],
    "why_heading": "Modern environments challenge the skin barrier every day.",
    "why_body": "ELARA was created to help skin recover.",
    "concerns": ["Pollution", "Stress", "Climate", "Blue Light", "Daily Fatigue"],
    "ingredients_heading": "8 Active Bio-Botanicals",
    "ingredients_body": (
        "Rather than flooding skin with aggressive percentages, ELARA delivers 8 "
        "bio-compatible botanical extracts that communicate directly with skin cells to "
        "restore native barrier resilience."
    ),
    "ingredients_badge": "Bio-Identical Synergies",
    "ingredients": [
        {"name": "Dragon's Blood", "description": "Precious Amazonian tree resin chosen to soothe, protect, and fortify natural skin resilience."},
        {"name": "Hyaluronic Acid", "description": "Multi-molecular hydration complex providing deep, sustained water retention."},
        {"name": "Vitamin C (Ascorbyl Glucoside)", "description": "Stabilized antioxidant derivative that brightens tone and defends against daily stress."},
        {"name": "Caffeine", "description": "Energizing botanical agent that revitalizes micro-circulation and calms puffiness."},
        {"name": "Cherry Extract", "description": "Nutrient-dense super-berry bio-active rich in natural antioxidants and vitamins."},
        {"name": "Red Clover Extract", "description": "Botanical balancing extract known to refine skin texture and soothe sensitivity."},
        {"name": "Prickly Pear Extract", "description": "Desert-resilient botanical that deeply nourishes and locks in essential moisture."},
        {"name": "Radish Root Ferment", "description": "Natural probiotic ferment peptide that preserves skin flora and formula purity."},
    ],
    "texture_heading": "Fluidity Meets Substance",
    "texture_body": (
        "A velvet-smooth, fast-absorbing elixir that melts into skin upon contact, leaving "
        "zero heavy residue."
    ),
    "texture_points": [
        {"title": "Comfort", "description": "Instantly calms irritation with a weightless, soothing veil."},
        {"title": "Hydration", "description": "Deep, sustained moisture infusion that lasts all day."},
        {"title": "Radiance", "description": "Unlocks a natural, inner luminosity without excess shine."},
    ],
    "ritual_heading": "Harmonized Application",
    "morning_ritual": [
        {"title": "Apply", "description": "2–3 drops onto clean skin"},
        {"title": "Absorb", "description": "Press gently into face & neck"},
        {"title": "Protect", "description": "Follow with daily sun shield"},
    ],
    "night_ritual": [
        {"title": "Repair", "description": "Smooth over cleansed skin"},
        {"title": "Recover", "description": "Allow active lipids to penetrate"},
        {"title": "Wake Renewed", "description": "Awaken to replenished vitality"},
    ],
    "specifications": [
        {"label": "Product Type", "value": "Facial Serum"},
        {"label": "Texture", "value": "Lightweight gel serum"},
        {"label": "Skin Type", "value": "All Skin Types"},
        {"label": "Size", "value": "30 ml"},
        {"label": "Use", "value": "Morning & Evening"},
        {"label": "Absorption", "value": "Fast Absorbing"},
        {"label": "Finish", "value": "Natural Healthy Glow"},
    ],
    "suitable_for": [
        "Sensitive Skin",
        "Dry Skin",
        "Combination Skin",
        "Normal Skin",
        "Dehydrated Skin",
        "Dull Skin",
        "Post-Acne Marks",
    ],
    "faqs": [
        {"question": "How often should I use ELARA Regenerative Barrier Serum?", "answer": "For optimal results, apply 2 to 3 drops daily in both your morning and evening rituals after cleansing."},
        {"question": "Is ELARA suitable for sensitive or climate-stressed skin?", "answer": "Yes. ELARA is explicitly formulated for skin exposed to heat, air conditioning, and urban stressors, tested for optimal skin compatibility."},
        {"question": "Can ELARA be layered with other skincare products?", "answer": "Absolutely. Its lightweight fluid texture absorbs rapidly, making it ideal under moisturizers, sunscreen, or makeup."},
        {"question": "What makes ELARA different from conventional serums?", "answer": "ELARA focuses on cellular harmony rather than high-percentage harsh actives, repairing the barrier while boosting natural resilience."},
    ],
}

ARABIC = {
    "title": "إيلارا",
    "sub_title": "سيروم التجديد وحماية حاجز البشرة",
    "size": "٣٠ مل",
    "hero_eyebrow": "التركيبة الفاخرة",
    "benefits": [
        {"icon": "droplet", "label": "يرطب البشرة"},
        {"icon": "shield", "label": "يدعم حاجز البشرة"},
        {"icon": "heart-handshake", "label": "يهدئ البشرة ويمنحها الراحة"},
        {"icon": "sparkles", "label": "يعيد للبشرة مظهرها الصحي والمشرق"},
        {"icon": "feather", "label": "تركيبة خفيفة وسريعة الامتصاص"},
        {"icon": "shield-check", "label": "تركيبة غنية بمضادات الأكسدة"},
    ],
    "why_heading": "تتعرض البشرة يوميًا للتحديات البيئية الحديثة",
    "why_body": "صُمِّم إيلارا لمساعدة البشرة على التعافي والتجدد.",
    "concerns": ["التلوث البيئي", "الإجهاد اليومي", "المناخ المتغير", "الضوء الأزرق", "الإرهاق اليومي"],
    "ingredients_heading": "ثمانية مكونات فعّالة، تركيبة واحدة.",
    "ingredients_body": (
        "تعتمد إلارا على ثمانية مكونات فعالة تعمل بتناغم لدعم حاجز البشرة، وتعزيز الترطيب، "
        "واستعادة الإشراقة الطبيعية."
    ),
    "ingredients": [
        {"name": "دم التنين (Dragon's Blood)", "description": "راتنج طبيعي غني بمضادات الأكسدة، يساعد على تهدئة البشرة، ودعم حاجزها الطبيعي، وتعزيز مرونتها."},
        {"name": "حمض الهيالورونيك", "description": "يمنح البشرة ترطيبًا عميقًا، ويعزز امتلاءها ونعومتها."},
        {"name": "فيتامين C (أسكوربيل جلوكوزيد)", "description": "يساعد على توحيد لون البشرة، ويعزز إشراقتها الطبيعية، ويحميها من العوامل البيئية."},
        {"name": "الكافيين", "description": "يساعد على تنشيط البشرة وتقليل مظهر الإرهاق، ليمنحها مظهرًا أكثر حيوية."},
        {"name": "مستخلص الكرز", "description": "غني بمضادات الأكسدة، يساعد على حماية البشرة وتعزيز حيويتها وإشراقتها الطبيعية."},
        {"name": "مستخلص البرسيم الأحمر", "description": "يساعد على تهدئة البشرة، وتحسين نعومتها، وتقليل مظهر الحساسية."},
        {"name": "مستخلص التين الشوكي", "description": "مستخلص نباتي غني بالترطيب، يدعم حاجز البشرة الطبيعي ويحافظ على توازنها."},
        {"name": "مخمر جذور الفجل", "description": "مكون طبيعي يدعم توازن البشرة ويساعد في الحفاظ على استقرار التركيبة."},
    ],
    "texture_heading": "ملمس حريري، امتصاص فوري",
    "texture_body": (
        "تركيبة خفيفة تنساب بسلاسة على البشرة وتمتص بسرعة، لتمنحها ترطيبًا مريحًا دون أي "
        "إحساس دهني أو ثقيل."
    ),
    "texture_points": [
        {"title": "الراحة", "description": "يمنح البشرة إحساسًا فوريًا بالراحة والنعومة."},
        {"title": "الترطيب", "description": "يرطب البشرة بعمق ويحافظ على نعومتها طوال اليوم."},
        {"title": "الإشراقة", "description": "يعزز الإشراقة الطبيعية دون ترك أي لمعان دهني."},
    ],
    "ritual_heading": "طريقة الاستخدام",
    "morning_ritual": [
        {"title": "التطبيق", "description": "ضعي 2–3 قطرات على بشرة نظيفة وجافة."},
        {"title": "التوزيع", "description": "وزّعي السيروم بلطف على الوجه والرقبة حتى يمتص بالكامل."},
        {"title": "الحماية", "description": "اتبعيه بواقي الشمس ضمن روتينك الصباحي."},
    ],
    "night_ritual": [
        {"title": "التطبيق", "description": "ضعي 2–3 قطرات على بشرة نظيفة بعد تنظيف الوجه."},
        {"title": "التوزيع", "description": "وزّعي السيروم بلطف على الوجه والرقبة حتى يمتص بالكامل."},
        {"title": "الاستعادة", "description": "اتركي السيروم يعمل طوال الليل لتستيقظي ببشرة أكثر ترطيبًا وإشراقًا"},
    ],
    "specifications": [
        {"label": "نوع المنتج", "value": "سيروم للوجه"},
        {"label": "الملمس", "value": "سيروم جيل خفيف الوزن"},
        {"label": "نوع البشرة", "value": "جميع أنواع البشرة"},
        {"label": "الحجم", "value": "٣٠ مل"},
        {"label": "طريقة الاستخدام", "value": "صباحاً ومساءً"},
        {"label": "الامتصاص", "value": "سريع الامتصاص"},
        {"label": "المظهر النهائي", "value": "إشراقة صحية طبيعية"},
    ],
    "suitable_for": [
        "البشرة الحساسة",
        "البشرة الجافة",
        "البشرة المختلطة",
        "البشرة العادية",
        "البشرة فاقدة الترطيب",
        "البشرة الباهتة",
        "آثار ما بعد حب الشباب",
    ],
    "faqs": [
        {"question": "كم مرة يجب استخدام سيروم إيلارا؟", "answer": "للحصول على أفضل النتائج، ضعي من ٢ إلى ٣ قطرات يوميًا في طقوس الصباح والمساء بعد التنظيف."},
        {"question": "هل إيلارا مناسب للبشرة الحساسة أو المتأثرة بالمناخ؟", "answer": "نعم. صُمم إيلارا خصيصًا للبشرة المعرضة للحرارة والتكييف والعوامل البيئية الحضرية."},
        {"question": "هل يمكن استخدام إيلارا مع منتجات العناية الأخرى؟", "answer": "بالتأكيد. ملمسه السائل الخفيف يمتص بسرعة، مما يجعله مثاليًا تحت المرطبات أو واقي الشمس."},
        {"question": "ما الذي يميز إيلارا عن السيرومات التقليدية؟", "answer": "يركز إيلارا على التناغم الخلوي بدلاً من الأحماض المجهدة، حيث يعيد ترميم الحاجز ويعزز المرونة الطبيعية."},
    ],
}
