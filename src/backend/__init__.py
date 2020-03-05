# Avoids write time error.
from importlib import import_module
hyper_py = import_module("hyper_py")

def main():
  print(hyper_py)
