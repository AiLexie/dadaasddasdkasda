import base64 as Base64
import random as Random
import string
from functools import reduce
from datetime import datetime as DateTime
import math as Math
import re as Regex
import json as Json
from urllib import parse
from typing import Callable, Optional, Dict, List, Union
from http.server import HTTPServer, BaseHTTPRequestHandler

contents: Dict[str, bytes] = dict()
contents["/"] = open("./index.html", "r").read().encode("utf-8")

class InternalError(Exception):
  message: str

  def __init__(self, message: str):
    self.message = message

class DunderJSONEncoder(Json.JSONEncoder):
  def default(self, obj):
    try:
      return obj.__to_json__()
    except AttributeError:
      return obj

class User:
  # `name` is the identifying property for users.

  def __init__(self, name: str, password: str, about: str = None):
    self.name = name
    self.password = password
    self.about = about

  def __to_json__(self):
    return {
      "name": self.name,
      "about": self.about
    }

class Message:
  # `timestamp` is the identifying property for messages.

  def __init__(self, timestamp: float, author: Union[User, str], content: str):
    self.timestamp = timestamp
    self.author = author.name if isinstance(author, User) else author
    self.content = content

  def __to_json__(self):
    return {
      "content": self.content,
      "timestamp": str(self.timestamp),
      "user": self.author
    }

class Invite:
  # `code` is the identifying property for invites.

  def __init__(self, inviter: Union[User, str], code: str, accepter: Union[User, str] = None):
    self.inviter = inviter.name if isinstance(inviter, User) else inviter
    self.accepter = accepter.name if isinstance(accepter, User) else accepter
    self.code = code

  def __to_json__(self):
    return {
      "code": self.code,
      "accepter": self.accepter
    }

user_set = set()
message_set = set()
invite_set = set()

def get_user(name: str) -> Optional[User]:
  return next((user for user in user_set if user.name == name), None)

def store_user(new_user: User):
  old_user = get_user(new_user.name)
  if old_user is not None:
    user_set.remove(old_user)
  user_set.add(new_user)

def get_latest_messages(count: int, before: float = Math.inf) -> List[Message]:
  unsorted_messages: list[Message] = list(message_set)
  messages = sorted(unsorted_messages, key=lambda message : message.timestamp)
  raw_before_ind = next((ind for ind, message in enumerate(reversed(messages)) if before > message.timestamp), None)
  before_ind = raw_before_ind if raw_before_ind is not None else len(messages)
  return messages[len(messages) - count:len(messages) - before_ind]

def store_message(new_message: Message):
  old_message = next((message for message in message_set if message.timestamp == new_message.timestamp), None)
  if old_message is not None:
    message_set.remove(old_message)
  message_set.add(new_message)

def messages_get_authors(messages: List[Message]) -> List[str]:
  def reducer(author_list: List[str], message: Message) -> List[str]:
    if message.author not in author_list:
      return [*author_list, message.author]
    return author_list
  return reduce(reducer, messages, [])

def get_invites_from_user(username: str) -> List[Invite]:
  return [invite for invite in invite_set if invite.inviter == username]

def get_invite(code: str):
  return next((invite for invite in invite_set if invite.code == code), None)

def store_invite(new_invite: Invite):
  old_invite = get_invite(new_invite.code)
  if old_invite is not None:
    invite_set.remove(old_invite)
  invite_set.add(new_invite)

john = User("john", "12345")
bob = User("bob", "67890")
store_user(john)
store_user(bob)
store_message(Message(0, john, "Hi, I'm John!"))
store_message(Message(1, bob, "Hello World"))
store_message(Message(2, john, "Test test test"))
store_message(Message(3, john, "Can you see this?"))
store_invite(Invite(john, "pee"))

class RequestHandler(BaseHTTPRequestHandler):
  DIRECTORIES: Dict[str, Callable[[BaseHTTPRequestHandler], None]]
  FALLBACK: Callable[[BaseHTTPRequestHandler], None]

  method: str

  def do(self):
    path = parse.urlparse(self.path)
    path_parts = path.path.split("/")[1:]
    if len(path_parts) > 2 and path_parts[0] == "api" and (path_parts[1] == "v1" or path_parts[1] == "v1.0"):
      directory = path_parts[2]
      directory_handler = RequestHandler.DIRECTORIES.get(directory, RequestHandler.FALLBACK)
      directory_handler(self)
    elif self.method == "GET" and contents.get(path.path):
      content = contents.get(path.path)
      assert content is not None
      self.send_response(200)
      self.send_header("Content-Type", "text/html, charset=utf-8")
      self.send_header("Content-Length", str(len(content.decode("utf-8"))))
      self.end_headers()
      self.wfile.write(content)

  def do_GET(self):
    self.method = "GET"
    self.do()

  def do_POST(self):
    self.method = "POST"
    self.do()

def get_authorized_user(http_request: BaseHTTPRequestHandler) -> Optional[User]:
  def respond(message: str = "Bad cridentials.", code: int = 400):
    http_request.send_response(code)
    http_request.send_header("Content-Type", "application/json")
    http_request.end_headers()
    http_request.wfile.write(f'{{"message":"{message}"}}'.encode("utf-8"))
  
  try:
    full_auth = http_request.headers.get("Authorization")
    if full_auth is None:
      respond("Unauthorized.", 401); return
    auth_type, auth_raw = full_auth.split(" ", 1)
    if auth_type != "Basic":
      respond("Unknown authorization type."); return
    auth = Base64.b64decode(auth_raw).decode("utf-8")
    match = Regex.match(r"^(\w+):(.*)$", auth)
    if match is None:
      respond(); return
    user = get_user(match[1])
    if user is None or user.password != match[2]:
      respond(); return
    return user
  except:
    respond("Invalid cridentials.")

def request_user(http_request: BaseHTTPRequestHandler):
  if (authed_user := get_authorized_user(http_request)) is None:
    return
  user = get_user(http_request.path.split("/")[2]) # Update
  if user is None:
    http_request.send_response(404)
    http_request.send_header("Content-Type", "application/json")
    http_request.end_headers()
    http_request.wfile.write(b'{"message":"No one with that name exists."}')
    return
  http_request.send_response(200)
  http_request.send_header("Content-Type", "application/json")
  http_request.end_headers()
  http_request.wfile.write(Json.dumps(authed_user, cls = DunderJSONEncoder, separators = (',', ':')).encode("utf-8"))

def request_me(http_request: RequestHandler):
  if http_request.path != "/api/v1/me":
    request_not_found(http_request); return
  if http_request.method == "GET":
    if (authed_user := get_authorized_user(http_request)) is None:
      return
    http_request.send_response(200)
    http_request.send_header("Content-Type", "application/json")
    http_request.end_headers()
    http_request.wfile.write(Json.dumps(authed_user, cls = DunderJSONEncoder, separators = (',', ':')).encode("utf-8"))
  elif http_request.method == "POST":
    user: User
    try:
      length = int(http_request.headers.get("Content-Length"))
      body = http_request.rfile.read(length)
      data = Json.loads(body)
      invite_code = data.get("invite")
      username = data.get("username")
      password = data.get("password")
      invite = get_invite(invite_code)
      if invite is None or invite.accepter is not None:
        raise InternalError("Invalid invite.")
      if Regex.match(r"[a-z]{2,32}", username) is None:
        raise InternalError("Username must be between 2 and 32 characters, and lowecase latin characters only.")
      if get_user(username) is not None:
        raise InternalError("Username is taken.")
      user = User(username, password)
      new_invite = Invite(invite.inviter, invite.code, user)
      store_user(user)
      store_invite(new_invite)
    except BaseException as ex:
      message = ex.message if isinstance(ex, InternalError) else "Invalid body."
      http_request.send_response(400)
      http_request.send_header("Content-Type", "application/json")
      http_request.end_headers()
      http_request.wfile.write(f'{{"message":"{message}"}}'.encode("utf-8"))
    else:
      http_request.send_response(200)
      http_request.send_header("Content-Type", "application/json")
      http_request.end_headers()
      http_request.wfile.write(Json.dumps(user, cls = DunderJSONEncoder, separators = (',', ':')).encode("utf-8"))

def request_message(http_request: RequestHandler):
  if http_request.path != "/api/v1/messages":
    request_not_found(http_request); return
  if (authed_user := get_authorized_user(http_request)) is None:
     return
  assert authed_user is not None
  if http_request.method == "GET":
    path = parse.urlparse(http_request.path)
    query = dict(parse.parse_qsl(path.query))
    raw_count = query.get("count")
    raw_before = query.get("before")
    count = int(raw_count) if raw_count is not None else 50
    before = float(raw_before) if raw_before is not None else Math.inf
    messages = get_latest_messages(count, before)
    author_names = messages_get_authors(messages)
    authors = list(map(get_user, author_names))
    info_obj = {"users": authors, "messages": messages}
    
    http_request.send_response(200)
    http_request.send_header("Content-Type", "application/json")
    http_request.end_headers()
    http_request.wfile.write(Json.dumps(info_obj, cls = DunderJSONEncoder, separators = (',', ':')).encode("utf-8"))
  elif http_request.method == "POST":
    message: Message
    try:
      length = int(http_request.headers.get("Content-Length"))
      body = http_request.rfile.read(length)
      content = Json.loads(body).get("content")
      if content is None or content == "":
        raise InternalError("Invalid body." if content is None else "Cannot send empty message.")
      message = Message(DateTime.now().timestamp(), authed_user, content)
      store_message(message)
    except BaseException as ex:
      err_message = ex.message if isinstance(ex, InternalError) else "Invalid body."
      http_request.send_response(400)
      http_request.send_header("Content-Type", "application/json")
      http_request.end_headers()
      http_request.wfile.write(f'{{"message":"{err_message}"}}'.encode("utf-8"))
    else:
      http_request.send_response(200)
      http_request.send_header("Content-Type", "application/json")
      http_request.end_headers()
      http_request.wfile.write(Json.dumps(message, cls = DunderJSONEncoder, separators = (',', ':')).encode("utf-8"))

def request_invite(http_request: RequestHandler):
  path = parse.urlparse(http_request.path)
  if http_request.method == "GET":
    path_parts = path.path.split("/")[1:]
    invite_code = path_parts[1] if len(path_parts) > 1 else None
    if invite_code is None:
      if (authed_user := get_authorized_user(http_request)) is None:
        return
      invites = get_invites_from_user(authed_user.name)
      http_request.send_response(200)
      http_request.send_header("Content-Type", "application/json")
      http_request.end_headers()
      http_request.wfile.write(Json.dumps(invites, cls=DunderJSONEncoder, separators=(',', ':')).encode("utf-8"))
    else:
      invite = get_invite(invite_code)
      if invite is None or invite.author is not None:
        http_request.send_response(404)
        http_request.send_header("Content-Type", "application/json")
        http_request.end_headers()
        http_request.wfile.write(b'{"message":"Invite not found."}')
        return
      http_request.send_response(204)
      http_request.send_header("Content-Type", "application/json")
      http_request.end_headers()
  elif http_request.method == "POST":
    http_request.send_response(403)
    http_request.send_header("Content-Type", "application/json")
    http_request.end_headers()
    http_request.wfile.write(b'{"message":"POST towards /invites is temporarily dissabled until further notice."}')
    return
    if (authed_user := get_authorized_user(http_request)) is None:
      return
    assert authed_user is not None
    code = "".join(Random.choice(string.ascii_letters + string.digits) for i in range(8))
    invite = Invite(authed_user, code)
    store_invite(invite)
    http_request.send_response(200)
    http_request.send_header("Content-Type", "application/json")
    http_request.end_headers()
    http_request.wfile.write(Json.dumps(invite, cls=DunderJSONEncoder, separators=(',', ':')).encode("utf-8"))

def request_not_found(http_request: BaseHTTPRequestHandler):
  http_request.send_response(404)
  http_request.send_header("Content-Type", "application/json")
  http_request.end_headers()
  http_request.wfile.write(b'{"message":"Endpoint not found."}')

RequestHandler.DIRECTORIES = {"users": request_user, "messages": request_message, "invites": request_invite, "me": request_me}
RequestHandler.FALLBACK = request_not_found

server = HTTPServer(("", 8080), RequestHandler)

try:
  server.serve_forever()
except KeyboardInterrupt:
  print("Shutting down.")
  server.socket.close()
