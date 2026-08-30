import re
from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r"[A-Za-z]", password):
            raise ValidationError(
                "Password must contain at least one letter."
            )

        if not re.search(r"\d", password):
            raise ValidationError(
                "Password must contain at least one number."
            )

        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                "Password must contain at least one special character."
            )

    def get_help_text(self):
        return (
            "Your password must contain at least one letter, "
            "one number, and one special character."
        )