import os
from pymongo import MongoClient
from pymongo.database import Database, Collection
from datetime import datetime, timedelta
from time import sleep
from threading import Thread
from inspect import signature
from .utilities import ptr
from typing import Any, Callable, Dict, Tuple, Type, TypeVar, Optional, Union

C = TypeVar("C")
T = TypeVar("T")

_client: Database = MongoClient(os.getenv("MONGO_DB_CONNECT"))["project-dark"]

_db_cache: ptr[Dict[object, datetime]] = ptr(dict())

class User:
	"""Represents a user, piping hot from the database. Users' unique id is the
	name property.
	"""

	def __init__(self, name: str, password: str, about: str = None):
		self.name = name
		self.password = password
		self.about = about

	def __to_json__(self):
		return {
			"name": self.name
		}

class Message:
	"""Represents a message, piping hot from the database. Messages' unique id is
	the timestamp property.
	"""

	def __init__(self, timestamp: float, author: Union[User, str], content: str):
		self.timestamp = timestamp
		self.author = author.name if isinstance(author, User) else author
		self.content = content

	def __to_json__(self):
		return {
			"timestamp": self.timestamp,
			"author": self.author,
			"content": self.content
		}

def _create_simple_db_cache_getter(cache: ptr[Dict[Any, datetime]],
		collection: Collection, id_name: str, id_type: Type[T], Class: Type[C]):
	"""Creates a getter function for a database collection that has only one
	unique property to worry about. The getter function returned will
	automatically query the `cache` first, and if required set the newly made
	object in the `cache`. The returned object type is supplied as `Class`, and
	the unique id is supplied as `id_name` and it's type as `id_type`. `id_type`
	is only used for type hinting.
	"""

	def create(raw_obj: Dict[str, Any]):
		class_params = signature(Class).parameters
		args = {key: val for key, val in raw_obj.items() if key in class_params}
		return Class(**args)

	def db_getter(id_attr: T) -> Optional[C]:
		nonlocal cache

		cached_obj = next((obj for obj, time in cache.value.items() \
			if isinstance(obj, Class) and getattr(obj, id_name) == id_attr), None)
		
		if cached_obj is not None:
			# Update the cache with the access time.
			cache.value = {
				**cache.value,
				cached_obj: datetime.now()
			}
			return cached_obj
		else:
			# Query the data base since this query hasn't been cached.
			raw_obj = collection.find_one({id_name: id_attr})
			if raw_obj is None:
				return None

			obj = create(raw_obj)
			# Update cache with the object.
			cache.value = {
				**cache.value,
				obj: datetime.now()
			}
			return obj
	return db_getter

def _create_simple_db_cache_setter(cache: ptr[Dict[Any, datetime]],
		collection: Collection, id_name: str, Class: Type[C]):
	"""Creates a setter function for a database collection that has only one
	unique property to worry about. The setter function returned will
	automatically place the new value in the `cache`. The accepted object type is
	supplied as `Class`, and the unique id is supplied as `id_name`.
	"""

	def db_setter(new_obj: C):
		nonlocal cache

		id_attr = getattr(new_obj, id_name)
		collection.replace_one({id_name: id_attr}, vars(new_obj), True)

		# Update cache with the new object, replacing the old one if present.
		cache.value = {
			**{
				key: val for key, val in cache.value.items() \
					if type(val) != Class or getattr(key, id_name) != id_attr
			},
			new_obj: datetime.now()
		}
	return db_setter

def _create_simple_db_cache_getter_setter(cache: ptr[Dict[Any, datetime]],
		collection: Collection, id_name: str, id_type: Type[T], Class: Type[C]) -> \
		Tuple[Callable[[T], Optional[C]], Callable[[C], None]]:
	"""Returns a getter setter tuple. Read `_create_simple_db_cache_getter` and
	`_create_simple_db_cache_setter`'s docs.
	"""

	return (
		_create_simple_db_cache_getter(cache, collection, id_name, id_type, Class),
		_create_simple_db_cache_setter(cache, collection, id_name, Class)
	)

# Getters and setters for data with one ID.
get_user_by_name, set_user = _create_simple_db_cache_getter_setter(_db_cache, _client.users, "name", str, User)
get_message_by_timestamp, set_message = _create_simple_db_cache_getter_setter(_db_cache, _client.messages, "timestamp", float, Message)

# TODO: Use cache here!
def get_messages_by_timestamp(timestamp: float, before: bool, limit: int):
	collection: Collection = _client.messages

	aggregation = [
		{"$match": {"timestamp": {"$lt" if before else "$gt": timestamp}}},
		{"$sort": {"timestamp": -1 if before else 1}},
		{"$limit": limit}
	]

	raw_messages = collection.aggregate(aggregation)
	return [
		Message(**{key: val for key, val in raw_message.items() if key != "_id"}) \
			for raw_message in raw_messages
	]

def _db_cache_mngmnt_func(cache: ptr[Dict[object, datetime]], seconds: int):
	delta = timedelta(0, seconds)
	while True:
		now = datetime.now()
		global _db_cache
		cache.value = {
			obj: time for obj, time in cache.value.items() \
				if now < time + delta
		}
		sleep(30)

_db_cache_mngmnt = Thread(target = _db_cache_mngmnt_func,
	args = [_db_cache, 500], daemon = True)
_db_cache_mngmnt.start()
