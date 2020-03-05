from os import getenv, path
from .utilities import load_json, static_routes
from typing import Dict
from clastic import Application

def main():
  print(__import__(path.abspath("out/server-start")))

main()
