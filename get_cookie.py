import asyncio
import os
import urllib.request

import websockets
from tornado import concurrent

from utils import Utils


class GetCookie(object):
   def __init__(self, game_id):
      self.GAME_ID = game_id or '2VQEY-Vn6ggeXBtg7mUkXY_Dd'
      self.GAME_URL = 'https://www.pokernow.club/games/%s/' % self.GAME_ID
      self.WSS_URL = 'wss://www.pokernow.club/socket.io/?gameID=%s&EIO=3&transport=websocket' % self.GAME_ID


   async def get_cookie(self):
      cookie = Utils.read_file('%s.cookie' % self.GAME_ID)
      if cookie:
         try:
            url = urllib.request.urlopen('%s/log' % self.GAME_URL)
            cookie = url.info()['Set-Cookie'].split(';')[0]
         except:
            # Cookie has expired/never worked
            cookie = None

      if not cookie:
         url = urllib.request.urlopen(self.GAME_URL)
         cookie = url.info()['Set-Cookie'].split(';')[0]

         async def hello():
            async with websockets.connect(self.WSS_URL, extra_headers=[('Cookie', cookie)]) as websocket:
               pass
               # Dirty Russian bot doesn't want people just doenloading logs.
               # So have to initiate websocket connection to prove you're not a
               # python script designed to scrape logs.

         # Write cookie to disk to stop hundreds of 'users'.



         await hello()
         Utils.write_file('cookies/%s' % self.GAME_ID, cookie)
      return cookie
