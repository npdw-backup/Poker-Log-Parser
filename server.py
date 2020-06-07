"""
PokerNow Logs Web Based
Currently static because effort.
"""
import argparse
import concurrent
import concurrent.futures
import csv
import fractions
import json
import logging
import os

import tornado
import tornado.web
from  tornado import template

from game_tracker import GameTracker
from log_parser import LogParser
from stats_parser import StatsParser
from utils import Utils


log = logging.getLogger('poker_track')

parser = argparse.ArgumentParser(description='Poker Now Server Log Tracker.')
parser.add_argument('-p', '--port', type=int, default=None,
                  help='Port to listen on. Default: 80 / 443')
parser.add_argument('-g', '--game-id', type=str, default='2VQEY-Vn6ggeXBtg7mUkXY_Dd',
                  help='Game Id')
cmd_args = parser.parse_args()


GAME_ID = '200520-dontknowgameid'

# This is so bad. Not even in a csv, mixing quotation marks. Eugh. Hate it
GAME_IDS = {
   # "29.05": {
   #    'id': 'BDs_ea39TgqKJ39DZC5CQjeRh',
   #    'live': False
   # },
   "23.05.20": {
      'id': 'YiGSaUBmpPnB2pB8prARt-QhR',
      'live': False
   },
   "20.05.20": {
      'id': '200520-dontknowgameid',
      'live': False
   }
}

GAME_IDS_LIST = []
for game, data in GAME_IDS.items():
   GAME_IDS_LIST.append(data['id'])



class GameManager(object):
   stats = None
   num_denom = None
   hands = {}
   latest = 0

   def __init__(self, game_id, live):
      self.live = live
      if not live:
         self.hands = {0: {}}
      stats_file = 'stats/%s.csv' % game_id
      if os.path.isfile(stats_file):
         with open(stats_file, 'r') as f:
            data = f.read()
            # print(data)
            self.stats, self.num_denom = self.parse_stats_file(data)

   def parse_stats_file(self, data):
      users = data.split('\n')[0].split(',')[1:]
      stats = data.split('\n')[1:]
      total_stats = {}
      total_stats_fraction = {}
      for stat in stats:
         if not stat:
            continue
         stat = stat.split(',')
         total_stats[stat[0]] = {}
         total_stats_fraction[stat[0]] = {}
         for idx, user in enumerate(users):
            stat_fraction = stat[idx+1] or '0'
            total_stats[stat[0]][user] = float(fractions.Fraction(stat_fraction))
            total_stats_fraction[stat[0]][user] = stat_fraction
      return total_stats, total_stats_fraction

   def overall_stats(self, formatted_stats):
      # Add overall stats
      formatted_stats['details']['hands_played'] = {
         "title": "Hands Played",
         "sub_title": "Current Session",
         "value": len(self.hands)
      }

      total_players = set()
      for stat_name, stat in self.stats.items():
         for player in stat:
            if player not in total_players:
               total_players.add(player)

      # Add overall stats
      formatted_stats['details']['players_tracked'] = {
         "title": "Players Tracked",
         "sub_title": "Current Session",
         "value": len(total_players)
      }

      return formatted_stats


   def get_formatted(self, dec_places=4):
      formatted_stats = {"stats": {}, "details": {}}

      # Rounding
      for stat_name, stat in self.stats.items():
         formatted_stats['stats'][stat_name] = {"values": {}}

         for name, val in stat.items():
            try:
               formatted_stats['stats'][stat_name]['values'][name] = round(val, dec_places)
            except:
               print('OH NO')
               print(dec_places)
               raise Exception

      # Add docstring
      for stat in StatsParser.STAT_CLASSES:
         stat_class = stat({})
         formatted_stats['stats'][stat_class.__name__]['desc'] = stat_class.__doc__

      # Add overall game stats
      formatted_stats = self.overall_stats(formatted_stats)

      # Add latest log_id for ajax
      formatted_stats['latest'] = max(self.hands.keys() or [1])

      return formatted_stats



game_manager = GameManager(GAME_ID, live=True)
total_game_manager = GameManager('total', live=False)
total_game_manager.hands = {1:{}}

for game, data in GAME_IDS.items():
   GAME_IDS[game]['game_manager'] = GameManager(data['id'], False)



class PastGameHandler(tornado.web.RequestHandler):
   """Simplest Hello World handler"""
   async def get(self, game_id):
      if not game_id in GAME_IDS.keys():
         self.write('Game does not exist. Apologies')
         self.finish()
         return

      if GAME_IDS[game_id]['game_manager']:
         past_game_manager = GAME_IDS[game_id]['game_manager']
      else:
         self.write('Game does not exist. Apologies')
         self.finish()
         return

      if past_game_manager.stats:
         loader = template.Loader("templates")
         formatted_stats = past_game_manager.get_formatted()
         self.write(loader.load("base2.html").generate(stats=formatted_stats, live=False))

      else:
         self.write('Nothing yet, stay calm Dan')


class TotalGameHandler(tornado.web.RequestHandler):
   """Simplest Hello World handler"""
   def compile_stats(self):
      total_stats = {}
      final_stats = {}
      game_manager_list = [game_manager]
      for game , game_data in GAME_IDS.items():
         game_manager_list.append(game_data['game_manager'])
      # print(game_manager_list)
      for game_num_denum in game_manager_list:
         for stat, stat_vals in game_num_denum.num_denom.items():
            if not stat in total_stats:
               total_stats[stat] = {}

            for user, user_val in stat_vals.items():
               if type(user_val) == str:
                  user_val = user_val.split('/')

               if not user in total_stats:
                  total_stats[stat][user] = [0,0]
               try:
                  total_stats[stat][user][0] += int(user_val[0])
                  total_stats[stat][user][1] += int(user_val[1])
               except:
                  print(total_stats[stat][user])
                  print(user_val)
                  raise

      for stat, users in total_stats.items():
         final_stats[stat] = {}
         for user, val in users.items():
            try:
               final_stats[stat][user] = float(val[0]/val[1])
            except:
               final_stats[stat][user] = 0

      return final_stats

   async def get(self):
      total_stats = self.compile_stats()
      total_game_manager.stats = total_stats
      total_game_manager.hands = game_manager.hands
      loader = template.Loader("templates")
      formatted_stats = total_game_manager.get_formatted()
      self.write(loader.load("base2.html").generate(stats=formatted_stats, live=True))


class SingleGameHandler(tornado.web.RequestHandler):
   """Simplest Hello World handler"""
   async def get(self):
      if game_manager.stats:
         loader = template.Loader("templates")
         formatted_stats = game_manager.get_formatted()
         self.write(loader.load("base2.html").generate(stats=formatted_stats, live=True))

      else:
         self.write('Nothing yet, stay calm Dan')


class UpdateStatsHandler(tornado.web.RequestHandler):
   """Checks for new stats available"""
   async def post(self):
      client_latest = int(self.request.arguments.get('latest')[0])
      if game_manager.hands.keys() and client_latest != max(game_manager.hands.keys()):
         self.write(json.dumps({'refresh': True}))
      else:
         self.write(json.dumps({'refresh': False}))
      self.finish()


class Server(object):
   def __init__(self, log, port):
      self.log = log
      self.app = self.make_app()
      self.app.listen(port=port)
      self.log.info('event="api-started"')

      self.ioloop = tornado.ioloop.IOLoop.current()
      pc = tornado.ioloop.PeriodicCallback(self.periodic_callback, 20 * 1000,
                                           jitter=0.1)
      pc.start()
      self.ioloop.add_callback(self.periodic_callback)
      self.ioloop.start()

   async def periodic_callback(self):
      """Update logs, internal json logs and stats"""
      self.log.info('event="calling-logs"')
      await self.app.game_tracker.listen()
      if self.app.game_tracker.updates:
      # if True:
         self.log.info('event="applying-updates"')
         await self.app.log_parser.parse_file()
         self.app.stats_parser.parse_file()
         global game_manager
         game_manager.stats = self.app.stats_parser.stats
         game_manager.hands = self.app.log_parser.hands
         game_manager.num_denom = self.app.stats_parser.num_denom

         # self.log.info('event="applying-updates-to-total"')
         # await self.app.total_log_parser.parse_file()
         # self.app.stats_parser.parse_file()
         # global total_game_manager
         # total_game_manager.stats = self.app.total_stats_parser.stats
         # total_game_manager.hands = self.app.total_log_parser.hands


      self.log.info('event="finished-calling-logs"')

   def make_app(self):
      app = tornado.web.Application([
         # Additional endpoints to test the service is up and running.
         (r"/stats/total", TotalGameHandler),
         (r"/stats", SingleGameHandler),
         (r"/stats/([^/]+)", PastGameHandler),
         (r"/update", UpdateStatsHandler)
      ])
      app.game_tracker = GameTracker(GAME_ID)
      app.stats_parser = StatsParser(GAME_ID) #, single=False, game_ids=GAME_IDS, filename="20.05-25.05")
      app.log_parser = LogParser(GAME_ID)

      return app


def main():
   log_format = 'time="%(asctime)-15s" level=%(levelname)-7s %(message)s'
   logging.basicConfig(
      level=logging.INFO,
      format=log_format)

   if not cmd_args.port:
      cmd_args.port = 80

   log.info('=' * 51)
   log.info('{:^51}'.format('Starting PokerNow Stats'))
   log.info(' '.join(['*'] * 25))

   for key, value in vars(cmd_args).items():
      log.info('{!s:>24s} = {!s:<24}'.format(key, value))

   log.info('=' * 51)

   log.info('event="api-starting"')


   server = Server(log=log, port=cmd_args.port)

   # app = server.make_app()
   # app.listen(cmd_args.port)
   # log.info('event="api-started"')


   # tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
   main()