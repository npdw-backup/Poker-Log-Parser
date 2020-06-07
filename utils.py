import os
from concurrent.futures import ThreadPoolExecutor

from tornado.concurrent import run_on_executor
# Fuck IO blocking. I don't care. It's max 10 people at once.


class Utils(object):
   @staticmethod
   def line_prepender(filename, line):
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