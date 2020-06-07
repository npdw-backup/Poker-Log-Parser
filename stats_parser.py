import argparse
import csv
import json
import os
import sys

from utils import Utils
from stats import (VPIP, ThreeBet, FourBet, AF, AFq, BetF, BetT, BetR, CvFCB,
                   FDONK, FDONK10, PFR)


class StatsParser(object):
   STAT_CLASSES = [VPIP, PFR, ThreeBet, FourBet, AF, AFq, BetF, BetT, BetR,
                   CvFCB, FDONK, FDONK10]

   def __init__(self, game_id, single=True, game_ids={}, filename=None):
      self.game_id = game_id
      self.stats_filename = 'stats/%s.csv' % self.game_id
      self.json_filename = 'hands/%s.json' % self.game_id
      self.stats = {}
      self.data = {}
      self.num_denom = {}

      if not os.path.isdir('stats'):
         os.mkdir('stats')


   def parse(self):
      for stat_cls in self.STAT_CLASSES:
         stat = stat_cls(self.data)
         stat.calculate()
         self.stats[stat.__name__] = stat.output()
         self.num_denom[stat.__name__] = stat.num_denom()

      f = csv.writer(open(self.stats_filename, "w"))
      names = list(self.num_denom[self.STAT_CLASSES[0].__name__].keys())
      f.writerow(['Stats'] + names)
      for stat_name, stats in self.num_denom.items():
         row = [stat_name]
         for name in names:
            stat = stats.get(name)
            if stat and stat[1]!= 0:
               row += ['%s/%s' % (stat[0], stat[1])]
            else:
               row += ['0']
         f.writerow(row)

   def parse_file(self):
      unsorted_data = json.loads(Utils.read_file(self.json_filename))
      for hand_no, hand in unsorted_data.items():
         if hand.get('winner', {}).get('amount'):
            self.data[hand_no] = hand

      self.parse()


def main(args):
   FILE = args.file
   GAME_ID = ''.join(FILE.split('.')[-1])

   parser = StatsParser(GAME_ID)
   parser.filename = FILE
   parser.parse_file()



if __name__ == "__main__":
   parser = argparse.ArgumentParser(
      description='Parse PokerNow Log Files')
   parser.add_argument(
      '-f', '--file', type=str, help='PokerNow log file location',
      default='output_hands.json')
   args = parser.parse_args()
   if not args.file and sys.stdin.isatty():
      parser.print_help()
      sys.exit(1)

   main(args)