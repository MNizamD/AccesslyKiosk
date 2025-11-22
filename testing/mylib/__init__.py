# Only adjust when this module is imported (not run directly)
# Add /src/lib/ to sys.path so `from env import ...` still works
from sys import path as syspath
from os import path as ospath

current_dir = ospath.dirname(__file__)
if current_dir not in syspath:
    syspath.append(current_dir)
