"""
I hate this code. Hate it.
These logs are disgusting.
You try tracking the money.
I dare you.
"""


import argparse
import csv
import json
import os
import sys

from tornado.httpclient import AsyncHTTPClient

from utils import Utils


USERS = {}
HANDS = {}
HAND_NO = 0


class LogParser(object):
   def __init__(self, game_id):
      self.GAME_ID = game_id
      self.FILE = 'logs/%s.csv' % self.GAME_ID
      self.http_client = AsyncHTTPClient

   @property
   def hands(self):
      return HANDS


   async def parse_file(self):
      ## Different States and Variables
      # Want this thing to be kinda tidy
      START = 'start'
      END = 'end'
      BET = 'bet'
      PREFLOP = 'preflop'
      FLOP = 'flop'
      TURN = 'turn'
      RIVER = 'river'
      HAND = 'hand'
      SHOW = 'show'
      JOIN = 'join'
      QUIT = 'quit'
      CREATE = 'create'
      STAND = 'stand'
      SIT = 'sit'
      WARNING = 'warning'
      UPDATE = 'update'
      APPROVE = 'approve'
      ADMIN_SHIFT = 'admin_shift'

      CHECK = 'check'
      CALL = 'call'
      RAISE = 'raise'
      RAISE_ALL_IN = 'raise_all_in'
      CALL_ALL_IN = 'call_all_in'
      FOLD = 'fold'
      GAIN = 'gain'
      WIN = 'win'
      SMALL_BLIND = 'small_blind'
      BIG_BLIND = 'big_blind'
      MISSING_SMALL_BLIND = 'missing_small_blind'
      MISSING_BIG_BLIND = 'missing_big_blind'

      STATE = CREATE
      HAND_STATE = PREFLOP
      HAND_NO = 0


      def find_user(row):
         index_start = row.find('\"')
         if index_start == -1:
            return None, None
         index_end = row[index_start+1:].find('\"') + 1
         user_string = row[index_start + 1:index_start + index_end]
         username = user_string[0:user_string.find(' @ ')]
         user_id = user_string[user_string.find(' @ ')+3:]
         return (username, user_id)

      def parse_create(action):
         username, user_id = find_user(action)
         if not username or not user_id:
            raise Exception('OH OH')
         stack_size = int(action.split(' ')[-1][:-1])
         USERS[username] = {
            'starting_stack': stack_size,
            'current_stack': stack_size,
            'hands': {},
         }

      def parse_approve_join(action):
         username, user_id = find_user(action)
         stack_size = int(action.split(' ')[-1][:-1])
         if USERS.get(username):
            if stack_size != USERS[username]['current_stack']:
               USERS[username]['top_up'] = (
                  stack_size - USERS[username]['current_stack'])
               USERS[username]['current_stack'] = stack_size
            return
         USERS[username] = {
            'starting_stack': stack_size,
            'current_stack': stack_size,
            'hands': {},
         }

      def parse_update_stack(action):
         # username, user_id = find_user(action)
         # new_stack = int(action.split(' ')[-1][:-1])
         # top_up_amount = new_stack - USERS[username]['current_stack']
         # if USERS[username].get('top_up'):
         #    USERS[username]['top_up'] += top_up_amount
         # else:
         #    USERS[username]['top_up'] = top_up_amount
         # USERS[username]['current_stack'] = new_stack
         pass

      def parse_start(action):
         hand_no_start = action.find('starting hand #') + 15
         hand_no_end = action.find('(dealer') - 1
         if hand_no_end == -2:
            # Dead button, no dealer
            hand_no_end = action.find('(dead button') - 1
         hand_no = int(action[hand_no_start:hand_no_end])
         dealer = find_user(action)
         HANDS[hand_no] = {'dealer': dealer[0]}
         return hand_no

      def parse_bet(action, hand_no, hand_state):
         username, user_id = find_user(action)

         if action.find('posts a small blind') != -1:
            bet = SMALL_BLIND
            HANDS[hand_no][PREFLOP] = {'bets': []}
            hand_state = PREFLOP
         elif action.find('posts a big blind') != -1:
            bet = BIG_BLIND
         elif action.find('posts a missing small blind') != -1:
            bet = MISSING_SMALL_BLIND
         elif action.find('posts a missed big blind') != -1:
            bet = MISSING_BIG_BLIND
         elif action.find('calls with') != -1:
            bet = CALL
         elif action.find('raises with') != -1:
            bet = RAISE
         elif action.find('raises and all in') != -1:
            bet = RAISE_ALL_IN
         elif action.find('calls and all in') != -1:
            bet = CALL_ALL_IN
         elif action.find('checks') != -1:
            bet = CHECK
            bet_amount = 0
         elif action.find('folds') != -1:
            bet = FOLD
            bet_amount = 0
         elif action.find('gained ') != -1:
            bet = GAIN
         elif action.find('wins ') != -1:
            # Could be shared pot ffs
            bet = WIN
            bet_amount = int(action.split('wins ')[1].split(' ')[0])
         else:
            print(action)
            raise Exception('what')

         if bet not in (FOLD, CHECK, WIN):
            bet_amount = int(action.split(' ')[-1])
         if bet in (WIN, GAIN):
            # GAIN states total chips received - final bet
            # WIN states total chips received
            # FFS

            if not HANDS[hand_no].get('winner'):
               # not a split pot
               HANDS[hand_no]['winner'] = {
                  "player": [username],
                  "amount": [bet_amount],
                  "type": bet
               }
            else:
               try:
                  HANDS[hand_no]['winner']['player'] += [username]
                  HANDS[hand_no]['winner']['amount'] += [bet_amount]
               except Exception as e:
                  print('OH NO')
                  print(HANDS[hand_no]['winner'])
                  print(action)
                  print(bet)
                  print(username)
                  print(e)
                  raise Exception
            bet_amount = 0

         try:
            HANDS[hand_no][hand_state]['bets'] += [{
               'action': bet,
               'amount': bet_amount,
               'player': username
            }]
            if not HANDS[hand_no][hand_state].get('pot_contributions'):
               HANDS[hand_no][hand_state]['pot_contributions'] = {}
            if bet_amount:
               # Still need to get winner's pot contribution
               HANDS[hand_no][hand_state]['pot_contributions'][username] = bet_amount
         except Exception as e:
            print(HANDS)
            print(action)
            print(bet)
            print(hand_state)
            print(e)
            raise Exception
         return hand_state

      def parse_show_hand(action, hand_no):
         username, user_id = find_user(action)
         hand = [card_str[:-1] for card_str in action.split(' ')[-2:]]
         if not HANDS[hand_no].get('player_cards'):
            HANDS[hand_no]['player_cards'] = {}
         HANDS[hand_no]['player_cards'][username] = hand

      def parse_flop(action, hand_no):
         cards_string = action[6:]
         cards = cards_string.split(', ')
         HANDS[hand_no]['cards'] = cards
         HANDS[hand_no][FLOP] = {'bets': []}

      def parse_turn(action, hand_no):
         cards_string = action[-2:]
         HANDS[hand_no]['cards'] += [cards_string]
         HANDS[hand_no][TURN] = {'bets': []}

      def parse_river(action, hand_no):
         cards_string = action[-2:]
         HANDS[hand_no]['cards'] += [cards_string]
         HANDS[hand_no][RIVER] = {'bets': []}

      def calculate_start_stacks(hand_no):
         if hand_no == 1:
            # Haven't played any hands yet, use starting_stacks
            for player in USERS:
               USERS[player]['hands'][hand_no] = {
                  "starting_stack": USERS[player]['starting_stack']
               }
            return

         for player in USERS:
            USERS[player]['hands'][hand_no] = {
                  "starting_stack": USERS[player]['current_stack']
            }

      def calculate_end_stacks(hand_no):
         if not HANDS[hand_no].get('winner'):
            # Folded all around find big blind
            for bet in HANDS[hand_no]['preflop']['bets']:
               if bet['action'] == 'big_blind':
                  winner = bet['player']
                  big_blind_amount = bet['amount']
               if bet['action'] == 'small_blind':
                  small_blind_amount = bet['amount']
            HANDS[hand_no]['winner'] = {
               'player': [winner],
               'amount': [small_blind_amount+big_blind_amount],
               'type': 'Fold_around'
            }


         for player in USERS:
            try:
               loss = 0
               winner_gain_checked = False
               for key in reversed([PREFLOP,FLOP,TURN,RIVER]):
                  if key in HANDS[hand_no].keys():
                     for contributor, amount in HANDS[hand_no][key].get('pot_contributions', {}).items():
                        if contributor == player:
                           if (player in HANDS[hand_no]['winner']['player'] and
                              HANDS[hand_no]['winner']['type'] == GAIN and
                              not winner_gain_checked):
                                 winner_gain_checked = True
                                 player_index = HANDS[hand_no]['winner']['player'].index(player)
                                 HANDS[hand_no]['winner']['amount'][player_index] += amount

                           loss += amount

            except:
               print(hand_no)
               print(key)
               print(HANDS[hand_no])
               raise Exception

            ending_stack = USERS[player]['current_stack']
            if player in HANDS[hand_no]['winner']['player']:
               player_index = HANDS[hand_no]['winner']['player'].index(player)
               ending_stack += HANDS[hand_no]['winner']['amount'][player_index]
            ending_stack -= loss
            if USERS[player]['hands'].get(hand_no):
               # If joined late will not have hand
               USERS[player]['hands'][hand_no]['ending_stack'] = ending_stack
               USERS[player]['current_stack'] = ending_stack

      def find_type(row):
         if row.startswith('-- starting'):
            return START
         if row.startswith('-- ending'):
            return END
         if row.startswith('Your hand'):
            return HAND
         if row.startswith('flop:'):
            return FLOP
         if row.startswith('turn:'):
            return TURN
         if row.startswith('river:'):
            return RIVER
         if row.startswith('\"'):
            if row.find('shows a ') != -1:
               return SHOW
            else:
               return BET
         if row.startswith('The player'):
            if row.find('created the game') != -1:
               return CREATE
            if row.find('joined the game') != -1:
               return JOIN
            if row.find('quits the game') != -1:
               return QUIT
            if row.find('stand up with') != -1:
               return STAND
            if row.find('sit back with') != -1:
               return SIT
         if row.startswith('The admin'):
            if row.startswith('The admin updated the player'):
               return UPDATE
            if row.startswith('The admin approved the player'):
               return APPROVE
         if row.find('passed the room ownership') != -1:
            return ADMIN_SHIFT
         if row.startswith('WARNING:'):
            return WARNING
         print('MISSING STATE')
         print(row)
         raise Exception('MISSING')

      with open(self.FILE, 'r') as csvfile:
         poker_entries = csv.reader(csvfile, delimiter=',', quotechar='"')
         for row in reversed(list(poker_entries)):
            action = row[0]
            time = row[1]


            STATE = find_type(action)
            if STATE == CREATE:
               parse_create(action)
            if STATE == APPROVE:
               parse_approve_join(action)
            if STATE == UPDATE:
               parse_update_stack(action)
            if STATE == START:
               HAND_NO = parse_start(action)
               calculate_start_stacks(HAND_NO)
            if STATE == END:
               calculate_end_stacks(HAND_NO)
            if STATE == SHOW:
               parse_show_hand(action, HAND_NO)
            if STATE == BET:
               HAND_STATE = parse_bet(action, HAND_NO, HAND_STATE)
            if STATE == FLOP:
               HAND_STATE = FLOP
               parse_flop(action, HAND_NO)
            if STATE == TURN:
               HAND_STATE = TURN
               parse_turn(action, HAND_NO)
            if STATE == RIVER:
               HAND_STATE = RIVER
               parse_river(action, HAND_NO)

      # with open('output_users.json', 'w') as f:
      #    json.dump(USERS, f, indent=4)
      Utils.write_file('hands/%s.json' % self.GAME_ID,
                       json.dumps(HANDS, indent=4))



if __name__ == "__main__":
   parser = argparse.ArgumentParser(
      description='Parse PokerNow Log Files')
   parser.add_argument(
      '-f', '--file', type=str, help='PokerNow log file location',
      default='20.05.20.csv')
   parser.add_argument(
      '-g', '--game-id', type=str, help='Game Id',
      default='20.05.20.csv')
   args = parser.parse_args()
   if not args.file and sys.stdin.isatty():
      parser.print_help()
      sys.exit(1)

   log_parser = LogParser(args.game_id)
   log_parser.parse_file()

   print('DONE')
   print('HANDS PLAYED: %s' % len(HANDS.keys()))