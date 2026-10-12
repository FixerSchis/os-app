"""Sanitize wiki editor HTML and safely highlight search matches."""

import html
import re

import nh3

# Tags the wiki editor produces: paragraphs, headings, lists, links, emphasis, tables.
_ALLOWED_TAGS = {
    "a",
    "b",
    "blockquote",
    "br",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "i",
    "li",
    "ol",
    "p",
    "s",
    "strong",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
}

_ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}

# target is restricted here instead of _ALLOWED_ATTRIBUTES. nh3 rejects an
# attribute listed in both places.
_TAG_ATTRIBUTE_VALUES = {
    "a": {"target": {"_blank"}},
}

_ALLOWED_CLASSES = {
    "figure": {"table"},
}

_URL_SCHEMES = {"http", "https", "mailto"}


def sanitize_wiki_html(value):
    """Keep editor formatting and drop scripts, event handlers, and unsafe URLs."""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return nh3.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        tag_attribute_values=_TAG_ATTRIBUTE_VALUES,
        allowed_classes=_ALLOWED_CLASSES,
        url_schemes=_URL_SCHEMES,
        link_rel="noopener noreferrer",
    )


def highlight_text(text, query):
    """Escape text and wrap case-insensitive query matches in <mark> tags.

    Titles and excerpts are escaped before the mark tags are added so stored
    characters are shown as text.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    if not query:
        return html.escape(text, quote=True)
    if not isinstance(query, str):
        query = str(query)
    if not query:
        return html.escape(text, quote=True)

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    parts = []
    cursor = 0
    for match in pattern.finditer(text):
        parts.append(html.escape(text[cursor : match.start()], quote=True))
        parts.append("<mark>")
        parts.append(html.escape(match.group(0), quote=True))
        parts.append("</mark>")
        cursor = match.end()
    parts.append(html.escape(text[cursor:], quote=True))
    return "".join(parts)
