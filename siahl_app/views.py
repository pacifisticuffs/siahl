from django.template import Template, Context
from django.http import HttpResponse
from django.shortcuts import render
from siahl_app import models

def index(request):
  players = models.PlayerStat.objects.raw('''
    select *, (goals / gp) as ratio
    from siahl_app_playerstat
    where gp > 3
    order by ratio desc
    limit 10
  ''')

  return render(request, 'index.html', { 'players' : players })
