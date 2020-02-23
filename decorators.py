from typing import Callable, List, Optional, TypeVar, Union, overload
from clastic import Response
from werkzeug.test import create_environ
from functools import reduce

_T = TypeVar("_T")

@overload
def try_except(success: Callable[..., _T]) -> Optional[_T]: ...
def try_except(success: Callable[..., _T],
    failiure: Union[Callable[[BaseException], None], _T] = None,
    *exceptions: List[BaseException]) -> _T:
  try:
    return success()
  except exceptions or BaseException as ex:
    return failiure(ex) if callable(failiure) else failiure

def generate_methods(**opts: List[str]):
  """Modifies a route function to automatically handle HEAD and OPTIONS method
  requests.
  """

  def to_comma_sep_str(lst: List[str]):
    return try_except(lambda: reduce(lambda a, b: f"{a}, {b}", lst))
  methods = to_comma_sep_str(opts.get("methods", list()))
  cors_methods = to_comma_sep_str(opts.get("cors_methods", list()))
  cors_origins = to_comma_sep_str(opts.get("cors_origins", list()))
  cors_headers = to_comma_sep_str(opts.get("cors-headers", list()))

  headers = {
    name: val for name, val in {
      "Allow": methods,
      "Access-Control-Allow-Origin": cors_origins,
      "Access-Control-Allow-Methods": cors_methods,
      "Access-Control-Allow-Headers": cors_headers
    } if val is not None
  }

  def decorator(route):
    def new_route(request):
      if request.method == "HEAD":
        new_request = create_environ(method="GET",
          query_string=request.query_string, headers=dict(request.headers))
        response = route(new_request)
        return Response(status=response.status, headers=response.headers)
      elif request.method == "OPTIONS":
        return Response(status=204, headers=headers)
      else:
        return route(request)
    return new_route
  return decorator
