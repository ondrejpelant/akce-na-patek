from scraper.sources.tesco import _total_pages


def test_total_pages_with_nbsp():
    html = (
        '<div class="ddsweb-pagination__results">'
        "Zobrazeno 1 až 48 z&nbsp;346&nbsp;produktů</div>"
    )
    assert _total_pages(html) == 8


def test_total_pages_plain_spaces():
    html = '<div class="ddsweb-pagination__results">Zobrazeno 1 až 24 z 346 produktů</div>'
    assert _total_pages(html) == 8


def test_total_pages_missing_falls_back_to_one():
    assert _total_pages("<div>nic</div>") == 1
