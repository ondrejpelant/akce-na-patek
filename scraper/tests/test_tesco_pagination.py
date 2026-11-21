from scraper.sources import tesco


def test_page_url_for_whole_listing_and_subcategory():
    assert tesco.page_url("", "relevance") == (
        "https://nakup.itesco.cz/shop/cs-CZ/browse/napoje/lihoviny?sortBy=relevance&count=48"
    )
    assert tesco.page_url("vodka", "price-ascending") == (
        "https://nakup.itesco.cz/shop/cs-CZ/browse/napoje/lihoviny/vodka"
        "?sortBy=price-ascending&count=48"
    )


def test_rotation_covers_every_listing_and_sort_once():
    assert len(tesco.ROTATION) == len(set(tesco.ROTATION)) == len(tesco.LISTINGS) * len(tesco.SORTS)


def test_rotation_state_advances_and_wraps(tmp_path, monkeypatch):
    state = tmp_path / ".cache" / "tesco_rotation.txt"
    monkeypatch.setattr(tesco, "_rotation_file", lambda: state)

    assert tesco._next_rotation_step() == 0          # no file yet
    tesco._save_rotation_step(5)
    assert tesco._next_rotation_step() == 5
    tesco._save_rotation_step(len(tesco.ROTATION))   # wraps to the start
    assert tesco._next_rotation_step() == 0
    state.write_text("garbage")
    assert tesco._next_rotation_step() == 0
