from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Estensione del modello utente di Django.
    Include nome, cognome, email, nickname e data di nascita.
    """
    # La email diventa obbligatoria
    email = models.EmailField(unique=True, verbose_name='Email')
    
    # Aggiungiamo il campo data di nascita
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Data di nascita')
    
    # Ripristiniamo l'uso dell'email per validazione
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Utente'
        verbose_name_plural = 'Utenti'
    
    def __str__(self):
        return self.username
    
    def is_league_president(self, league):
        """Controlla se l'utente è presidente della lega specificata"""
        return hasattr(league, 'president') and league.president == self