from django.template import Template, Context
from django.http import HttpResponse
from django.shortcuts import render
from siahl_app import models
from django.db.models import Count, Sum, Avg, Max

def index(request):
  players = models.PlayerStat.objects.raw('''
    select *, (goals / gp) as ratio
    from siahl_app_playerstat
    where gp > 3
    order by ratio desc
    limit 10
  ''')

  rats = models.PlayerStat.objects.raw('''
    SELECT *, COUNT(`siahl_app_playerstat`.`player_id`) AS `count`
    FROM `siahl_app_playerstat`
    INNER JOIN siahl_app_player ON (siahl_app_playerstat.player_id = siahl_app_player.id)
    WHERE siahl_app_player.goalie=False
    GROUP BY `siahl_app_playerstat`.`player_id`
    HAVING COUNT(`siahl_app_playerstat`.`player_id`) > 4
    ORDER BY count desc
  ''')

  return render(request, 'index.html', { 'players' : players, 'rats' : rats })

def rinkrats(request):
  players = models.PlayerStat.objects.raw('''
    SELECT *, COUNT(`siahl_app_playerstat`.`player_id`) AS `count`
    FROM `siahl_app_playerstat`
    INNER JOIN siahl_app_player ON (siahl_app_playerstat.player_id = siahl_app_player.id)
    WHERE siahl_app_player.goalie=False
    GROUP BY `siahl_app_playerstat`.`player_id`
    HAVING COUNT(`siahl_app_playerstat`.`player_id`) > 4
    ORDER BY count desc
  ''')

  return render(request, 'rinkrats.html', { 'players' : players})

