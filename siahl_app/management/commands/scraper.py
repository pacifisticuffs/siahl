from django.core.management.base import BaseCommand
from siahl_app.models import Team, Division, Season, Player, PlayerStat

import requests
import lxml
from lxml import html
import time, datetime


class Command(BaseCommand):
  help = 'Scrapes the SIAHL site'
  DIVISION_NAME = ''
  DIVISION_ID = 0
  TEAM = ''
  SERVER = 'http://stats.liahl.org/'

  def handle(self, *args, **options):
    self.stdout.write('Scraping started at %s' % str(datetime.datetime.now()))

    url = SERVER + 'display-stats.php?league=1'

    self.stdout.write('Scraping url: %s\n' % url)
    r = requests.get(url)
    root = lxml.html.fromstring(r.content)
    cells = root.cssselect('tr')

    for cell in cells:
      division = cell.cssselect('th')
      team = cell.cssselect('td a')
      if division and len(division) == 1:
        division = division[0].text_content().strip()

        # this is a division name
        if 'Senior' in division:
          DIVISION_NAME = division
          self.stdout.write('\nFound division: %s' % division)
          DIVISION_ID = self.add_division(division)

      # this should be a team
      elif team and len(team) == 1 and team[0].get('href') and DIVISION_ID:
        detail = team[0].get('href')
        team = team[0].text_content().strip()
        self.stdout.write('\nFound %s in %s (%s) at %s' % (team, DIVISION_NAME, DIVISION_ID, detail))
        TEAM = self.add_team(team, DIVISION_ID)
        self.get_details(detail, TEAM)


  def get_details(self, url, team):
    self.stdout.write('Scraping team details: %s' % url)
    r = requests.get(url)
    root = lxml.html.fromstring(r.content)
    tables = root.cssselect('table')
    goalie = False

    if (not tables) or (len(tables) == 1):
      self.stdout.write('No player info available for team %s' % team)
      return False
    else:
      for table in tables:
        rows = table.cssselect('tr')
        if rows:
          row = rows[0]
          txt = row.text_content().strip()
          if txt == 'Game Results':
            self.stdout.write('Skipping game table')
            continue
          if txt == 'Goalie Stats':
            self.stdout.write('Found goalies')
            goalie = True
          else:
            self.stdout.write('Found players')

          # This contains the column headers for our stats blob
          blob = self.get_headers(rows[1])
          self.stdout.write('Stats struct looks like %s' % blob)

          for playerRow in rows[2:]:
            cells = playerRow.cssselect('td')
            name = cells[0]
            iterator = 1
            # populate player's stats
            for key in blob:
              blob[key] = cells[iterator].text_content().strip()
              iterator++

            player = self.add_player(name, goalie)
            self.add_player_stats(player, team, blob)


  def get_headers(self, headers):
    blob = {}
    # First column header is "Name", which we don't want
    for header in headers[1:]:
      headerName = header.text_content().strip()
      blob[headerName] = ''

    return blob


  def add_team(self, team, division_id):
    self.stdout.write('Checking team %s in division_id %s.' % (team, division_id))
    returnVal = Team.objects.filter(team_name__iexact=team, division_id=division_id)

    if not returnVal:
      self.stdout.write("It's new! Adding.")
      t = Team(team_name=team, division_id=division_id)
      t.save()
      returnVal = Team.objects.latest('id').id
      self.stdout.write(' ... saved to db, id=%s' % returnVal)
    else:
      returnVal = returnVal[0].id
      self.skip()

    return returnVal


  def add_division(self, division):
    self.stdout.write('Checking division %s.' % division)
    returnVal = Division.objects.filter(division_name__iexact=division)

    if not returnVal:
      self.stdout.write("It's new! Adding.")
      d = Division(division_name=division)
      d.save()
      returnVal = Division.objects.latest('id').id
      self.stdout.write(' ... saved to db, id=%s' % returnVal)
    else:
      returnVal = returnVal[0].id
      self.skip()

    return returnVal


  def add_player_stats(self, player, team, stats):
    self.stdout.write('Checking player stats for %s on %s.' % (player,team))
    returnVal = PlayerStat.objects.filter(player_id=player, team_id=team)

    if not returnVal:
      self.stdout.write('New player stat, adding')
      ps = PlayerStat(player_id=player, team_id=team, stats=stats)
      ps.save()
      returnVal = PlayerStat.objects.latest('id').id
      self.stdout.write(' ... saved to db, id=%s' % returnVal)
    else:
      self.stdout.write('Existing player stat, updating')


  def add_player(self, player, goalie):
    self.stdout.write('Checking player %s (goalie=%s).' % (player,goalie))
    returnVal = Player.objects.filter(player_name__iexact=player, goalie=goalie)

    if not returnVal:
      self.stdout.write('New player, adding')
      p = Player(player_name=player, goalie=goalie)
      p.save()
      returnVal = Player.objects.latest('id').id
      self.stdout.write(' ... saved to db, id=%s' % returnVal)
    else:
      returnVal = returnVal[0].id
      self.skip()

    return returnVal


  def skip(self):
    self.stdout.write('Already found in db')

