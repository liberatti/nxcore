import json
from typing import Any, Dict, List, Optional, Union

import pymongo
from bson import ObjectId
from marshmallow import Schema, fields
from pymongo.errors import PyMongoError

from nxcore.middleware.logging_manager import logger
from nxcore.repository.schemas.page_meta_schema import PageMetaSchema


class MongoDAO:
    """Base class for MongoDB data access.

    This class provides an interface for basic CRUD operations
    and additional functionalities like pagination, data export and import.

    Attributes:
        __DB_NAME__ (str): MongoDB database name
        database: MongoDB database instance
        collection_name (str): Collection name
        collection: MongoDB collection reference
        schema: Marshmallow schema for validation and serialization
    """

    def __init__(
        self, url: Any, collection_name: str, schema: Optional[type[Schema]] = None, database: str = "app"
    ) -> None:
        """Initializes the DAO with the specified collection and schema.

        Args:
            url (any): MongoDB connection URL string.
            collection_name (str): MongoDB collection name.
            schema (type[Schema], optional): Marshmallow schema for validation.
            database (str, optional): Target database name. Defaults to "app".
        """
        self.collection = None
        self.__DB_NAME__ = database
        self.__mongo_url = url
        self.collection_name = collection_name
        self.client = None
        self.pageSchema = None
        self.schema = None
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
            self.schema = schema()
        self.connect()

    def connect(self) -> None:
        """Establish connection to MongoDB."""
        if not self.client:
            self.client = pymongo.MongoClient(
                str(self.__mongo_url),
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=10000
            )
            self.collection = self.client[f"{self.__DB_NAME__}"][self.collection_name]

    def is_connected(self) -> bool:
        """Check if the connection to MongoDB is established and credentials are valid.

        Returns:
            bool: True if connection is valid, False otherwise.
        """
        if self.client is None:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the connection to MongoDB."""
        if self.client:
            self.client.close()
            self.client = None

    def __enter__(self) -> "MongoDAO":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def json_load(self, json_data: Any) -> Any:
        """Loads and validates JSON data using the assigned schema.

        Args:
            json_data (dict): The JSON data to load.

        Returns:
            object: The loaded and validated data.
        """
        if self.schema:
            return self.schema.load(json_data)
        else:
            return json.loads(json_data) if isinstance(json_data, str) else json_data

    def json_dump(self, vo: Any) -> Any:
        """Serializes an object using the assigned schema.

        Args:
            vo (object): The object to serialize.

        Returns:
            dict: The serialized data.
        """
        return self.schema.dump(vo) if self.schema else vo

    def _from_dict(self, vo: Dict[str, Any]) -> None:
        """Converts the '_id' field from string to ObjectId in-place.

        Args:
            vo (dict): The dictionary to convert.
        """
        if vo and "_id" in vo and vo["_id"]:
            try:
                vo["_id"] = ObjectId(vo["_id"])
            except Exception:
                pass

    def _to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Converts the '_id' field from ObjectId to string in-place.

        Args:
            vo (dict): The dictionary to convert.

        Returns:
            dict: The modified dictionary.
        """
        if vo and "_id" in vo:
            vo["_id"] = str(vo["_id"])
        return vo

    def _fetch_all(self, rs: Dict[str, Any], pagination: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processes the result set from a faceted aggregate query, applying pagination metadata.

        Args:
            rs (dict): The result set from MongoDB.
            pagination (dict, optional): Pagination parameters and where to store metadata.

        Returns:
            dict: A dictionary containing 'metadata' and 'data'.
        """
        rows = rs.get("data", [])
        if pagination:
            _meta = rs.get("pagination")
            if not _meta or len(_meta) == 0:
                _meta = [{"total": 0}]
            pagination.update({"total_elements": _meta[0].get("total", 0)})
        else:
            te = len(rows)
            pagination = {"total_elements": te, "page": 1, "per_page": te}

        for r in rows:
            self._to_dict(r)
        return {
            "metadata": pagination,
            "data": rows,
        }

    def get_all(self, pagination: Optional[Dict[str, Any]] = None, filters: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Retrieves all documents from the collection with optional pagination and filtering.

        Args:
            pagination (dict, optional): Pagination parameters ('page', 'per_page').
            filters (list, optional): List of MongoDB match filters.

        Returns:
            dict: Paginated results including metadata.
        """
        query = []
        if pagination:
            query.append(
                {
                    "$facet": {
                        "data": [
                            {
                                "$skip": (
                                    (pagination["page"] - 1) * pagination["per_page"]
                                )
                            },
                            {"$limit": pagination["per_page"]},
                        ],
                        "pagination": [{"$count": "total"}],
                    }
                }
            )
        else:
            query.append({"$facet": {"data": []}})

        if filters:
            query.insert(0, {"$match": {}})
            for f in filters:
                query[0]["$match"].update(f)

        logger.debug(query)
        rs = list(self.collection.aggregate(query))[0]
        return self._fetch_all(rs, pagination=pagination)

    def get_descr_by_id(self, _id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """Retrieves a document's ID and name by its ID.

        Args:
            _id (str or ObjectId): The document ID.

        Returns:
            dict or None: A dictionary with '_id' and 'name' if found, otherwise None.
        """
        target_id = ObjectId(_id) if isinstance(_id, str) else _id
        rs = self.collection.find_one({"_id": target_id})
        if rs and "_id" in rs and "name" in rs:
            return {"_id": str(rs["_id"]), "name": rs["name"]}
        return None

    def get_by_id(self, _id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """Retrieves a complete document by its ID.

        Args:
            _id (str or ObjectId): The document ID.

        Returns:
            dict or None: The document if found, otherwise None.
        """
        target_id = ObjectId(_id) if isinstance(_id, str) else _id
        rs = self.collection.find_one({"_id": target_id})
        if rs:
            self._to_dict(rs)
        return rs

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document by its 'name' field.

        Args:
            name (str): The name to search for.

        Returns:
            dict or None: The document if found, otherwise None.
        """
        rs = self.collection.find_one({"name": name})
        if rs:
            self._to_dict(rs)
        return rs

    def update_by_query(self, query: Dict[str, Any], vo: Dict[str, Any]) -> bool:
        """Updates a single document matching the specified query.

        Args:
            query (dict): MongoDB query to find the document.
            vo (dict): Data to update.

        Returns:
            bool: True if a document was modified, False otherwise.
        """
        self._from_dict(vo)
        logger.debug(query)
        rs = self.collection.update_one(query, {"$set": vo})
        return rs.modified_count > 0

    def update_by_id(self, _id: Union[str, ObjectId], vo: Dict[str, Any]) -> bool:
        """Updates a document by ID.

        Args:
            _id (Union[str, ObjectId]): Document ID
            vo (Dict[str, Any]): Dictionary with updated data

        Returns:
            bool: True if the document was updated, False otherwise

        Raises:
            PyMongoError: If an error occurs during the update operation
        """
        try:
            self._from_dict(vo)
            query = {"$set": vo}
            logger.debug(query)
            target_id = ObjectId(_id) if isinstance(_id, str) else _id
            rs = self.collection.update_one({"_id": target_id}, query)
            self._to_dict(vo)
            return rs.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating document: {str(e)}")
            raise

    def persist(self, vo: Dict[str, Any]) -> str:
        """Persists a new document in the collection.

        Args:
            vo (Dict[str, Any]): Dictionary with document data

        Returns:
            str: ID of the inserted document

        Raises:
            PyMongoError: If an error occurs during the insert operation
        """
        try:
            if "_id" in vo:
                vo.pop("_id")
            self._from_dict(vo)
            pk = self.collection.insert_one(vo)
            vo["_id"] = str(pk.inserted_id)
            return str(pk.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error persisting document: {str(e)}")
            raise

    def persist_many(self, arr: List[Dict[str, Any]]) -> Any:
        """Inserts multiple documents into the collection.

        Args:
            arr (list): List of dictionaries to insert.

        Returns:
            pymongo.results.InsertManyResult: The result of the insert operation.
        """
        return self.collection.insert_many(arr)

    def delete_by_id(self, _id: Union[str, ObjectId]) -> bool:
        """Deletes a single document by its ID.

        Args:
            _id (str or ObjectId): The document ID.

        Returns:
            bool: True if a document was deleted, False otherwise.
        """
        target_id = ObjectId(_id) if isinstance(_id, str) else _id
        dr = self.collection.delete_one({"_id": target_id})
        return dr.deleted_count > 0

    def delete_all(self) -> bool:
        """Deletes all documents from the collection.

        Returns:
            bool: True if any documents were deleted, False otherwise.
        """
        dr = self.collection.delete_many({})
        return dr.deleted_count > 0
