import string
import random
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings

User = settings.AUTH_USER_MODEL


def generate_league_code():
    """Genera un codice alfanumerico univoco per la lega"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(6))
        if not League.objects.filter(join_code=code).exists():
            return code


class League(models.Model):
    """Modello per le leghe di padel"""
    name = models.CharField(max_length=100, verbose_name="Nome lega")
    created_at = models.DateTimeField(auto_now_add=True)
    president = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='presided_leagues',
        verbose_name="Presidente"
    )
    join_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_league_code,
        verbose_name="Codice di accesso"
    )
    players = models.ManyToManyField(
        User,
        through='Membership',
        related_name='leagues',
        verbose_name="Giocatori"
    )
    
    class Meta:
        verbose_name = "Lega"
        verbose_name_plural = "Leghe"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_league_standings(self):
        """Calcola e restituisce la classifica dei giocatori nella lega"""
        # Membri della lega
        members = self.membership_set.all()
        standings = []
        
        for membership in members:
            player = membership.player
            
            # Statistiche partite
            player_matches = MatchPlayer.objects.filter(
                player=player,
                match__league=self
            )
            matches_played = player_matches.count()
            
            if matches_played == 0:
                continue
                
            # Calcola vittorie, pareggi, sconfitte e set vinti
            wins = 0
            draws = 0
            sets_won = 0

            for mp in player_matches:
                match = mp.match
                
                # Determina se è un pareggio
                if match.team1_sets == match.team2_sets:
                    draws += 1
                # Determina se il giocatore ha vinto
                elif (mp.team == 1 and match.team1_sets > match.team2_sets) or \
                    (mp.team == 2 and match.team2_sets > match.team1_sets):
                    wins += 1
                
                # Calcola set vinti
                if mp.team == 1:
                    sets_won += match.team1_sets
                else:
                    sets_won += match.team2_sets

            losses = matches_played - wins - draws

            # Calcola punti (3 per vittoria, 1 per pareggio)
            points = (wins * 3) + draws
            
            standings.append({
            'player': player,
            'matches_played': matches_played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'sets_won': sets_won,
            'points': points
        })
        
        # Ordina per punti, quindi premia chi ha giocato meno partite (rateo più alto), quindi vittorie, set vinti
        standings.sort(
            key=lambda x: (x['points'], -x['matches_played'], x['wins'], x['sets_won']),
            reverse=True
        )
        
        return standings


class Membership(models.Model):
    """Modello per l'appartenenza di un utente a una lega"""
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Iscrizione"
        verbose_name_plural = "Iscrizioni"
        unique_together = ['player', 'league']
    
    def __str__(self):
        return f"{self.player} - {self.league.name}"


class Match(models.Model):
    """Modello per le partite di padel"""
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name='matches',
        verbose_name="Lega"
    )
    match_date = models.DateField(default=timezone.now, verbose_name="Data partita")
    team1_sets = models.PositiveSmallIntegerField(default=0, verbose_name="Set Squadra 1")
    team2_sets = models.PositiveSmallIntegerField(default=0, verbose_name="Set Squadra 2")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Partita"
        verbose_name_plural = "Partite"
        ordering = ['-match_date', '-created_at']
    
    def __str__(self):
        team1_players = self.players.filter(team=1)
        team2_players = self.players.filter(team=2)
        
        if not team1_players.exists() or not team2_players.exists():
            return f"Partita {self.id} ({self.match_date})"
            
        team1_str = " / ".join([str(mp.player) for mp in team1_players])
        team2_str = " / ".join([str(mp.player) for mp in team2_players])
        
        return f"{team1_str} {self.team1_sets}-{self.team2_sets} {team2_str} ({self.match_date})"
    
    @property
    def winner_team(self):
        """Restituisce il numero della squadra vincitrice (1 o 2) o None se pareggio"""
        if self.team1_sets > self.team2_sets:
            return 1
        elif self.team2_sets > self.team1_sets:
            return 2
        return None


class MatchPlayer(models.Model):
    """Relazione tra giocatori e partite"""
    TEAM_CHOICES = [
        (1, 'Squadra 1'),
        (2, 'Squadra 2'),
    ]
    
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='players'
    )
    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    team = models.PositiveSmallIntegerField(choices=TEAM_CHOICES)
    
    class Meta:
        verbose_name = "Giocatore partita"
        verbose_name_plural = "Giocatori partita"
        unique_together = ['match', 'player']
    
    def __str__(self):
        return f"{self.player} - {self.get_team_display()}"