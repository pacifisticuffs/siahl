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
  # SERVER = 'http://stats.liahl.org/'

  SERVER = 'http://localhost/data/'

  def handle(self, *args, **options):
    self.stdout.write('Scraping started at %s' % str(datetime.datetime.now()))

    # url = SERVER + 'display-stats.php?league=1'
    url = self.SERVER + 'display-stats.php.html'

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


          for playerRow in rows[2:]:
            cells = playerRow.cssselect('td')
            name = cells[0].text_content().strip()

            # populate the player's stats
            if goalie:
              stats = {
                'number'  : cells[1].text_content().strip(),
                'gp'      : cells[2].text_content().strip(),
                'goals'   : cells[3].text_content().strip(),
                'assists' : cells[4].text_content().strip(),
                'shots'   : cells[5].text_content().strip(),
                'ga'      : cells[6].text_content().strip(),
                'gaa'     : cells[7].text_content().strip(),
                'save_p'  : cells[8].text_content().strip(),
                'ppg'     : 0,
                'ppa'     : 0,
                'shg'     : 0,
                'sha'     : 0,
                'gwg'     : 0,
                'gwa'     : 0,
                'psg'     : 0,
                'eng'     : 0,
                'sog'     : 0,
                'pts'     : 0
              }
            else:
              stats = {
                'number'  : cells[1].text_content().strip(),
                'gp'      : cells[2].text_content().strip(),
                'goals'   : cells[3].text_content().strip(),
                'assists' : cells[4].text_content().strip(),
                'ppg'     : cells[5].text_content().strip(),
                'ppa'     : cells[6].text_content().strip(),
                'shg'     : cells[7].text_content().strip(),
                'sha'     : cells[8].text_content().strip(),
                'gwg'     : cells[9].text_content().strip(),
                'gwa'     : cells[10].text_content().strip(),
                'psg'     : cells[11].text_content().strip(),
                'eng'     : cells[12].text_content().strip(),
                'sog'     : cells[13].text_content().strip(),
                'pts'     : cells[14].text_content().strip(),
                'ga'      : 0,
                'gaa'     : 0,
                'save_p'  : 0
              }

            player = self.add_player(name, goalie)
            self.add_player_stats(player, team, stats)


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
      # we'll update the stats below
      ps = PlayerStat(player_id=player, team_id=team)
      ps.save()
      returnVal = PlayerStat.objects.latest('id')
      self.stdout.write(' ... saved to db, id=%s' % returnVal)

    self.stdout.write('Updating stats for player %s' % returnVal)
    returnVal.number  = stats['number']
    returnVal.gp      = stats['gp']
    returnVal.goals   = stats['goals']
    returnVal.assists = stats['assists']
    returnVal.ppg     = stats['ppg']
    returnVal.ppa     = stats['ppa']
    returnVal.shg     = stats['shg']
    returnVal.sha     = stats['sha']
    returnVal.gwg     = stats['gwg']
    returnVal.gwa     = stats['gwa']
    returnVal.psg     = stats['psg']
    returnVal.eng     = stats['eng']
    returnVal.sog     = stats['sog']
    returnVal.pts     = stats['pts']
    returnVal.ga      = stats['ga']
    returnVal.gaa     = stats['gaa']
    returnVal.save_p  = stats['save_p']
    returnVal.save()

    return returnVal.id


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

