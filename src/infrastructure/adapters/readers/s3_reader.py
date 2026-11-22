import boto3

from application.ports.reader import Reader


class S3Reader(Reader):
    """Lee un objeto de S3. Opciones: `bucket`, `key`.

    Las credenciales las resuelve boto3 (variables de entorno, ~/.aws, rol...).
    """

    def __init__(self, bucket: str, key: str) -> None:
        self._bucket = bucket
        self._key = key

    def read(self) -> bytes:
        response = boto3.client("s3").get_object(Bucket=self._bucket, Key=self._key)
        return response["Body"].read()
