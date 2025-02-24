from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import UserRegisterForm, UserUpdateForm
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

def register(request):
    """Vista per la registrazione di un nuovo utente"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account creato con successo!')
            return redirect('leagues:list')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    """Vista per visualizzare e modificare il profilo utente"""
    from django.db.models import Count, Q, Sum, Case, When, IntegerField, F
    from django.utils import timezone
    import datetime
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Il tuo profilo è stato aggiornato!')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    # Statistiche di base
    leagues_count = request.user.leagues.count()
    
    # Statistiche partite
    user_matches = request.user.matches.all()
    total_matches = user_matches.count()
    
    # Calcola vittorie
    wins_count = 0
    draws_count = 0
    losses_count = 0
    sets_won = 0
    total_sets = 0
    
    # Statistiche partner e avversari
    teammates = {}
    opponents = {}
    
    # Analisi partite
    for match_player in user_matches.select_related('match'):
        match = match_player.match
        team = match_player.team
        
        # Calcola set totali
        total_sets += match.team1_sets + match.team2_sets
        
        # Calcola vittorie/sconfitte
        if team == 1:
            sets_won += match.team1_sets
            if match.team1_sets > match.team2_sets:
                wins_count += 1
            elif match.team1_sets < match.team2_sets:
                losses_count += 1
            elif match.team1_sets == match.team2_sets:
                # Pareggio
                draws_count = draws_count if 'draws_count' in locals() else 0
                draws_count += 1
        else:
            sets_won += match.team2_sets
            if match.team2_sets > match.team1_sets:
                wins_count += 1
            elif match.team2_sets < match.team1_sets:
                losses_count += 1
            elif match.team1_sets == match.team2_sets:
                # Pareggio
                draws_count = draws_count if 'draws_count' in locals() else 0
                draws_count += 1
        
        # Analisi compagni di squadra
        teammates_in_match = match.players.filter(team=team).exclude(player=request.user)
        for teammate in teammates_in_match:
            if teammate.player_id not in teammates:
                teammates[teammate.player_id] = {'player': teammate.player, 'matches': 0, 'wins': 0}
            
            teammates[teammate.player_id]['matches'] += 1
            if (team == 1 and match.team1_sets > match.team2_sets) or (team == 2 and match.team2_sets > match.team1_sets):
                teammates[teammate.player_id]['wins'] += 1
        
        # Analisi avversari
        opponents_in_match = match.players.filter(~Q(team=team))
        for opponent in opponents_in_match:
            if opponent.player_id not in opponents:
                opponents[opponent.player_id] = {'player': opponent.player, 'matches': 0, 'losses': 0}
            
            opponents[opponent.player_id]['matches'] += 1
            if (team == 1 and match.team1_sets < match.team2_sets) or (team == 2 and match.team2_sets < match.team1_sets):
                opponents[opponent.player_id]['losses'] += 1
    
    # Calcola percentuale vittorie
    win_percentage = int((wins_count / total_matches) * 100) if total_matches > 0 else 0
    avg_sets_per_match = round(total_sets / total_matches, 1) if total_matches > 0 else 0
    
    # Calcola percentuale set vinti
    set_win_percentage = int((sets_won / total_sets) * 100) if total_sets > 0 else 0
    
    # Trova compagno preferito
    favorite_partner = None
    partner_stats = None
    if teammates:
        best_teammate_id = max(teammates.items(), key=lambda x: x[1]['wins'])
        favorite_partner = best_teammate_id[1]['player']
        partner_stats = {
            'matches': best_teammate_id[1]['matches'],
            'wins': best_teammate_id[1]['wins'],
            'win_rate': int((best_teammate_id[1]['wins'] / best_teammate_id[1]['matches']) * 100) if best_teammate_id[1]['matches'] > 0 else 0
        }
    
    # Trova avversario più difficile
    toughest_opponent = None
    opponent_stats = None
    if opponents:
        worst_opponent_id = max(opponents.items(), key=lambda x: x[1]['losses'])
        toughest_opponent = worst_opponent_id[1]['player']
        opponent_stats = {
            'matches': worst_opponent_id[1]['matches'],
            'losses': worst_opponent_id[1]['losses'],
            'loss_rate': int((worst_opponent_id[1]['losses'] / worst_opponent_id[1]['matches']) * 100) if worst_opponent_id[1]['matches'] > 0 else 0
        }

    # Trova la vittima preferita (avversario contro cui si vince di più)
    favorite_victim = None
    victim_stats = None
    if opponents:
        # Per ogni avversario, calcola le vittorie (cioè le partite - le sconfitte)
        for opp_id, stats in opponents.items():
            wins_against = stats['matches'] - stats['losses']
            stats['wins_against'] = wins_against
            
        # Trova l'avversario con più vittorie
        best_victim_id = max(opponents.items(), key=lambda x: x[1]['wins_against'])
        if best_victim_id[1]['wins_against'] > 0:  # Solo se c'è almeno una vittoria
            favorite_victim = best_victim_id[1]['player']
            victim_stats = {
                'matches': best_victim_id[1]['matches'],
                'wins_against': best_victim_id[1]['wins_against'],
                'win_rate': int((best_victim_id[1]['wins_against'] / best_victim_id[1]['matches']) * 100) if best_victim_id[1]['matches'] > 0 else 0
            }
    
    # Esempio di dati per trend di performance
    performance_trend = None
    if total_matches > 5:
        # Questa è solo una simulazione, in un'app reale andrebbero calcolati dai dati effettivi
        performance_trend = [
            {'month_short': 'Gen', 'month_name': 'Gennaio', 'wins': 3, 'matches': 5, 'win_rate': 60},
            {'month_short': 'Feb', 'month_name': 'Febbraio', 'wins': 4, 'matches': 6, 'win_rate': 67},
            {'month_short': 'Mar', 'month_name': 'Marzo', 'wins': 2, 'matches': 5, 'win_rate': 40},
            {'month_short': 'Apr', 'month_name': 'Aprile', 'wins': 5, 'matches': 7, 'win_rate': 71},
            {'month_short': 'Mag', 'month_name': 'Maggio', 'wins': 3, 'matches': 4, 'win_rate': 75},
            {'month_short': 'Giu', 'month_name': 'Giugno', 'wins': 2, 'matches': 3, 'win_rate': 67},
        ]
    
    # Esempio per campo fortunato
    lucky_court = None
    court_stats = None
    # In una vera app, questi dati verrebbero calcolati basandosi sui campi effettivi
    if total_matches > 3:
        lucky_court = "Centro Sportivo XYZ - Campo 3"
        court_stats = {
            'matches': 8,
            'wins': 6,
            'win_rate': 75
        }
    
    # Recupera le partite recenti
    recent_matches = []
    # Recupera tutte le partite
    if total_matches > 0:
        match_ids = user_matches.values_list('match_id', flat=True)
        from leagues.models import Match
        recent_matches = Match.objects.filter(id__in=match_ids).order_by('-match_date')  # Rimuovi [:5]

    # Calcola striscia di vittorie consecutive
    winning_streak = 0
    if recent_matches:
        for match in recent_matches:
            # Trova il match player relativo all'utente corrente
            user_mp = match.players.filter(player=request.user).first()
            if user_mp:
                team = user_mp.team
                if (team == 1 and match.team1_sets > match.team2_sets) or (team == 2 and match.team2_sets > match.team1_sets):
                    winning_streak += 1
                else:
                    # Se ha perso, interrompiamo il conteggio
                    break
            else:
                break
    
    context = {
        'form': form,
        'leagues_count': leagues_count,
        'total_matches': total_matches,
        'total_wins': wins_count,
        'total_losses': losses_count,
        'win_percentage': win_percentage,
        'total_draws': draws_count,
        'set_win_percentage': set_win_percentage,
        'total_sets': total_sets,
        'sets_won': sets_won,
        'avg_sets_per_match': avg_sets_per_match,
        'favorite_partner': favorite_partner,
        'partner_stats': partner_stats,
        'toughest_opponent': toughest_opponent,
        'opponent_stats': opponent_stats,
        'performance_trend': performance_trend,
        'recent_matches': recent_matches,
        'winning_streak': winning_streak,
        'favorite_victim': favorite_victim,
        'victim_stats': victim_stats,
    }
    
    return render(request, 'accounts/profile.html', context)

