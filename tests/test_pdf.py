from app.services import pdf


def test_chunk_pages_splits_with_overlap(monkeypatch):
    # force small, predictable windows so the math is easy to check
    from app import config

    monkeypatch.setattr(config.get_settings(), "chunk_size", 10, raising=False)
    monkeypatch.setattr(config.get_settings(), "chunk_overlap", 2, raising=False)

    chunks = pdf.chunk_pages(["abcdefghijklmno"])  # 15 chars on page 1

    assert all(c["page"] == 1 for c in chunks)
    assert chunks[0]["text"] == "abcdefghij"
    # next window starts at size - overlap = 8
    assert chunks[1]["text"].startswith("ij")


def test_chunk_pages_tracks_page_numbers():
    chunks = pdf.chunk_pages(["first page text", "", "third page text"])
    pages = {c["page"] for c in chunks}
    assert pages == {1, 3}  # the empty page 2 is skipped
