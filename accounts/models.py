from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Estensione del modello utente di Django.
    Non richiediamo email, solo username e password.
    """
    # Il campo email è opzionale
    email = models.EmailField(blank=True, null=True)
    
    # Disabilita l'uso dell'email per validazione
    EMAIL_FIELD = None
    REQUIRED_FIELDS = []  # Rimuoviamo 'email' dalla lista dei campi richiesti
    
    class Meta:
        verbose_name = 'Utente'
        verbose_name_plural = 'Utenti'
    
    def __str__(self):
        return self.username
    
    def is_league_president(self, league):
        """Controlla se l'utente è presidente della lega specificata"""
        return hasattr(league, 'president') and league.president == self