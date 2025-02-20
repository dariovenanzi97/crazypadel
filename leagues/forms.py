from django import forms
from .models import League, Match

class LeagueForm(forms.ModelForm):
    """Form per creare una nuova lega"""
    class Meta:
        model = League
        fields = ['name']
        labels = {
            'name': 'Nome della lega',
        }

class JoinLeagueForm(forms.Form):
    """Form per unirsi a una lega tramite codice"""
    join_code = forms.CharField(
        max_length=6, 
        min_length=6,
        label='Codice di accesso',
        help_text='Inserisci il codice di 6 caratteri fornito dal presidente della lega'
    )
    
    def clean_join_code(self):
        code = self.cleaned_data['join_code'].upper()
        return code

class MatchForm(forms.ModelForm):
    """Form per creare/modificare una partita"""
    team1_player1 = forms.ModelChoiceField(queryset=None, label='Giocatore 1 (squadra 1)')
    team1_player2 = forms.ModelChoiceField(queryset=None, label='Giocatore 2 (squadra 1)')
    team2_player1 = forms.ModelChoiceField(queryset=None, label='Giocatore 1 (squadra 2)')
    team2_player2 = forms.ModelChoiceField(queryset=None, label='Giocatore 2 (squadra 2)')
    
    class Meta:
        model = Match
        fields = ['match_date', 'team1_sets', 'team2_sets']
        labels = {
            'match_date': 'Data della partita',
            'team1_sets': 'Set vinti dalla squadra 1',
            'team2_sets': 'Set vinti dalla squadra 2',
        }
        widgets = {
            'match_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Estrai la lega dal kwargs
        self.league = kwargs.pop('league', None)
        super().__init__(*args, **kwargs)
        
        if self.league:
            # Imposta i queryset con i membri della lega
            members = self.league.players.all()
            self.fields['team1_player1'].queryset = members
            self.fields['team1_player2'].queryset = members
            self.fields['team2_player1'].queryset = members
            self.fields['team2_player2'].queryset = members
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Controllo che i 4 giocatori siano diversi
        players = [
            cleaned_data.get('team1_player1'),
            cleaned_data.get('team1_player2'),
            cleaned_data.get('team2_player1'),
            cleaned_data.get('team2_player2'),
        ]
        
        if len(set(filter(None, players))) != 4:
            raise forms.ValidationError(
                "Tutti i giocatori devono essere diversi. Ogni partita deve avere esattamente 4 giocatori distinti."
            )
        
        return cleaned_data