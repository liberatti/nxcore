import json
import redis


class RedisDAO:
    """
    Data Access Object for Redis.

    Provides a simple interface for persisting and retrieving JSON data
    in Redis with support for key prefix scanning.
    """

    def __init__(self, host="127.0.0.1", port=6379, password=None, db=0):
        """
        Initializes the RedisDAO with connection parameters.

        Args:
            host (str, optional): Redis host address. Defaults to "127.0.0.1".
            port (int, optional): Redis port. Defaults to 6379.
            password (str, optional): Redis password. Defaults to None.
            db (int, optional): Redis database index. Defaults to 0.
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.conn = None

    def connect(self):
        """Establishes connection to the Redis server."""
        if not self.conn:
            self.conn = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True,
            )
            self.conn.ping()

    def _ensure_connection(self):
        """Ensures that the Redis connection is active."""
        if not self.is_connected():
            self.connect()

    def is_connected(self):
        try:
            return self.conn and self.conn.ping()
        except (redis.ConnectionError, AttributeError):
            return False

    def persist(self, key, value, expire=None):
        """
        Persists a value in Redis.

        Args:
            key (str): The key under which to store the value.
            value (any): The value to store (will be JSON serialized).
            expire (int, optional): Expiration time in seconds. Defaults to None.
        """
        self._ensure_connection()
        payload = json.dumps(value)
        self.conn.set(key, payload, ex=expire)

    def get_by_id(self, key):
        """
        Retrieves a value from Redis by its key.

        Args:
            key (str): The key to retrieve.

        Returns:
            any|None: The deserialized value if found, else None.
        """
        self._ensure_connection()
        value = self.conn.get(key)
        return json.loads(value) if value else None

    def delete(self, key):
        """
        Deletes a key from Redis.

        Args:
            key (str): The key to delete.

        Returns:
            int: The number of keys removed.
        """
        self._ensure_connection()
        return self.conn.delete(key)

    def get_keys_by_prefix(self, pattern="*"):
        """
        Retrieves all keys matching a specific pattern.

        Args:
            pattern (str, optional): The pattern to match. Defaults to "*".

        Returns:
            list[str]: List of matching keys.
        """
        self._ensure_connection()
        return list(self.conn.scan_iter(match=pattern))

    def get_items_by_prefix(self, pattern="*"):
        """
        Retrieves all items (keys and values) matching a pattern.

        Args:
            pattern (str, optional): The pattern to match. Defaults to "*".

        Returns:
            list[dict]: List of matching items with '_id' (key) and values.
        """
        self._ensure_connection()
        items = []

        for key in self.conn.scan_iter(match=pattern):
            raw = self.conn.get(key)
            if not raw:
                continue

            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    data["_id"] = key
                else:
                    data = {"_id": key, "value": data}
                items.append(data)
            except (json.JSONDecodeError, TypeError):
                continue

        return items

    def __enter__(self):
        """Context manager entry point."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        if self.conn:
            self.conn.close()
