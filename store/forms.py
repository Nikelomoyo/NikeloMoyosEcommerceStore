from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=999, initial=1)

class CheckoutForm(forms.ModelForm):
    token = forms.UUIDField(widget=forms.HiddenInput)
    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'address']
        labels = {'name': 'Full name', 'address': 'Shipping address'}
        widgets = {'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Street, suburb, city, province and postal code'}),
                   'name': forms.TextInput(attrs={'autocomplete': 'name'}),
                   'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
                   'phone': forms.TextInput(attrs={'autocomplete': 'tel', 'type': 'tel'})}
    def clean_phone(self):
        value = self.cleaned_data['phone']
        if not 7 <= len(''.join(c for c in value if c.isdigit())) <= 15:
            raise forms.ValidationError('Enter a valid phone number with 7 to 15 digits.')
        return value
