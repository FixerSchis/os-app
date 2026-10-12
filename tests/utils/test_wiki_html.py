import html

from utils.wiki_html import highlight_text, sanitize_wiki_html


def test_sanitize_keeps_editor_formatting():
    value = (
        "<p>Hello <strong>bold</strong> and <i>italic</i></p>"
        "<ul><li>one</li></ul>"
        "<h2>Title</h2>"
        '<figure class="table"><table><tbody><tr>'
        '<td colspan="2">cell</td></tr></tbody></table></figure>'
        '<a href="https://example.com" target="_blank">site</a>'
        '<a href="/wiki/rules">rules</a>'
        '<a href="mailto:crew@example.com">mail</a>'
    )

    cleaned = sanitize_wiki_html(value)

    assert "<strong>bold</strong>" in cleaned
    assert "<i>italic</i>" in cleaned
    assert "<ul><li>one</li></ul>" in cleaned
    assert "<h2>Title</h2>" in cleaned
    assert 'class="table"' in cleaned
    assert 'colspan="2"' in cleaned
    assert 'href="https://example.com"' in cleaned
    assert 'target="_blank"' in cleaned
    assert 'href="/wiki/rules"' in cleaned
    assert 'href="mailto:crew@example.com"' in cleaned
    assert 'rel="noopener noreferrer"' in cleaned


def test_sanitize_strips_scripts_handlers_and_unsafe_urls():
    value = (
        "<p>Visible</p>"
        "<script>wiki-xss-marker</script>"
        '<img src="x" onerror="wiki-xss-marker">'
        '<a href="javascript:wiki-xss-marker">bad</a>'
        '<a href="JaVaScRiPt:wiki-xss-marker">bad</a>'
        '<a href="data:text/html,wiki-xss-marker">bad</a>'
        '<a href="https://example.com" target="_top">top</a>'
        '<p onclick="wiki-xss-marker">Hi</p>'
        "</textarea><img src=x onerror=wiki-xss-marker>"
    )

    cleaned = sanitize_wiki_html(value)

    assert "wiki-xss-marker" not in cleaned
    assert "<script" not in cleaned
    assert "<img" not in cleaned
    assert "javascript:" not in cleaned.lower()
    assert "onclick" not in cleaned
    assert "onerror" not in cleaned
    assert 'target="_top"' not in cleaned
    assert "<p>Visible</p>" in cleaned
    assert "<p>Hi</p>" in cleaned


def test_sanitize_empty_values():
    assert sanitize_wiki_html(None) == ""
    assert sanitize_wiki_html("") == ""
    assert sanitize_wiki_html("plain text") == "plain text"


def test_highlight_text_escapes_before_marking():
    value = '<script>alert("Findme")</script>'

    highlighted = highlight_text(value, "Findme")

    assert "<script>" not in highlighted
    assert "&lt;script&gt;" in highlighted
    assert "<mark>Findme</mark>" in highlighted
    assert html.escape(value, quote=True).replace("Findme", "<mark>Findme</mark>") == highlighted


def test_highlight_text_is_case_insensitive_and_escapes_unmatched_text():
    assert highlight_text("Wiki Page", "wiki") == "<mark>Wiki</mark> Page"
    assert highlight_text("A & B <c>", "") == "A &amp; B &lt;c&gt;"
    assert highlight_text(None, "q") == ""
