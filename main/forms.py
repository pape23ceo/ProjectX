# myapp/forms.py
from django import forms

class ContactForm(forms.Form):
    token = forms.CharField(label="Your name", max_length=100)
