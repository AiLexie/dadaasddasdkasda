# from gevent import monkey; monkey.patch_all()
from gevent import spawn
from gevent.queue import Queue
from gevent.pywsgi import WSGIServer, WSGIHandler, Input
from typing import Any, Callable, Dict, List, Tuple, Union, Optional
from urllib.parse import parse_qsl, unquote, urlparse
from json import loads
from os import getenv, path as ospath

Environ = Dict[str, Any]
StartResponse = Callable[[str, List[Tuple[str, str]]], Any]

class RequestLinePathHandler(WSGIHandler):
	def get_environ(self):
		return {
			**super().get_environ(),
			'REQUEST_URI': self.path,
		}

class HTTPJob:
	"""Represents an HTTP request and response pair. The implementation of this
	means that you don't have to send a response immediately, infact you don't
	even have to send a response at all.
	"""

	status_codes = {
		int(code): f"{code} {message}" \
			for code, message in loads(open(ospath.join(ospath.dirname(__file__),
				"../statuscodes.json"), "r").read()).items()
	}

	def __init__(self, request: Environ, respond: StartResponse, body: Queue):
		self._wr_head_fn = respond
		self._wr_body_queue = body

		method = request.get("REQUEST_METHOD")
		path = request.get("REQUEST_URI")
		body = request.get("wsgi.input")
		assert method is not None
		assert path is not None
		assert body is not None
		self.method: str = method
		self.uri: str = path
		self.body: Input = body
		self.headers = {
			key[5:]: val for key, val in request.items() if key.startswith("HTTP_")
		}

		url = urlparse(path)
		self.path = [] if url.path == "/" else \
			[unquote(path) for path in url.path.split("/")][1:]
		self.query = parse_qsl(url.query)

	def write_head(self, status: Union[int, str], headers: Dict[str, str] = {}):
		"""Writes the head of the response. All headers must be supplied in
		`headers`.
		"""

		status_data: Optional[str] = status if type(status) is str \
			else HTTPJob.status_codes.get(status)
		header_arr = [(key, val) for key, val in headers.items()]
		if status_data is None:
			raise ValueError("Invalid status code.")

		self._wr_head_fn(status_data, header_arr)

	def close_head(self, status: Union[int, str], headers: Dict[str, str] = {}):
		"""Writes the head of the response, then ends the request with no content.
		"""

		self.write_head(status, headers)
		self.close_body()

	def write_body(self, body: Union[str, bytes, List[Union[str, bytes]]]):
		"""Writes part of the body. The body may be a `str`, `bytes`, or a list of
		any combination of them.
		"""

		data = [
			(part.encode("utf-8") if isinstance(part, str) else part) \
				for part in (body if isinstance(body, list) else [body])
		]

		for part in data:
			self._wr_body_queue.put(part)

	def close_body(self,
			body: Optional[Union[str, bytes, List[Union[str, bytes]]]] = None):
		"""Closes the body, before writing the optional value `body`. If `body` is
		present, the `write_body` method will be called with `body` before closing.
		"""

		if body is not None:
			self.write_body(body)
		self._wr_body_queue.put(StopIteration)

	def done(self):
		"""Typically should only be used for debugging. Sends a complete response
		with code 204, and no body nor headers.
		"""

		self.write_head(204, {})
		self.close_body()

from .endpoints import handler

def direct_request_handler(request: Environ, respond: StartResponse):
	body = Queue()
	job = HTTPJob(request, respond, body)
	spawn(handler, job)
	return list(body)

def main():
	port_env = getenv("PORT")
	port = int(port_env) if port_env is not None else 8080

	server = WSGIServer(('127.0.0.1', port), direct_request_handler,
		handler_class=RequestLinePathHandler)
	server.serve_forever()
