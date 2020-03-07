from . import HTTPJob
from json import JSONEncoder, dumps, loads
from functools import reduce
from mimetypes import guess_type as get_type
from typing import Callable, Dict, Generic, List, Optional, Tuple, TypeVar, \
  Union, overload

T = TypeVar("T")

class DunderJSONEncoder(JSONEncoder):
  """A JSON Encoder that treats objects with a __to_json__ method specially,
  and instead encodes the representation of the object using lists and
  dictionaries returned by the _to_json__ method.
  """

  def default(self, obj):
    try:
      return obj.__to_json__()
    except AttributeError:
      return obj

class ptr(Generic[T]):
  """A generic class that holds an object, and can be used as a pointer due to
  decorated names. The value of the pointer can easily be set and gotten with
  `self.value`. Represented as `<pointer to (representation of value)>`.
  """

  def __init__(self, value: T):
    self._value = value

  @property
  def value(self):
    return self._value

  @value.setter
  def value(self, value: T):
    self._value = value

  def __repr__(self) -> str:
    return f"<pointer to {self.value}>"

  def __str__(self) -> str:
    return str(self.value)

class HTTPHeadJob(HTTPJob):
  """Internal class used for desguising a HEAD request as a GET request. Used by
  the `generate_methods` function.
  """

  def __init__(self, old_job: HTTPJob):
    self.method = "GET"
    self.uri = old_job.uri
    self.headers = old_job.headers
    self._old_job = old_job

  def write_head(self, status: Union[int, str], headers: Dict[str, str] = {}):
    self._old_job.write_head(status, headers)
    self._old_job.close_body()

  def write_body(self):
    pass

  def close_body(self):
    pass

@overload
def try_except(success: Callable[..., T]) -> Optional[T]: ...
def try_except(success: Callable[..., T],
    failiure: Union[Callable[[BaseException], None], T] = None,
    *exceptions: List[BaseException]) -> T:
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

  def decorator(handler: Callable[..., None]):
    def new_route(job: HTTPJob, *args, **kwargs):
      if job.method not in methods and len(methods) > 0:
        allowed = to_comma_sep_str(methods)
        if allowed is None:
           job.write_head("500 Internal Server Error")
        else:
          job.write_head("405 Method Not Allowed", {"Allow": allowed})
        job.close_body()
      elif job.method == "HEAD":
        new_job = HTTPHeadJob(job)
        handler(new_job, *args, **kwargs)
      elif job.method == "OPTIONS":
        job.write_head("204 No Content", headers)
        job.close_body()
      else:
        return handler(job, *args, **kwargs)
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
  def route(job: HTTPJob):
    content_length = the_content if isinstance(the_content, str) \
      else the_content.decode("utf-8")
    job.write_head("200 OK", {
        "Content-Type": the_mime[0],
        "Content-Length": str(len(content_length))
      })
    job.close_body(the_content)

  return {path: route for path in paths}

def dump_json(obj, indent: Union[None, int, str] = "\t"):
  if indent is None:
    return dumps(obj, cls=DunderJSONEncoder, separators=(',', ':'))
  else:
    return dumps(obj, cls=DunderJSONEncoder, indent=indent)

def load_json(json: str):
  return loads(json)
