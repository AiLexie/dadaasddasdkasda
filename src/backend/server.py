from os import getenv, path
from .utilities import load_json, static_routes
from typing import Dict
from clastic import Application

def main():
  port = getenv("PORT")

  this = path.dirname(path.abspath(__file__))
  content_map: Dict[str, str] = \
    load_json(open(path.join(this, "frontendmap.json"), "r").read())

  content_routes = [
    item for point, fi in content_map.items() for item \
      in static_routes([point], file = path.abspath(path.join("out/assets", fi)))
  ]

  print(content_routes)
  server = Application(content_routes)
  server.serve(port = port if port is not None else 8080, use_reloader = False)
