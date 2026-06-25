from typing import Any, Dict, List, Optional, Tuple, Union

import cx_Oracle
from marshmallow import Schema, fields

from nxcore.middleware.logging_manager import logger
from nxcore.repository.schemas.page_meta_schema import PageMetaSchema


class OracleDAO:
    """Data Access Object for Oracle.

    Provides a standard interface for CRUD operations on an Oracle table
    with support for Marshmallow schemas and pagination.
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        service: str,
        table_name: str,
        schema: Optional[type[Schema]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initializes the OracleDAO with connection details and optional schema.

        Args:
            host (str): Oracle host address.
            port (int): Oracle port number.
            user (str): Oracle username.
            password (str): Oracle password.
            service (str): Oracle service name.
            table_name (str): Name of the table to operate on.
            schema (type[Schema], optional): Marshmallow schema for serialization. Defaults to None.
            config (dict, optional): Configuration flag to trigger connection. Defaults to None.
        """
        self.table_name = table_name
        self.schema = schema() if schema else None
        self.pageSchema = None
        if config:
            dsn = cx_Oracle.makedsn(host, port, service_name=service)
            self.conn = cx_Oracle.connect(user, password, dsn)

        if schema:
            page_class = type(
                "pagination",
                (Schema,),
                {
                    "metadata": fields.Nested(PageMetaSchema, many=False),
                    "data": fields.Nested(schema, many=True),
                },
            )
            self.pageSchema = page_class()

    def to_dict(self, row: Any) -> Any:
        """Post-processing hook for rows fetched from the database.

        Args:
            row (dict): The raw dictionary from the database.

        Returns:
            dict: The processed dictionary.
        """
        return row

    def from_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-processing hook for dictionaries before database operations.

        Args:
            row (dict): The dictionary to process.

        Returns:
            dict: The processed dictionary.
        """
        return row

    def json_load(self, json_data: Union[Dict[str, Any], List[Dict[str, Any]]], many: bool = False) -> Any:
        """Loads and validates JSON data using the assigned schema.

        Args:
            json_data (dict|list): The JSON data to load.
            many (bool): Whether to load multiple objects. Defaults to False.

        Returns:
            object: The loaded and validated data.
        """
        return self.schema.load(json_data, many=many) if self.schema else json_data

    def json_dump(self, row: Any, many: bool = False) -> Any:
        """Serializes an object using the assigned schema.

        Args:
            row (object): The object to serialize.
            many (bool): Whether to serialize multiple objects. Defaults to False.

        Returns:
            dict|list: The serialized data.
        """
        return self.schema.dump(row, many=many) if self.schema else row

    def _interpolate_sql(self, sql: str, params: Union[Tuple[Any, ...], List[Any], None]) -> str:
        """Interpolates SQL with parameters for debugging purposes.

        Args:
            sql (str): SQL query with placeholders.
            params (tuple|list): Parameters for the query.

        Returns:
            str: The interpolated SQL string.
        """
        if not params:
            return sql
        try:
            escaped = tuple(repr(p) for p in params)
            return sql % escaped
        except Exception:
            return f"{sql} | PARAMS: {params}"

    def _query(self, sql: str, params: Optional[Union[Tuple[Any, ...], List[Any]]] = None, fetch: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Executes a SQL query.

        Args:
            sql (str): SQL query to execute.
            params (tuple, optional): Parameters for the query. Defaults to None.
            fetch (bool): Whether to fetch results. Defaults to False.

        Returns:
            list[dict]|None: List of rows if fetch is True, otherwise None.
        """
        cursor = self.conn.cursor()
        logger.debug(self._interpolate_sql(sql, params))
        try:
            cursor.execute(sql, params or ())
            if fetch:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def __del__(self) -> None:
        """Destructor that closes the Oracle connection."""
        if hasattr(self, "conn"):
            try:
                self.conn.close()
            except Exception:
                pass

    def get_all(self, pagination: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves all records with optional pagination and ordering.

        Args:
            pagination (dict, optional): Pagination parameters ('page', 'per_page').
            order_by (str, optional): SQL ORDER BY clause. Defaults to None.

        Returns:
            dict: Dictionary with 'metadata' and 'data'.
        """
        sql = f"SELECT * FROM {self.table_name}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        count_sql = f"SELECT COUNT(*) AS total FROM {self.table_name}"

        count_result = self._query(count_sql, fetch=True)
        total = count_result[0]["TOTAL"] if count_result else 0
        rows = []

        if pagination:
            page = pagination.get("page", 1)
            per_page = pagination.get("per_page", 10)
            offset = (page - 1) * per_page
            sql += f" OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
            pagination["total_elements"] = total
        else:
            pagination = {"total_elements": total, "page": 1, "per_page": total}

        rs = self._query(sql, fetch=True)
        if rs:
            rows = [row for row in rs]
            for r in rows:
                self.to_dict(r)
        return {
            "metadata": pagination,
            "data": rows,
        }

    def get_desc_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        """Retrieves id and name for a specific record.

        Args:
            id (any): The record identifier.

        Returns:
            dict|None: Row containing id and name if found, else None.
        """
        sql = f"SELECT id, name FROM {self.table_name} WHERE id = :1"
        rs = self._query(sql, (id,), fetch=True)
        row = rs[0] if rs else None
        if row:
            self.to_dict(row)
        return row

    def get_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        """Retrieves a complete record by its ID.

        Args:
            id (any): The record identifier.

        Returns:
            dict|None: The complete row if found, else None.
        """
        sql = f"SELECT * FROM {self.table_name} WHERE id = :1"
        rs = self._query(sql, (id,), fetch=True)
        row = rs[0] if rs else None
        if row:
            self.to_dict(row)
        return row

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a complete record by its name.

        Args:
            name (str): The name to search for.

        Returns:
            dict|None: The complete row if found, else None.
        """
        sql = f"SELECT * FROM {self.table_name} WHERE name = :1 AND ROWNUM = 1"
        rs = self._query(sql, (name,), fetch=True)
        row = rs[0] if rs else None
        if row:
            self.to_dict(row)
        return row

    def update_by_id(self, id: Any, vo: Dict[str, Any]) -> bool:
        """Updates a record by its ID.

        Args:
            id (any): The record identifier.
            vo (dict): Dictionary with updated data.

        Returns:
            bool: True if operation completed successfully.
        """
        self.from_dict(vo)
        keys = ", ".join([f"{k} = :{i + 1}" for i, k in enumerate(vo.keys())])
        sql = f"UPDATE {self.table_name} SET {keys} WHERE id = :{len(vo) + 1}"
        values = list(vo.values()) + [id]
        self._query(sql, values)
        self.conn.commit()
        return True

    def persist(self, vo: Dict[str, Any]) -> Any:
        """Inserts a new record.

        Args:
            vo (dict): Dictionary with record data.

        Returns:
            any: The last inserted ID.
        """
        self.from_dict(vo)
        keys = ", ".join(vo.keys())
        values_placeholder = ", ".join([f":{i + 1}" for i in range(len(vo))])
        sql = f"INSERT INTO {self.table_name} ({keys}) VALUES ({values_placeholder})"
        values = list(vo.values())

        cursor = self.conn.cursor()
        try:
            logger.debug(self._interpolate_sql(sql, values))
            cursor.execute(sql, values)
            self.conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    def persist_many(self, arr: List[Dict[str, Any]]) -> bool:
        """Inserts multiple records.

        Args:
            arr (list[dict]): List of dictionaries with record data.

        Returns:
            bool: True if operation completed successfully.
        """
        if not arr:
            return False
        keys = ", ".join(arr[0].keys())
        values_placeholder = ", ".join([f":{i + 1}" for i in range(len(arr[0]))])
        sql = f"INSERT INTO {self.table_name} ({keys}) VALUES ({values_placeholder})"
        for item in arr:
            self._query(sql, tuple(item.values()))
        self.conn.commit()
        return True

    def delete_by_id(self, id: Any) -> bool:
        """Deletes a record by its ID.

        Args:
            id (any): The record identifier.

        Returns:
            bool: True if operation completed successfully.
        """
        sql = f"DELETE FROM {self.table_name} WHERE id = :1"
        self._query(sql, (id,))
        self.conn.commit()
        return True

    def delete_all(self) -> bool:
        """Deletes all records from the table.

        Returns:
            bool: True if operation completed successfully.
        """
        sql = f"DELETE FROM {self.table_name}"
        self._query(sql)
        self.conn.commit()
        return True
