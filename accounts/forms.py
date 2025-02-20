from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class UserRegisterForm(UserCreationForm):
    """Form per registrare un nuovo utente"""
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendi opzionali i campi first_name e last_name
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        
        # Personalizza i messaggi di aiuto
        self.fields['username'].help_text = 'Richiesto. 150 caratteri o meno. Solo lettere, numeri e @/./+/-/_.'
        self.fields['password1'].help_text = 'La password deve contenere almeno 8 caratteri.'

class UserUpdateForm(forms.ModelForm):
    """Form per aggiornare i dati del profilo utente"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']