import json
import os
import time
import urllib

from tornado.httpclient import AsyncHTTPClient

from get_cookie import GetCookie


class GameTracker(object):
   def __init__(self, game_id):
      self.GAME_ID = game_id or '2VQEY-Vn6ggeXBtg7mUkXY_Dd'
      self.LOG_URL = 'https://www.pokernow.club/games/%s/log?after_at=&before_at=&mm=false' % self.GAME_ID
      self.FILENAME = 'logs/%s.csv' % self.GAME_ID
      self.updates = False
      self.http_client = AsyncHTTPClient()

   def line_prepender(self, filename, line):
      file_dir = '/'.join(filename.split('/')[:-1])
      if not os.path.isdir(file_dir):
         os.mkdir(file_dir)
      if not os.path.isfile(filename):
         with open(filename, 'w') as f:
            pass

      with open(filename, 'r+') as f:
         content = f.read()

         if not content and '-- starting hand' not in line:
            # Only want to start writing to file at beginning of hand
            return

         f.seek(0, 0)
         f.write(line.rstrip('\r\n') + '\n' + content)

   def write_to_file(self, events):
      for event in events:
         action = "\"" + event['msg'].replace("\"", "\"\"") + "\""
         line = ','.join([action, event['at'], event['created_at']])
         self.line_prepender(self.FILENAME, line)

   def get_max_time(self, filename):
      if not os.path.isfile(filename):
         return 0

      with open(filename, 'r') as f:
         content = f.readline()
         if not content:
            return 0
         return int(content.split(',')[-1])


   def parse_json(self, content):
      new_max_time = int(content['infos']['max'])
      max_time = self.get_max_time(self.FILENAME)
      if new_max_time == max_time:
         return False

      log_events = content['logs']

      log_events.sort(key=lambda x: int(x['created_at']), reverse=False)
      new_log_events = [log_event for log_event in log_events
                                 if int(log_event['created_at']) > max_time]

      self.write_to_file(new_log_events)
      return True


   async def listen(self):
      cookie_manager = GetCookie(self.GAME_ID)
      cookie = await cookie_manager.get_cookie()
      headers = {
         "cookie": cookie,
         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
      }
      req = await self.http_client.fetch(self.LOG_URL, headers=headers)
      content = req.body
      json_content = json.loads(content)

      self.updates = self.parse_json(json_content)
      self.updates = True



if __name__ == "__main__":
   # If started from command line.
   game_tracker = GameTracker(None)
   game_tracker.listen()