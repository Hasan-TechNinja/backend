from rest_framework import serializers

class TranslatedField(serializers.Field):
    def __init__(self, field_en, field_ar, **kwargs):
        self.field_en = field_en
        self.field_ar = field_ar
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        """
        Override get_attribute so that the field always receives the model instance,
        not the attribute value. This avoids DRF passing a string instead of the instance.
        """
        return instance

    def to_representation(self, obj):
        """
        obj is guaranteed to be the model instance here.
        """
        if obj is None:
            return None

        try:
            request = self.context.get("request")
            lean = (request.query_params.get("lean") if request else "EN") or "EN"
            lean = lean.strip().upper()

            val_en = getattr(obj, self.field_en, None)
            val_ar = getattr(obj, self.field_ar, None)

            if lean == "EN":
                return val_en or val_ar
            else:
                return val_ar or val_en
        except Exception as e:
            print(f"Error in TranslatedField: {e}")
            return None
        
