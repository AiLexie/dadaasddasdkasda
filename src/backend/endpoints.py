from . import HTTPJob
from urllib.parse import parse_qsl, urlparse, unquote
from .utilities import load_json, static_routes, generate_methods
from typing import Dict, Callable, Union, List, Tuple, Optional
from os import path

class AnnotatedEndpoint():
	@staticmethod
	def annotate(expression: List[Optional[str]]):
		def decorator(endpoint: Callable[[HTTPJob, List[str]], None]):
			return AnnotatedEndpoint(expression, endpoint)
		return decorator

	def __init__(self, expression: List[Optional[str]],
			endpoint: Callable[[HTTPJob, List[str]], None]):
		self.expression = expression
		self._annotated_item = endpoint

	def __call__(self, job: HTTPJob):
		unmarked_paths = [
			job.path[ind] for ind, item in enumerate(self.expression) \
				if item is None
		]

		self._annotated_item(job, unmarked_paths)

@AnnotatedEndpoint.annotate(["api", "v1", "communities", None, "channels", None, "messages"])
@generate_methods(methods=["HEAD", "OPTIONS", "GET", "POST"])
def on_messages_request(job: HTTPJob, path: List[str]):
	print(path)
	job.done()

internal_endpoints = [
	on_messages_request
]

def on_request(job: HTTPJob):
	# api.site.com/v1/communities/{community_name_id}/channels/{channel_name_id}/messages
	# api.site.com/v1/communities/_/channels/_/messages
	# https://website-schooll.herokuapp.com/api/v1/communities/_/channels/_/messages?max=50&polling=true

	url = urlparse(job.uri)
	paths = [unquote(path) for path in url.path.split("/")][1:]
	query = parse_qsl(url.query)

	endpoint = next((endpoint for endpoint in internal_endpoints \
		if len(endpoint.expression) == len(paths) and \
			all((end_part is None or end_part == paths[ind]) \
				for ind, end_part in enumerate(endpoint.expression))), None)
	
	if endpoint is not None:
		endpoint(job)
	else:
		job.write_head("501 Not Implemented", {})
		job.close_body()

front_end_points = {
	key: val \
		for endpoint, fil in (load_json(open(path.join(path.dirname(__file__),
			"../frontendmap.json"), "r").read()).items())
				for key, val in static_routes([endpoint],
					file=path.join(path.dirname(__file__), "../assets", fil)).items()
}

back_end_points = {
	None: on_request
}

endpoints: Dict[Union[str, None], Callable[[HTTPJob], None]] = \
	dict(back_end_points, **front_end_points)
