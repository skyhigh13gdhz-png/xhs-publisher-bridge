from app.feishu import extract_attachment_tokens, normalize_text


def test_extract_attachment_tokens():
    value = [{"file_token": "a"}, {"fileToken": "b"}, {"name": "x"}]
    assert extract_attachment_tokens(value) == ["a", "b"]


def test_normalize_text():
    assert normalize_text("abc") == "abc"
    assert normalize_text([{"text": "a"}, {"text": "b"}]) == "ab"
