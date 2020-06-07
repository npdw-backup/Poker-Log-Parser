class BaseStats(object):
   __name__ = 'Stat'

   def __init__(self, data):
      self.data = data
      self.users = {}
      self.numerator = 0
      self.denominator = 0

   def small_blind(self, hand_no):
      if not self.data.get(hand_no):
         return (None, None)
      if not self.data[hand_no].get('preflop'):
         return (None, None)
      for bet in self.data[hand_no]['preflop']['bets']:
         if bet['action'] == 'small_blind':
            return (bet['player'], bet['amount'])
      return (None, None)

   def big_blind(self, hand_no):
      if not self.data.get(hand_no):
         return (None, None)
      if not self.data[hand_no].get('preflop'):
         return (None, None)
      for bet in self.data[hand_no]['preflop']['bets']:
         if bet['action'] == 'big_blind':
            return (bet['player'], bet['amount'])
      return (None, None)

   def cbet(self, hand_no):
      if not self.data.get(hand_no):
         return (None, None)
      if not self.data[hand_no].get('preflop') or not self.data[hand_no].get('flop'):
         return (None, None)

      big_blind = self.big_blind(hand_no)
      last_raise = (None, big_blind[1])
      for bet in self.data[hand_no]['preflop']['bets']:
         user = bet['player']
         action = bet['action']
         amount = bet['amount']

         if amount > last_raise[1]:
            last_raise = (user, amount)
      if not last_raise[0]:
         return (None, None)

      for bet in self.data[hand_no]['flop']['bets']:
         user = bet['player']
         action = bet['action']
         amount = bet['amount']
         if amount:
            if user == last_raise[0]:
               return (user, amount)
            else:
               return (None, None)

      return (None, None)

   def preflop_aggressor(self, hand_no):
      if not self.data.get(hand_no):
         return (None, None)
      if not self.data[hand_no].get('preflop'):
         return (None, None)

      big_blind = self.big_blind(hand_no)
      last_raise = (None, big_blind[1])
      for bet in self.data[hand_no]['preflop']['bets']:
         user = bet['player']
         action = bet['action']
         amount = bet['amount']

         if amount > last_raise[1]:
            last_raise = (user, amount)
      if not last_raise[0]:
         return (None, None)

      return last_raise

class VPIP(BaseStats):
   """
   Voluntarily placed cash in preflop. Does not count big blind contribution.


   """
   __name__ = 'VPIP'

   def __init__(self, data):
      super(VPIP, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         if not hand.get('preflop') or not hand['preflop'].get('pot_contributions'):
            continue
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         for bet in hand['preflop']['bets']:
            user = bet['player']
            action = bet['action']
            amount = bet['amount']
            if not self.users.get(user):
               self.users[user] = {
                  'hands_played': [],
                  'hands_volunteered': []
               }
            if hand_no in self.users[user]['hands_volunteered']:
               # Already counted this hand
               continue

            if hand_no not in self.users[user]['hands_played']:
               self.users[user]['hands_played'] += [hand_no]

            if action in ('small_blind', 'big_blind', 'missing_small_blind', 'missing_big_blind'):
               continue
            if user in hand['preflop']['pot_contributions']:
               if user == small_blind[0]:
                  if hand['preflop']['pot_contributions'][user] > small_blind[1]:
                     self.users[user]['hands_volunteered'] += [hand_no]
               elif user == big_blind[0]:
                  if hand['preflop']['pot_contributions'][user] > big_blind[1]:
                     self.users[user]['hands_volunteered'] += [hand_no]
               elif amount > 0:
                  self.users[user]['hands_volunteered'] += [hand_no]

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = float(len(hands['hands_volunteered'])) / float(len(hands['hands_played']))
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (len(hands['hands_volunteered']), len(hands['hands_played']))
      return output


class PFR(BaseStats):
   """PFR tracks the percentage of hands in which a particular player makes a
   preflop raise when having the opportunity to fold or call instead. This
   includes reraises.
   """
   __name__ = 'PFR'

   def __init__(self, data):
      super(PFR, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         current_bet_size = big_blind[1]
         for hand_stage in ['preflop']:
            if not hand.get(hand_stage) or not hand[hand_stage].get('bets'):
               continue

            for bet in hand[hand_stage]['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'raise': 0,
                     'not_raise': 0
                  }

               if action in ('small_blind', 'big_blind', 'missing_small_blind', 'missing_big_blind'):
                  continue

               if amount > current_bet_size:
                  self.users[user]['raise'] += 1
                  current_bet_size = amount
               else:
                  self.users[user]['not_raise'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['raise']) /
                              float(hands['raise']+hands['not_raise']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['raise'], hands['raise']+hands['not_raise'])
      return output


class ThreeBet(BaseStats):
   """
   Three Bet Preflop
   """
   __name__ = '3BET'

   def __init__(self, data):
      super(ThreeBet, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         if not hand.get('preflop') or not hand['preflop'].get('pot_contributions'):
            continue
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         three_bet = False
         bet_sizes = [big_blind[1]]
         for bet in hand['preflop']['bets']:
            user = bet['player']
            action = bet['action']
            amount = bet['amount']

            if not self.users.get(user):
               self.users[user] = {
                  'hands_played': [],
                  'hands_three_bet': []
               }
            if hand_no not in self.users[user]['hands_played']:
               self.users[user]['hands_played'] += [hand_no]

            if action in ('small_blind', 'big_blind', 'missing_small_blind', 'missing_big_blind'):
               continue
            if amount not in bet_sizes and amount > bet_sizes[-1]:
               bet_sizes += [amount]
            if len(bet_sizes) == 3 and not three_bet:
               self.users[user]['hands_three_bet'] += [hand_no]
               three_bet = True

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = float(len(hands['hands_three_bet'])) / float(len(hands['hands_played']))
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (len(hands['hands_three_bet']), len(hands['hands_played']))
      return output


class FourBet(BaseStats):
   """
   Four Bet Preflop
   """
   __name__ = '4BET'


   def __init__(self, data):
      super(FourBet, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         if not hand.get('preflop') or not hand['preflop'].get('pot_contributions'):
            continue
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         four_bet = False
         bet_sizes = [big_blind[1]]
         for bet in hand['preflop']['bets']:
            user = bet['player']
            action = bet['action']
            amount = bet['amount']

            if not self.users.get(user):
               self.users[user] = {
                  'hands_played': [],
                  'hands_four_bet': []
               }
            if hand_no not in self.users[user]['hands_played']:
               self.users[user]['hands_played'] += [hand_no]

            if action in ('small_blind', 'big_blind', 'missing_small_blind', 'missing_big_blind'):
               continue
            if amount not in bet_sizes and amount > bet_sizes[-1]:
               bet_sizes += [amount]
            if len(bet_sizes) == 4 and not four_bet:
               self.users[user]['hands_four_bet'] += [hand_no]
               four_bet = True

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = float(len(hands['hands_four_bet'])) / float(len(hands['hands_played']))
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (len(hands['hands_four_bet']), len(hands['hands_played']))
      return output


class AF(BaseStats):
   """Aggression factor. A ratio of how often a player takes an aggressive
   action vs a passive action. The formula is (bets + raises)/(calls+checks). A
   high number implies most of their actions are aggressive. This book only
   shows total AF, and not per street AF."""
   __name__ = 'AF'

   def __init__(self, data):
      super(AF, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         for hand_stage in ['preflop', 'flop', 'turn', 'river']:
            current_bet_size = big_blind[1] if hand_stage == 'preflop' else 0
            if not hand.get(hand_stage) or not hand[hand_stage].get('bets'):
               continue

            for bet in hand[hand_stage]['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'aggressive': 0,
                     'passive': 0
                  }
               if action in ('small_blind', 'big_blind', 'missing_small_blind', 'missing_big_blind'):
                  continue
               if amount == current_bet_size:
                  self.users[user]['passive'] += 1
               elif amount > current_bet_size:
                  self.users[user]['aggressive'] +=1
                  current_bet_size = amount

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = float(hands['aggressive']) / float(hands['passive'])
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['aggressive'], hands['passive'])
      return output


class AFq(BaseStats):
   """Aggression frequency. This is a percentage of non-checking postflop
   actions that were aggressive.  For example, an AFq of 60 means a player made
   a bet or raise 60% of the time he bet, raised, called, or folded. This book
   only shows total AFq, and not per street AFq."""
   __name__ = 'AFq'

   def __init__(self, data):
      super(AFq, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         for hand_stage in ['turn', 'river']:
            current_bet_size = big_blind[1] if hand_stage == 'preflop' else 0
            if not hand.get(hand_stage) or not hand[hand_stage].get('bets'):
               continue

            for bet in hand[hand_stage]['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'aggressive': 0,
                     'passive': 0
                  }
               if action in ('small_blind', 'big_blind', 'missing_small_blind', 'missing_big_blind'):
                  continue
               if amount > current_bet_size:
                  self.users[user]['aggressive'] += 1
                  current_bet_size = amount
               else:
                  self.users[user]['passive'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['aggressive']) /
                              float(hands['aggressive']+hands['passive']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['aggressive'], hands['aggressive']+hands['passive'])
      return output


class BetF(BaseStats):
   """How often a player bet the flop when given the opportunity.
   Only counts when bet, not call or check
   """
   __name__ = 'BET F'

   def __init__(self, data):
      super(BetF, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         current_bet_size = 0
         for hand_stage in ['flop']:
            if not hand.get(hand_stage) or not hand[hand_stage].get('bets'):
               continue

            for bet in hand[hand_stage]['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'bet': 0,
                     'not_bet': 0
                  }
               if amount > current_bet_size:
                  self.users[user]['bet'] += 1
                  current_bet_size = amount
               else:
                  self.users[user]['not_bet'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['bet']) /
                              float(hands['bet']+hands['not_bet']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['bet'], hands['bet']+hands['not_bet'])
      return output


class BetT(BaseStats):
   """How often a player bet the turn when given the opportunity.
   Only counts when bet, not call or check
   """
   __name__ = 'BET T'

   def __init__(self, data):
      super(BetT, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         current_bet_size = 0
         for hand_stage in ['turn']:
            if not hand.get(hand_stage) or not hand[hand_stage].get('bets'):
               continue

            for bet in hand[hand_stage]['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'bet': 0,
                     'not_bet': 0
                  }
               if amount > current_bet_size:
                  self.users[user]['bet'] += 1
                  current_bet_size = amount
               else:
                  self.users[user]['not_bet'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['bet']) /
                              float(hands['bet']+hands['not_bet']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['bet'], hands['bet']+hands['not_bet'])
      return output


class BetR(BaseStats):
   """How often a player bet the river when given the opportunity.
   Only counts when bet, not call or check
   """
   __name__ = 'BET R'

   def __init__(self, data):
      super(BetR, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         small_blind = self.small_blind(hand_no)
         big_blind = self.big_blind(hand_no)
         current_bet_size = 0
         for hand_stage in ['river']:
            if not hand.get(hand_stage) or not hand[hand_stage].get('bets'):
               continue

            for bet in hand[hand_stage]['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'bet': 0,
                     'not_bet': 0
                  }
               if amount > current_bet_size:
                  self.users[user]['bet'] += 1
                  current_bet_size = amount
               else:
                  self.users[user]['not_bet'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['bet']) /
                              float(hands['bet']+hands['not_bet']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['bet'], hands['bet']+hands['not_bet'])
      return output


class CvFCB(BaseStats):
   """How often a player calls a flop continuation bet (also see FCB).

   Only measure when someone calls/folds the initial cbet.
   If somebody raises the cbet, ignore all call/folds afterwards.
   """
   __name__ = 'CvFCB'

   def __init__(self, data):
      super(CvFCB, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         cbet = self.cbet(hand_no)
         if cbet and cbet[0]:
            for bet in hand['flop']['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'cbet': 0,
                     'call_cbet': 0,
                     'fold_cbet': 0
                  }

               if amount == cbet[1]:
                  if user != cbet[0]:
                     self.users[user]['call_cbet'] += 1
                  else:
                     self.users[user]['cbet'] += 1
               if amount > cbet[1]:
                  # Someone else reraised
                  break
               if action == 'fold':
                  self.users[user]['fold_cbet'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['call_cbet']) /
                              float(hands['call_cbet']+hands['fold_cbet']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['call_cbet'], hands['call_cbet']+hands['fold_cbet'])
      return output


class FDONK(BaseStats):
   """How often a player donk bet the flop (by betting into the preflop
   aggressor).

   (donk bet)/(checks + folds before preflop aggressor).

   The larger this number the better a player you are.
   """
   __name__ = 'FDONK'

   def __init__(self, data):
      super(FDONK, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         donk_bet = False
         preflop_aggressor = self.preflop_aggressor(hand_no)
         if preflop_aggressor and preflop_aggressor[0]:
            if not (hand.get('flop') and hand['flop'].get('bets')):
               continue
            for bet in hand['flop']['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'donk_bet': 0,
                     'not_donk_bet': 0,
                  }

               if user == preflop_aggressor[0]:
                  break

               if amount != 0 and not donk_bet:
                  self.users[user]['donk_bet'] += 1
                  donk_bet = True
               else:
                  self.users[user]['not_donk_bet'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['donk_bet']) /
                              float(hands['not_donk_bet']+hands['donk_bet']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['donk_bet'], hands['not_donk_bet']+hands['donk_bet'])
      return output


class FDONK10(BaseStats):
   """How often a player donk bet the flop (by betting into the preflop
   aggressor) and ignoring the strategic 10p bet.

   (donk bet)/(checks + folds before preflop aggressor).

   If somebody does a big blind donk bet, the next raise (before preflop
   aggressor) will count as the donk bet.

   Smaller FDONK-Josh/FDONK implies better player.
   """
   __name__ = 'FDONK-JOSH'

   def __init__(self, data):
      super(FDONK10, self).__init__(data)

   def calculate(self):
      for hand_no, hand in self.data.items():
         donk_bet = False
         big_blind = self.big_blind(hand_no)[1]
         preflop_aggressor = self.preflop_aggressor(hand_no)
         if preflop_aggressor and preflop_aggressor[0]:
            if not (hand.get('flop') and hand['flop'].get('bets')):
               continue
            for bet in hand['flop']['bets']:
               user = bet['player']
               action = bet['action']
               amount = bet['amount']

               if not self.users.get(user):
                  self.users[user] = {
                     'donk_bet': 0,
                     'not_donk_bet': 0,
                  }

               if user == preflop_aggressor[0]:
                  break

               if amount > big_blind and not donk_bet:
                  self.users[user]['donk_bet'] += 1
                  donk_bet = True
               else:
                  self.users[user]['not_donk_bet'] += 1

   def output(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         try:
            output[user] = (float(hands['donk_bet']) /
                              float(hands['not_donk_bet']+hands['donk_bet']))
         except:
            output[user] = 0
         print('%s: %s' % (user, output[user]))
      return output

   def num_denom(self):
      output = {}
      print(self.__name__)
      for user, hands in self.users.items():
         output[user] = (hands['donk_bet'], hands['not_donk_bet']+hands['donk_bet'])
      return output
