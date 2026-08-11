"""Unit tests for HTML -> text extraction (URL ingestion, pure function)."""

from __future__ import annotations

from app.ingestion.web import extract_html_text

HTML = """
<html>
  <head><title>  Example Page  </title></head>
  <body>
    <nav>menu here</nav>
    <script>var x = 1;</script>
    <style>.a{color:red}</style>
    <h1>Welcome</h1>
    <p>This is the body text.</p>
  </body>
</html>
"""


def test_extracts_title_and_visible_text() -> None:
    text, title = extract_html_text(HTML)
    assert title == "Example Page"
    assert "Welcome" in text
    assert "This is the body text." in text


def test_strips_scripts_and_styles() -> None:
    text, _ = extract_html_text(HTML)
    assert "var x" not in text
    assert "color:red" not in text
