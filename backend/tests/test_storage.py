from backend.infrastructure.storage import StorageClient


def _client_with_public_base(public_base_url: str) -> StorageClient:
    client = object.__new__(StorageClient)
    client.public_base_url = StorageClient._normalize_public_base_url(public_base_url)
    return client


def test_rewrite_presigned_url_to_same_origin_minio_prefix():
    client = _client_with_public_base("/minio")

    public_url = client._to_public_url(
        "http://localhost:9000/glacier-portrait-raw/users/1/left.jpg?X-Amz-SignedHeaders=host"
    )

    assert public_url == "/minio/glacier-portrait-raw/users/1/left.jpg?X-Amz-SignedHeaders=host"
    assert "localhost:9000" not in public_url


def test_rewrite_presigned_url_to_absolute_public_prefix():
    client = _client_with_public_base("https://actors.example.com/minio")

    public_url = client._to_public_url(
        "http://localhost:9000/glacier-style-generated/users/1/result.png?X-Amz-Expires=43200"
    )

    assert public_url == "https://actors.example.com/minio/glacier-style-generated/users/1/result.png?X-Amz-Expires=43200"
    assert "localhost:9000" not in public_url


def test_normalize_public_base_url_adds_leading_slash_for_relative_prefix():
    assert StorageClient._normalize_public_base_url("minio/") == "/minio"
