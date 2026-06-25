import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import duckdb
from marshmallow import Schema, fields

from nxcore.middleware.logging_manager import logger
from nxcore.repository.schemas.page_meta_schema import PageMetaSchema


class DuckDAO:
    """Data Access Object for DuckDB.

    Provides a standard interface for CRUD operations on a DuckDB table
    with support for Marshmallow schemas and pagination.
    """

    def __init__(
        self,
        db_path: str,
        table_name: str,
        schema: Optional[type[Schema]] = None,
        conn: Optional[duckdb.DuckDBPyConnection] = None,
        auto_commit: bool = True,
    ):
        """Initializes the DuckDAO with connection details and optional schema.

        Args:
            db_path (str): Path to the directory containing the DuckDB database.
            table_name (str): Name of the table to operate on.
            schema (type[Schema], optional): Marshmallow schema for serialization. Defaults to None.
            conn (duckdb.DuckDBPyConnection, optional): Existing connection. Defaults to None.
            auto_commit (bool, optional): Whether to commit changes automatically. Defaults to True.
        """
        self.table_name = table_name
        self.schema = schema() if schema else None
        self.pageSchema = None
        self.db_path = db_path
        self.conn = conn
        self.auto_commit = auto_commit

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

    def connect(self) -> None:
        """Establishes connection to the DuckDB database."""
        if not self.is_connected():
            db_file = f"{self.db_path}/app.duckdb"
            logger.debug(f"DuckDAO: {db_file}")
            os.makedirs(self.db_path, exist_ok=True)
            self.conn = duckdb.connect(db_file)

    def is_connected(self) -> bool:
        """Checks if the connection to DuckDB is established.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.conn is not None

    def __enter__(self) -> "DuckDAO":
        """Context manager entry point."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit point with automatic rollback on error."""
        try:
            if exc_type is not None:
                try:
                    self.conn.rollback()
                except Exception:
                    pass
            elif self.auto_commit:
                self.commit()
        finally:
            self.conn.close()

    def commit(self) -> None:
        """Commits the current transaction."""
        logger.debug(f"[{self.auto_commit}] commit")
        try:
            self.conn.commit()
        except Exception as e:
            logger.debug(f"DuckDAO commit exception (possibly no active transaction): {e}")

    def to_dict(self, row: Any) -> Optional[Dict[str, Any]]:
        """Post-processing hook for rows fetched from the database.

        Args:
            row (dict): The raw row from the database.

        Returns:
            dict or None: The processed dictionary.
        """
        return dict(row) if row else row

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-processing hook for dictionaries before database operations.

        Args:
            vo (dict): The dictionary to process.

        Returns:
            dict: The processed dictionary.
        """
        return vo

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

    def _interpolate_sql(self, sql: str, params: Union[Tuple[Any, ...], List[Any]]) -> str:
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
        except Exception as e:
            return f"{sql} | PARAMS: {params} | {e}"

    def _query(self, sql: str, params: Union[Tuple[Any, ...], List[Any]] = (), fetch: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Executes a SQL query.

        Args:
            sql (str): SQL query to execute.
            params (tuple, optional): Parameters for the query. Defaults to ().
            fetch (bool): Whether to fetch results. Defaults to False.

        Returns:
            list[dict]|None: List of rows if fetch is True, otherwise None.
        """
        cursor = self.conn.cursor()
        logger.debug(self._interpolate_sql(sql, params))
        try:
            cursor.execute(sql, params)
            if fetch:
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()

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
        rows = []
        total = self._query(count_sql, fetch=True)[0]["total"]

        if pagination:
            page = pagination.get("page", 1)
            per_page = pagination.get("per_page", 10)
            offset = (page - 1) * per_page
            sql += f" LIMIT {per_page} OFFSET {offset}"
            pagination["total_elements"] = total
        else:
            pagination = {"total_elements": total, "page": 1, "per_page": total}

        rs = self._query(sql, fetch=True)
        if rs:
            rows = [self.to_dict(row) for row in rs]
        return {
            "metadata": pagination,
            "data": rows,
        }

    def get_desc_by_id(self, _id: Any) -> Optional[Dict[str, Any]]:
        """Retrieves id and name for a specific record.

        Args:
            _id (any): The record identifier.

        Returns:
            dict|None: Row containing _id and name if found, else None.
        """
        sql = f"SELECT _id,name FROM {self.table_name} WHERE _id = ?"
        rs = self._query(sql, (_id,), fetch=True)
        row = rs[0] if rs else None
        return self.to_dict(row) if row else None

    def get_by_id(self, _id: Any) -> Optional[Dict[str, Any]]:
        """Retrieves a complete record by its ID.

        Args:
            _id (any): The record identifier.

        Returns:
            dict|None: The complete row if found, else None.
        """
        sql = f"SELECT * FROM {self.table_name} WHERE _id = ?"
        rs = self._query(sql, (_id,), fetch=True)
        row = rs[0] if rs else None
        return self.to_dict(row) if row else None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a complete record by its name.

        Args:
            name (str): The name to search for.

        Returns:
            dict|None: The complete row if found, else None.
        """
        sql = f"SELECT * FROM {self.table_name} WHERE name = ? LIMIT 1"
        rs = self._query(sql, (name,), fetch=True)
        row = rs[0] if rs else None
        return self.to_dict(row) if row else None

    def update_by_id(self, _id: Any, vo: Dict[str, Any]) -> bool:
        """Updates a record by its ID.

        Args:
            _id (any): The record identifier.
            vo (dict): Dictionary with updated data.

        Returns:
            bool: True if operation completed successfully.
        """
        vo = self.from_dict(vo)
        keys = ", ".join([f"{k} = ?" for k in vo.keys()])
        sql = f"UPDATE {self.table_name} SET {keys} WHERE _id = ?"
        values = list(vo.values()) + [_id]
        self._query(sql, values)
        if self.auto_commit:
            self.commit()
        return True

    def persist(self, vo: Dict[str, Any]) -> Any:
        """Inserts a new record.

        Args:
            vo (dict): Dictionary with record data.

        Returns:
            any: The last inserted ID.
        """
        vo = self.from_dict(vo)
        keys = ", ".join(vo.keys())
        values_placeholder = ", ".join(["?"] * len(vo))
        sql = f"INSERT INTO {self.table_name} ({keys}) VALUES ({values_placeholder}) RETURNING _id"
        values = list(vo.values())
        logger.debug(self._interpolate_sql(sql, values))
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, values)
            row = cursor.fetchone()
            lastrowid = row[0] if row else None
            if self.auto_commit:
                self.commit()
            return lastrowid
        finally:
            cursor.close()

    def persist_many(self, arr: List[Dict[str, Any]]) -> Union[int, bool]:
        """Inserts multiple records.

        Args:
            arr (list[dict]): List of dictionaries with record data.

        Returns:
            int|bool: The number of inserted rows if successful, else False.
        """
        if not arr:
            return False

        first_vo = self.from_dict(arr[0])
        keys = ", ".join(first_vo.keys())
        values_placeholder = ", ".join(["?"] * len(first_vo))
        sql = f"INSERT INTO {self.table_name} ({keys}) VALUES ({values_placeholder})"

        values_list = [tuple(self.from_dict(vo).values()) for vo in arr]
        logger.debug(self._interpolate_sql(sql, values_list))
        cursor = self.conn.cursor()
        try:
            cursor.executemany(sql, values_list)
            if self.auto_commit:
                self.commit()
            return len(arr)
        except Exception as e:
            logger.error(f"Error in persist_many: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return False
        finally:
            cursor.close()

    def delete_by_id(self, _id: Any) -> bool:
        """Deletes a record by its ID.

        Args:
            _id (any): The record identifier.

        Returns:
            bool: True if operation completed successfully.
        """
        sql = f"DELETE FROM {self.table_name} WHERE _id = ?"
        self._query(sql, (_id,))
        if self.auto_commit:
            self.commit()
        return True

    def delete_all(self) -> bool:
        """Deletes all records from the table.

        Returns:
            bool: True if operation completed successfully.
        """
        sql = f"DELETE FROM {self.table_name}"
        self._query(sql)
        if self.auto_commit:
            self.commit()
        return True

    def ddl(self, sql: str) -> None:
        """Executes a DDL (Data Definition Language) statement.

        Args:
            sql (str): DDL statement to execute.
        """
        sql_upper = sql.upper()
        if "AUTOINCREMENT" in sql_upper:
            # Extract table name from: CREATE TABLE IF NOT EXISTS table_name ( ...
            match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", sql, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                seq_name = f"seq_{table_name}"
                seq_sql = f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START 1;"
                logger.debug(seq_sql)
                cursor = self.conn.cursor()
                cursor.execute(seq_sql)
                cursor.close()
                # Now replace AUTOINCREMENT and standard SQLite definition
                sql = re.sub(
                    r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
                    f"INTEGER PRIMARY KEY DEFAULT nextval('{seq_name}')",
                    sql,
                    flags=re.IGNORECASE
                )
        logger.debug(sql)
        cursor = self.conn.cursor()
        cursor.execute(sql)
        cursor.close()

    def count_all(self, where_clause: Optional[str] = None, params: Optional[Union[Tuple[Any, ...], List[Any]]] = None) -> int:
        """Count all records in the table with optional where clause.

        Args:
            where_clause (str, optional): SQL WHERE clause. Defaults to None.
            params (tuple, optional): Parameters for the WHERE clause. Defaults to None.

        Returns:
            int: Total count of records
        """
        sql = f"SELECT COUNT(*) AS total FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        logger.debug(sql)
        result = self._query(sql, params or (), fetch=True)
        return result[0]["total"] if result else 0
