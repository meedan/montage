"""
    Forms for the admin app
"""
from django import forms

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from greenday_core.models import PendingUser


class InviteNewUserForm(forms.Form):
    """
        Form definition to invite new whitelisted users to Montage
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "autofocus": "autofocus",
            "required": "required",
            "placeholder": "Enter email address"}))

    def clean_email(self):
        """
            Validates the entered email address
        """
        email = self.cleaned_data['email']

        if get_user_model().objects.filter(email=email).exists():
            raise ValidationError("User already exists")

        if PendingUser.objects.filter(email=email).exists():
            raise ValidationError("User has already been invited")

        return email
