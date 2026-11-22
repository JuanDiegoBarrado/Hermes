import boto3

from application.ports.writer import Writer


class S3Writer(Writer):
    """Escribe un objeto en S3. Opciones: `bucket`, `key`.

    Las credenciales las resuelve boto3 (variables de entorno, ~/.aws, rol...).
    """

    def __init__(self, bucket: str, key: str) -> None:
        self._bucket = bucket
        self._key = key

    def write(self, content: bytes) -> None:
        boto3.client("s3").put_object(Bucket=self._bucket, Key=self._key, Body=content)
