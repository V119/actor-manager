import base64

from backend.application.style_generation import LangChainStyleImageGenerator, StyleReferenceImage


def test_parse_bailian_output_choice_with_image_url():
    generator = LangChainStyleImageGenerator()
    expected_bytes = b"fake-image-bytes"
    generator._download_remote_image = lambda _url: (expected_bytes, "image/png")  # type: ignore[method-assign]

    payload = {
        "output": {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"image": "https://example.com/result.png"},
                        ]
                    }
                }
            ]
        },
        "request_id": "test-request-id",
    }

    image_bytes, mime_type = generator._parse_image_response(payload)
    assert image_bytes == expected_bytes
    assert mime_type == "image/png"


def test_parse_bailian_output_choice_with_data_uri():
    generator = LangChainStyleImageGenerator()
    raw = b"png-content"
    data_uri = f"data:image/png;base64,{base64.b64encode(raw).decode('utf-8')}"
    payload = {
        "output": {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"image": data_uri},
                        ]
                    }
                }
            ]
        },
        "request_id": "test-request-id",
    }

    image_bytes, mime_type = generator._parse_image_response(payload)
    assert image_bytes == raw
    assert mime_type == "image/png"


def test_build_multimodal_content_uses_three_reference_images():
    generator = LangChainStyleImageGenerator()
    refs = [
        StyleReferenceImage(data=b"left-bytes", filename="left.jpg"),
        StyleReferenceImage(data=b"front-bytes", filename="front.jpg"),
        StyleReferenceImage(data=b"right-bytes", filename="right.jpg"),
    ]

    content = generator._build_multimodal_content("prompt", refs)

    assert len(content) == 4
    assert content[0] == {"text": "prompt"}
    assert "image" in content[1]
    assert "image" in content[2]
    assert "image" in content[3]
