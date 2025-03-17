from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class UserRegisterForm(UserCreationForm):
    """Form per registrare un nuovo utente"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'date_of_birth', 'password1', 'password2']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendi obbligatori i campi richiesti
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        
        # Personalizza i messaggi di aiuto
        self.fields['username'].help_text = 'Richiesto. 150 caratteri o meno. Solo lettere, numeri e @/./+/-/_.'
        self.fields['password1'].help_text = 'La password deve contenere almeno 8 caratteri.'
        self.fields['email'].help_text = 'Inserisci un indirizzo email valido.'
        self.fields['date_of_birth'].help_text = 'Formato: AAAA-MM-GG'

class UserUpdateForm(forms.ModelForm):
    """Form per aggiornare i dati del profilo utente"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


from django.contrib.auth.forms import PasswordResetForm

class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Override del metodo per personalizzare l'oggetto e il corpo dell'email senza usare file separati
        """
        subject = "Reset password CrazyPadel"
        user = context.get('user')
        
        # Personalizza l'email in base al fatto che l'utente abbia un nome o meno
        greeting = f"Ciao {user.first_name}," if user.first_name else f"Ciao {user.username},"
        
        # Genera l'URL per il reset
        protocol = context.get('protocol')
        domain = context.get('domain')
        uid = context.get('uid')
        token = context.get('token')
        reset_url = f"{protocol}://{domain}/accounts/password-reset-confirm/{uid}/{token}/"
        
        # Crea il corpo dell'email in HTML
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #2b6cb0; margin-bottom: 20px;">Reset Password CrazyPadel</h2>
                <p>{greeting}</p>
                <p>Hai richiesto il reset della password per il tuo account su CrazyPadel.</p>
                <p>Clicca sul pulsante qui sotto per reimpostare la tua password:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #3182ce; color: white; padding: 12px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">Reset Password</a>
                </p>
                <p>Se non riesci a cliccare sul pulsante, puoi copiare e incollare questo link nel browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p>Se non sei stato tu a richiedere il reset della password, puoi ignorare questa email.</p>
                <p style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; font-size: 0.9em;">
                    Cordiali saluti,<br>
                    Il team di CrazyPadel
                </p>
            </div>
        </body>
        </html>
        """
        
        # Crea il testo semplice come alternativa
        text_message = f"""
        {greeting}

        Hai richiesto il reset della password per il tuo account su CrazyPadel.
        Clicca sul link qui sotto per reimpostare la tua password:

        {reset_url}

        Se non sei stato tu a richiedere il reset della password, puoi ignorare questa email.

        Cordiali saluti,
        Il team di CrazyPadel
        """
        
        # Invia l'email
        from django.core.mail import EmailMultiAlternatives
        email = EmailMultiAlternatives(subject, text_message, from_email, [to_email])
        email.attach_alternative(html_message, "text/html")
        email.send()