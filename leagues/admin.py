from django.contrib import admin
from .models import League, Membership, Match, MatchPlayer

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1

class MatchPlayerInline(admin.TabularInline):
    model = MatchPlayer
    extra = 4
    max_num = 4

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'president', 'join_code', 'created_at')
    search_fields = ('name', 'president__username')
    inlines = [MembershipInline]

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('player', 'league', 'joined_at')
    list_filter = ('league',)
    search_fields = ('player__username', 'league__name')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'league', 'match_date', 'team1_sets', 'team2_sets')
    list_filter = ('league', 'match_date')
    date_hierarchy = 'match_date'
    inlines = [MatchPlayerInline]

@admin.register(MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = ('player', 'match', 'get_team_display')
    list_filter = ('team', 'match__league')
    search_fields = ('player__username',)