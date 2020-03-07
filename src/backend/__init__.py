from gevent import monkey; monkey.patch_all()
from gevent import spawn
from gevent.queue import Queue
from gevent.pywsgi import WSGIServer, WSGIHandler
from typing import Any, Callable, Dict, List, Tuple, Union, Optional
from urllib.parse import parse_qsl, unquote, urlparse
from time import sleep
from os import getenv

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

	def __init__(self, request: Environ, respond: StartResponse, body: Queue):
		self._wr_head_fn = respond
		self._wr_body_queue = body

		method = request.get("REQUEST_METHOD")
		path = request.get("REQUEST_URI")
		assert method is not None
		assert path is not None
		self.method: str = method
		self.uri: str = path
		self.headers = {
			key[5:]: val for key, val in request.items() if key.startswith("HTTP_")
		}

		url = urlparse(path)
		self.path = [unquote(path) for path in url.path.split("/")][1:]
		self.query = parse_qsl(url.query)

	def write_head(self, status: Union[int, str], headers: Dict[str, str] = {}):
		"""Writes the head of the response. All headers must be supplied in
		`headers`.
		"""

		if type(status) != str:
			raise Exception("no")
		status_data: str = status # type: ignore

		header_arr = [(key, val) for key, val in headers.items()]

		self._wr_head_fn(status_data, header_arr)

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

		self.write_head("204 No Content", {})
		self.close_body()

from .endpoints import endpoints

def handler(job: HTTPJob):
	endpoint = endpoints.get(job.uri, endpoints.get(None, None))
	if endpoint is not None:
		endpoint(job)
	else:
		job.write_head("501 Not Implemented", {})
		job.close_body()

def direct_request_handler(request: Environ, respond: StartResponse):
	body = Queue()
	job = HTTPJob(request, respond, body)
	spawn(handler, job)
	return list(body)

def main():
	port_env = getenv("PORT")
	port = port_env if port_env is not None else 8080

	server = WSGIServer(('127.0.0.1', port), direct_request_handler,
		handler_class=RequestLinePathHandler)
	server.serve_forever()
