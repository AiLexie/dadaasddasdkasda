from . import HTTPJob
from json import JSONEncoder, dumps, loads, JSONDecodeError
from functools import reduce
from mimetypes import guess_type as get_type
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Tuple, \
	TypeVar, Union, overload

T = TypeVar("T")

JSONDecodeError = JSONDecodeError

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

class Endpoint:
	@staticmethod
	def into(expression: Union[str, List[Optional[str]]]):
		return lambda handler: Endpoint(expression, handler)

	def __init__(self, expression: Union[str, List[Optional[str]]],
			handler: Callable[..., None]):
		self._handler = handler
		self.expression = [
			(part if part != "" else None) for part in \
				(expression.split("/")[1:] if type(expression) is str else expression)
		]

	def __call__(self, job: HTTPJob):
		parameters = [
			job.path[ind] for ind, item in enumerate(self.expression) \
				if item is None
		]
		self._handler(job, *parameters)

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

def join(lst: Iterable[Any], glue: str = ", "):
	return try_except(lambda: reduce(lambda a, b: f"{a}{glue}{b}", lst), "")

def generate_endpoint(expression: Union[str, List[Optional[str]]],
		methods: Dict[str, Optional[Callable[..., None]]],
		cors_methods: List[str] = [], cors_origins: List[str] = [],
		cors_headers: List[str] = []):
	headers_405 = {name: val for name, val in {
		"Accept": join(list(methods.keys()))
	}.items() if val != ""}
	headers_options = {name: val for name, val in dict({
		"Access-Control-Allow-Origin": join(cors_origins),
		"Access-Control-Allow-Methods": join(cors_methods),
		"Access-Control-Allow-Headers": join(cors_headers)
	}, **headers_405).items() if val != ""}

	def perform_head(job: HTTPJob, *args, **kwargs):
		new_job = HTTPHeadJob(job)
		methods.get("GET")(new_job)

	def preform_options(job: HTTPJob, *args, **kwargs):
		job.close_head("204 No Content", headers_options)

	compiled_methods = dict({
		"HEAD": perform_head,
		"OPTIONS": preform_options
	}, **methods)

	def on_request(job: HTTPJob, *args, **kwargs):
		method = compiled_methods.get(job.method)
		if method is None:
			job.close_head(405, headers_405)
		else:
			method(job, *args, **kwargs)
	return Endpoint(expression, on_request)

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

	def route(job: HTTPJob):
		content_length = the_content if isinstance(the_content, str) \
			else the_content.decode("utf-8")
		job.write_head("200 OK", {
				"Content-Type": the_mime[0],
				"Content-Length": str(len(content_length))
			})
		job.close_body(the_content)

	return [
		generate_endpoint("" if path == "/" else path, methods = {"GET": route}) \
			for path in paths
	]

def dump_json(obj, indent: Union[None, int, str] = "\t"):
	if indent is None:
		return dumps(obj, cls=DunderJSONEncoder, separators=(',', ':'))
	else:
		return dumps(obj, cls=DunderJSONEncoder, indent=indent)

def load_json(json: str):
	return loads(json)
