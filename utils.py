import os
from concurrent.futures import ThreadPoolExecutor

from tornado.concurrent import run_on_executor
# Fuck IO blocking. I don't care. It's max 10 people at once.


class Utils(object):
   @staticmethod
   def write_file(filename, contents, check_directory=True):
      file_dir = '/'.join(filename.split('/')[:-1])
      if check_directory and not os.path.isdir(file_dir):
         os.mkdir(file_dir)
      with open(filename, 'w') as f:
         f.write(contents)

   @staticmethod
   def read_file(filename):
      if not os.path.exists(filename):
         return None
      with open(filename, 'r') as f:
         data = f.read()
         return data