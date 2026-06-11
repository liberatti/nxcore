from minio import Minio


class MinioTool:
    """
    Utility class for interacting with Minio (S3 compatible storage).

    Handles file uploads, downloads, deletions, and listing within a specific bucket.
    """

    def __init__(self, url, access_key, secret_key, bucket_name: str = "capivara"):
        """
        Initializes the MinioTool with connection credentials and bucket name.

        Args:
            url (str): Minio server URL.
            access_key (str): Access key for authentication.
            secret_key (str): Secret key for authentication.
            bucket_name (str, optional): Target bucket name. Defaults to "capivara".
        """
        self.bucket_name = bucket_name
        self.minio_client = Minio(
            f"{url}",
            access_key=access_key,
            secret_key=secret_key,
        )

    def upload_file(self, file_path: str, file_name: str, content_type: str = "application/octet-stream"):
        """
        Uploads a file to the Minio bucket.

        Args:
            file_path (str): Local path to the file.
            file_name (str): Name to store the file as in Minio.
            content_type (str, optional): MIME type of the file. Defaults to "application/octet-stream".
        """
        self.minio_client.fput_object(self.bucket_name, file_name, file_path, content_type=content_type)

    def download_file(self, file_name: str, file_path: str, content_type: str = "application/octet-stream"):
        """
        Downloads a file from the Minio bucket.

        Args:
            file_name (str): Name of the file in Minio.
            file_path (str): Local path where the file will be saved.
            content_type (str, optional): Expected MIME type. Defaults to "application/octet-stream".
        """
        self.minio_client.fget_object(self.bucket_name, file_name, file_path, content_type=content_type)

    def delete_file(self, file_name: str):
        """
        Deletes a file from the Minio bucket.

        Args:
            file_name (str): Name of the file to delete.
        """
        self.minio_client.remove_object(self.bucket_name, file_name)

    def list_files(self, prefix: str = ""):
        """
        Lists files in the Minio bucket with an optional prefix.

        Args:
            prefix (str, optional): Filter files by prefix. Defaults to "".

        Returns:
            list: Iterable of objects in the bucket.
        """
        return self.minio_client.list_objects(self.bucket_name, prefix=prefix)

    def get_file_url(self, file_name: str):
        """
        Generates a presigned URL for a file in the Minio bucket.

        Args:
            file_name (str): Name of the file.

        Returns:
            str: Presigned URL for the file.
        """
        return self.minio_client.presigned_get_object(self.bucket_name, file_name)
