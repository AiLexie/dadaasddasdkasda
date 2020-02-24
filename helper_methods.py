from typing import Callable, List, Optional, Tuple, TypeVar, Union, overload
from clastic import Response
from werkzeug.test import create_environ
from functools import reduce
from mimetypes import guess_type as get_type

_T = TypeVar("_T")

@overload
def try_except(success: Callable[..., _T]) -> Optional[_T]: ...
def try_except(success: Callable[..., _T],
    failiure: Union[Callable[[BaseException], None], _T] = None,
    *exceptions: List[BaseException]) -> _T:
  try:
    return success()
  except exceptions or Exception as ex:
    return failiure(ex) if callable(failiure) else failiure

def generate_methods(**opts: List[str]):
  """Modifies a route function to automatically handle HEAD and OPTIONS method
  requests. If the methods keyword argument is set, any method not in the list
  will also automatically be responded with status code 405 from this
  decorator.
  """

  def to_comma_sep_str(lst: List[str]):
    return try_except(lambda: reduce(lambda a, b: f"{a}, {b}", lst))
  methods = opts.get("methods", list())
  cors_methods = to_comma_sep_str(opts.get("cors_methods", list()))
  cors_origins = to_comma_sep_str(opts.get("cors_origins", list()))
  cors_headers = to_comma_sep_str(opts.get("cors-headers", list()))

  headers = {
    name: val for name, val in {
      "Allow": to_comma_sep_str(methods),
      "Access-Control-Allow-Origin": cors_origins,
      "Access-Control-Allow-Methods": cors_methods,
      "Access-Control-Allow-Headers": cors_headers
    }.items() if val is not None
  }

  def decorator(route):
    def new_route(request):
      if request.method not in methods and len(methods) > 0:
        return Response(status=405,
          headers={"Allow": to_comma_sep_str(methods)})
      elif request.method == "HEAD":
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

def static_routes(paths: List[str], content: Optional[Union[bytes, str]] = None,
    file: Optional[str] = None, mime: Optional[Tuple[str, str]] = None):
  if content is None and file is None:
    raise TypeError("Expected content xor file to be present but neither were.")
  elif content is not None and file is not None:
    raise TypeError("Expected content xor file to be present but both were.")
  the_content: Optional[Union[str, bytes]] = open(file, "r").read() \
    if file is not None else content
  the_mime = mime if mime is not None else get_type(file) \
    if file is not None else None
  assert the_content is not None

  @generate_methods(methods=["HEAD", "GET", "OPTIONS"])
  def route(request):
    content_length = the_content if type(the_content) == str \
      else the_content.decode("utf-8") # type: ignore
    return Response(the_content, 200, {
        "Content-Type": the_mime[0],
        "Content-Length": str(len(content_length)) # type: ignore
      })

  return [(path, route) for path in paths]
