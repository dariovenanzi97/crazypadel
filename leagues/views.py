from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import League, Membership, Match, MatchPlayer
from .forms import LeagueForm, JoinLeagueForm, MatchForm

def get_team_players_string(match, team_number):
    """Restituisce una stringa formattata con i nomi dei giocatori di una squadra"""
    player_names = []
    for mp in match.players.filter(team=team_number):
        player_names.append(mp.player.username)
    return " / ".join(player_names)

@login_required
def league_list(request):
    """Vista per visualizzare le leghe dell'utente"""
    user_leagues = request.user.leagues.all()
    return render(request, 'leagues/league_list.html', {'leagues': user_leagues})

@login_required
def create_league(request):
    """Vista per creare una nuova lega"""
    if request.method == 'POST':
        form = LeagueForm(request.POST)
        if form.is_valid():
            league = form.save(commit=False)
            league.president = request.user
            league.save()
            
            # Aggiungi anche il presidente come membro
            Membership.objects.create(player=request.user, league=league)
            
            messages.success(request, f'Lega "{league.name}" creata con successo!')
            return redirect('leagues:detail', league_id=league.id)
    else:
        form = LeagueForm()
    
    return render(request, 'leagues/create_league.html', {'form': form})

@login_required
def league_detail(request, league_id):
    """Vista unificata per i dettagli di una lega, classifica e partite"""
    from django.db.models import Count, Q, Max, Min
    from collections import defaultdict
    import datetime
    
    league = get_object_or_404(League, id=league_id)
    
    # Verifica che l'utente sia membro della lega
    if not league.players.filter(id=request.user.id).exists():
        return HttpResponseForbidden("Non sei membro di questa lega")
    
    # Ottieni tutte le partite
    matches = league.matches.all().order_by('-match_date', '-created_at')
    
    # Ottieni le ultime 5 partite
    recent_matches = matches[:5]
    
    # Prepara le stringhe dei giocatori per ogni partita
    for match in matches:
        match.team1_players_str = get_team_players_string(match, 1)
        match.team2_players_str = get_team_players_string(match, 2)
    
    for match in recent_matches:
        match.team1_players_str = get_team_players_string(match, 1)
        match.team2_players_str = get_team_players_string(match, 2)
    
    # Ottieni la classifica
    standings = league.get_league_standings()
    
    # ========== STATISTICHE AVANZATE ==========
    
    # 1. L'Imbattibile - giocatori ordinati per minor numero di sconfitte
    # (già disponibile in standings, ordinato per punti e poi sconfitte)
    unbeatable_players = sorted(
        [player for player in standings if player['matches_played'] > 0],
        key=lambda x: (x['losses'], -x['matches_played'])
    )[:5]
    
    # 2. Gli Imbattibili - coppie con meno sconfitte
    teams_data = defaultdict(lambda: {'wins': 0, 'losses': 0, 'matches': 0})

    if matches:
        for match in matches:
            # Ottieni i giocatori di ciascuna squadra
            team1_players = list(match.players.filter(team=1).select_related('player'))
            team2_players = list(match.players.filter(team=2).select_related('player'))
            
            # Solo se entrambe le squadre hanno esattamente 2 giocatori
            if len(team1_players) == 2 and len(team2_players) == 2:
                # Crea le chiavi delle coppie (ordina i nomi per consistenza)
                team1_key = tuple(sorted([p.player.username for p in team1_players]))
                team2_key = tuple(sorted([p.player.username for p in team2_players]))
                
                # Incrementa match contati
                teams_data[team1_key]['matches'] += 1
                teams_data[team2_key]['matches'] += 1
                
                # Determina vittoria/sconfitta
                if match.team1_sets > match.team2_sets:
                    teams_data[team1_key]['wins'] += 1
                    teams_data[team2_key]['losses'] += 1
                elif match.team2_sets > match.team1_sets:
                    teams_data[team2_key]['wins'] += 1
                    teams_data[team1_key]['losses'] += 1
    
    # Converti in lista e calcola statistiche
    unbeatable_teams = []
    for team, stats in teams_data.items():
        if stats['matches'] >= 2:  # Solo coppie con almeno 2 partite
            team_stats = {
                'player1': team[0],  # Nome del primo giocatore
                'player2': team[1],  # Nome del secondo giocatore
                'matches': stats['matches'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': int((stats['wins'] / stats['matches']) * 100) if stats['matches'] > 0 else 0
            }
            unbeatable_teams.append(team_stats)

    # Ordina semplicemente per numero di vittorie (in ordine decrescente)
    unbeatable_teams = sorted(unbeatable_teams, key=lambda x: -x['wins'])[:5]    
    
    # 3. In Forma - giocatori con la serie positiva più lunga attiva
    player_streaks = defaultdict(int)
    player_last_matches = {}
    
    if matches:
        # Mappa ogni giocatore all'ultima partita giocata
        all_players = league.players.all()
        for player in all_players:
            # Trova tutte le partite del giocatore ordinate per data (dalla più recente)
            player_matches = MatchPlayer.objects.filter(
                player=player,
                match__league=league
            ).select_related('match').order_by('-match__match_date', '-match__created_at')
            
            if player_matches.exists():
                player_last_matches[player.id] = player_matches[0].match.match_date
                
                # Calcola streak di vittorie
                current_streak = 0
                for mp in player_matches:
                    match = mp.match
                    player_won = (mp.team == 1 and match.team1_sets > match.team2_sets) or \
                                (mp.team == 2 and match.team2_sets > match.team1_sets)
                    
                    if player_won:
                        current_streak += 1
                    else:
                        break
                
                player_streaks[player.id] = {
                    'player': player,
                    'streak': current_streak
                }
    
    # Ordina per streak più lunga
    in_form_players = sorted(
        player_streaks.values(),
        key=lambda x: -x['streak']
    )[:5]
    
    # 4. Sparito - giocatori con meno partite
    # Prendi tutti i membri della lega
    league_members = league.membership_set.select_related('player').all()
    missing_players = []

    for membership in league_members:
        player = membership.player
        player_matches_count = MatchPlayer.objects.filter(
            player=player,
            match__league=league
        ).count()
        
        # Includi il giocatore solo se ha almeno una partita
        if player_matches_count > 0:
            missing_players.append({
                'player': player,
                'matches_count': player_matches_count,
                'last_match_date': player_last_matches.get(player.id, None)
            })

    # Ordina per minor numero di partite giocate
    missing_players = sorted(missing_players, key=lambda x: x['matches_count'])[:5]
    
    # 5. Sempre sul pezzo - giocatori con più partite giocate
    most_active_players = sorted(
        [p for p in standings if p['matches_played'] > 0],
        key=lambda x: -x['matches_played']
    )[:5]
    
    context = {
        'league': league,
        'is_president': request.user.is_league_president(league),
        'join_code': league.join_code if request.user.is_league_president(league) else None,
        'matches': matches,
        'recent_matches': recent_matches,
        'standings': standings,
        'now': timezone.now(),
        'user': request.user,  # per evidenziare l'utente corrente nella classifica
        
        # Statistiche avanzate
        'unbeatable_players': unbeatable_players,
        'unbeatable_teams': unbeatable_teams,
        'in_form_players': in_form_players,
        'missing_players': missing_players,
        'most_active_players': most_active_players,
    }
    return render(request, 'leagues/league_detail.html', context)


@login_required
def join_league(request, league_id):
    """Vista per unirsi a una lega (tramite ID)"""
    league = get_object_or_404(League, id=league_id)
    
    # Verifica se l'utente è già membro
    if league.players.filter(id=request.user.id).exists():
        messages.warning(request, f'Sei già membro della lega "{league.name}"')
        return redirect('leagues:detail', league_id=league.id)
    
    # Aggiungi l'utente alla lega
    Membership.objects.create(player=request.user, league=league)
    messages.success(request, f'Ti sei unito alla lega "{league.name}" con successo!')
    return redirect('leagues:detail', league_id=league.id)

@login_required
def join_by_code(request):
    """Vista per unirsi a una lega tramite codice"""
    if request.method == 'POST':
        form = JoinLeagueForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['join_code']
            try:
                league = League.objects.get(join_code=code)
                
                # Verifica se l'utente è già membro
                if league.players.filter(id=request.user.id).exists():
                    messages.warning(request, f'Sei già membro della lega "{league.name}"')
                else:
                    # Aggiungi l'utente alla lega
                    Membership.objects.create(player=request.user, league=league)
                    messages.success(request, f'Ti sei unito alla lega "{league.name}" con successo!')
                
                return redirect('leagues:detail', league_id=league.id)
            except League.DoesNotExist:
                messages.error(request, 'Codice non valido. Nessuna lega trovata.')
    else:
        form = JoinLeagueForm()
    
    return render(request, 'leagues/join_by_code.html', {'form': form})

@login_required
def league_standings(request, league_id):
    """Vista per visualizzare la classifica della lega (redirect a detail)"""
    return redirect('leagues:detail', league_id=league_id)

@login_required
def match_list(request, league_id):
    """Vista per visualizzare tutte le partite di una lega (redirect a detail)"""
    return redirect('leagues:detail', league_id=league_id)

@login_required
def match_detail(request, league_id, match_id):
    """Vista per i dettagli di una partita"""
    league = get_object_or_404(League, id=league_id)
    match = get_object_or_404(Match, id=match_id, league=league)
    
    # Verifica che l'utente sia membro della lega
    if not league.players.filter(id=request.user.id).exists():
        return HttpResponseForbidden("Non sei membro di questa lega")
    
    # Aggiungi le stringhe dei giocatori per ogni squadra
    match.team1_players_str = get_team_players_string(match, 1)
    match.team2_players_str = get_team_players_string(match, 2)
    
    context = {
        'league': league,
        'match': match,
        'is_president': request.user.is_league_president(league),
    }
    return render(request, 'leagues/match_detail.html', context)

@login_required
def create_match(request, league_id):
    """Vista per creare una nuova partita"""
    league = get_object_or_404(League, id=league_id)
    
    # Verifica che l'utente sia il presidente della lega
    if not request.user.is_league_president(league):
        return HttpResponseForbidden("Solo il presidente può creare partite")
    
    if request.method == 'POST':
        form = MatchForm(request.POST, league=league)
        if form.is_valid():
            match = form.save(commit=False)
            match.league = league
            match.save()
            
            # Salva i giocatori della partita
            team1_player1 = form.cleaned_data['team1_player1']
            team1_player2 = form.cleaned_data['team1_player2']
            team2_player1 = form.cleaned_data['team2_player1']
            team2_player2 = form.cleaned_data['team2_player2']
            
            MatchPlayer.objects.create(match=match, player=team1_player1, team=1)
            MatchPlayer.objects.create(match=match, player=team1_player2, team=1)
            MatchPlayer.objects.create(match=match, player=team2_player1, team=2)
            MatchPlayer.objects.create(match=match, player=team2_player2, team=2)
            
            messages.success(request, 'Partita creata con successo!')
            return redirect('leagues:detail', league_id=league.id)
    else:
        form = MatchForm(league=league)
    
    context = {
        'league': league,
        'form': form,
    }
    return render(request, 'leagues/create_match.html', context)

@login_required
def edit_match(request, league_id, match_id):
    """Vista per modificare una partita esistente"""
    league = get_object_or_404(League, id=league_id)
    match = get_object_or_404(Match, id=match_id, league=league)
    
    # Verifica che l'utente sia il presidente della lega
    if not request.user.is_league_president(league):
        return HttpResponseForbidden("Solo il presidente può modificare partite")
    
    if request.method == 'POST':
        form = MatchForm(request.POST, league=league, instance=match)
        if form.is_valid():
            # Aggiorna la partita
            match = form.save()
            
            # Aggiorna i giocatori
            MatchPlayer.objects.filter(match=match).delete()
            
            team1_player1 = form.cleaned_data['team1_player1']
            team1_player2 = form.cleaned_data['team1_player2']
            team2_player1 = form.cleaned_data['team2_player1']
            team2_player2 = form.cleaned_data['team2_player2']
            
            MatchPlayer.objects.create(match=match, player=team1_player1, team=1)
            MatchPlayer.objects.create(match=match, player=team1_player2, team=1)
            MatchPlayer.objects.create(match=match, player=team2_player1, team=2)
            MatchPlayer.objects.create(match=match, player=team2_player2, team=2)
            
            messages.success(request, 'Partita aggiornata con successo!')
            return redirect('leagues:detail', league_id=league.id)
    else:
        # Inizializza il form con i dati esistenti
        initial_data = {}
        
        # Ottieni i giocatori attuali
        team1_players = list(match.players.filter(team=1).values_list('player', flat=True))
        team2_players = list(match.players.filter(team=2).values_list('player', flat=True))
        
        if len(team1_players) >= 1:
            initial_data['team1_player1'] = team1_players[0]
        if len(team1_players) >= 2:
            initial_data['team1_player2'] = team1_players[1]
        if len(team2_players) >= 1:
            initial_data['team2_player1'] = team2_players[0]
        if len(team2_players) >= 2:
            initial_data['team2_player2'] = team2_players[1]
        
        form = MatchForm(league=league, instance=match, initial=initial_data)
    
    context = {
        'league': league,
        'match': match,
        'form': form,
    }
    return render(request, 'leagues/edit_match.html', context)

@login_required
def delete_match(request, league_id, match_id):
    """Vista per eliminare una partita"""
    league = get_object_or_404(League, id=league_id)
    match = get_object_or_404(Match, id=match_id, league=league)
    
    # Verifica che l'utente sia il presidente della lega
    if not request.user.is_league_president(league):
        return HttpResponseForbidden("Solo il presidente può eliminare partite")
    
    if request.method == 'POST':
        match.delete()
        messages.success(request, 'Partita eliminata con successo!')
        return redirect('leagues:detail', league_id=league.id)
    
    context = {
        'league': league,
        'match': match,
    }
    return render(request, 'leagues/delete_match.html', context)