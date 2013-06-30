from django.db import models

# Each season has a name, an id and should be linked to provide
# historical data
class Season(models.Model):
  season_name = models.CharField(max_length=255)
  siahl_id = models.IntegerField(null=True, blank=True)

# All the division names (A, AA, DDDD, etc.)
class Division(models.Model):
  division_name = models.CharField(max_length=255)

  def __unicode__(self):
    return u'%s' % self.division_name


# Each team belonds to a particular division
class Team(models.Model):
  team_name = models.CharField(max_length=255)
  division = models.ForeignKey(Division)

  def __unicode__(self):
    return u'%s (%s)' % (self.team_name, self.division)


# Players can play on many different teams, and teams have many players.
# In reality with this dataset, we're using the player's name as the
# unique id, since usa hockey numbers aren't available (and they change
# every year)
class Player(models.Model):
  player_name = models.CharField(max_length=255)
  teams = models.ManyToManyField(Team, through='PlayerStat')
  goalie = models.BooleanField(default=False)

  def __unicode__(self):
    return u'%s (%s)' % (self.player_name, self.teams)


# Each player will have separate stats for every team they play on
# Opted to create separate columns for each stat instead of a json
# blob so that we can order and query based on these
class PlayerStat(models.Model):
  player  = models.ForeignKey(Player)
  team    = models.ForeignKey(Team)
  number  = models.IntegerField(null=True, blank=True, default=0)
  gp      = models.IntegerField(null=True, blank=True, default=0)
  goals   = models.IntegerField(null=True, blank=True, default=0)
  assists = models.IntegerField(null=True, blank=True, default=0)
  ppg     = models.IntegerField(null=True, blank=True, default=0)
  ppa     = models.IntegerField(null=True, blank=True, default=0)
  shg     = models.IntegerField(null=True, blank=True, default=0)
  sha     = models.IntegerField(null=True, blank=True, default=0)
  gwg     = models.IntegerField(null=True, blank=True, default=0)
  gwa     = models.IntegerField(null=True, blank=True, default=0)
  psg     = models.IntegerField(null=True, blank=True, default=0)
  eng     = models.IntegerField(null=True, blank=True, default=0)
  sog     = models.IntegerField(null=True, blank=True, default=0)
  pts     = models.IntegerField(null=True, blank=True, default=0)

  # goalie stats
  shots   = models.IntegerField(null=True, blank=True, default=0)
  ga      = models.IntegerField(null=True, blank=True, default=0)
  gaa     = models.IntegerField(null=True, blank=True, default=0)
  save_p  = models.IntegerField(null=True, blank=True, default=0)


  def __unicode__(self):
    return u'%s on %s' % (self.player.player_name, self.team.team_name)
