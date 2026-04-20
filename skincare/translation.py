import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skincare.settings')
django.setup()


from google import genai
from django.conf import settings

client = genai.Client(api_key=settings.GIMINIAPI_KEY)


def translate_text(text, target_language):
    lang_map = {
        "EN": "English",
        "AR": "Arabic"
    }

    language = lang_map.get(target_language.strip().upper())
    

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            Translate the following text into {language}.
            Keep the meaning accurate and natural. Only return the translated text.
            - Do not add explanations
            - Return only the translated text

            Text:
            {text}
            """
        )

        if not response or not response.text:
            print("no translation available")
            return text

        return response.text.strip()

    except Exception as e:
        print("Translation error:", str(e))
        return text