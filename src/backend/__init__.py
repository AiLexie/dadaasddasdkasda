from gevent import monkey; monkey.patch_all()
from gevent import spawn
from gevent.queue import Queue
from gevent.pywsgi import WSGIServer
from typing import Any, Callable, Dict, List, Tuple, Union, Optional
from time import sleep

Environ = Dict[str, Any]
StartResponse = Callable[[str, List[Tuple[str, str]]], Any]

class HTTPJob:
	def __init__(self, request: Environ, respond: StartResponse, body: Queue):
		self._wr_head_fn = respond
		self._wr_body_queue = body

		self.method = request.get("REQUEST_METHOD")
		self.path = request.get("PATH_INFO")
		self.headers = {
			key[5:]: val for key, val in request.items() if key.startswith("HTTP_")
		}

	def write_head(self, status: Union[int, str], headers: Dict[str, str]):
		if type(status) != str:
			raise Exception("no")
		status_data: str = status # type: ignore

		header_arr = [(key, val) for key, val in headers.items()]

		self._wr_head_fn(status_data, header_arr)

	def write_body(self, body: Union[str, bytes, List[Union[str, bytes]]]):
		data = [
			(part.encode("utf-8") if isinstance(part, str) else part) \
				for part in (body if isinstance(body, list) else [body])
		]

		for part in data:
			self._wr_body_queue.put(part)

	def close_body(self,
			body: Optional[Union[str, bytes, List[Union[str, bytes]]]] = None):
		if body is not None:
			self.write_body(body)
		self._wr_body_queue.put(StopIteration)

def handler(job: HTTPJob):
	job.write_head("200 OK", {"Content-Type": "text/plain"})
	job.write_body("Hello.")
	job.close_body()
	print(job.headers)

def direct_request_handler(request: Environ, respond: StartResponse):
	body = Queue()
	job = HTTPJob(request, respond, body)
	spawn(handler, job)
	return list(body)

def main():
	server = WSGIServer(('127.0.0.1', 8080), direct_request_handler)
	server.serve_forever()
