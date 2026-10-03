from datetime import date
from pathlib import Path

from jinja2 import Template
from playwright.sync_api import sync_playwright

from report_data import get_report_data

TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: Arial, sans-serif; color: #222; margin: 40px; }
  h1 { border-bottom: 2px solid #333; padding-bottom: 8px; }
  h2 { margin-top: 32px; break-after: avoid; }
  .summary { display: flex; gap: 40px; margin: 20px 0; }
  .summary-box { border: 1px solid #ccc; border-radius: 6px; padding: 12px 20px; }
  .summary-box .label { font-size: 12px; color: #666; text-transform: uppercase; }
  .summary-box .value { font-size: 24px; font-weight: bold; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  thead { display: table-header-group; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #ddd; }
  th { background-color: #f2f2f2; }
  tr { break-inside: avoid; }
</style>
</head>
<body>
  <h1>Book Catalog Report - {{ report_date }}</h1>

  <div class="summary">
    <div class="summary-box">
      <div class="label">Total Books</div>
      <div class="value">{{ total_books }}</div>
    </div>
    <div class="summary-box">
      <div class="label">Average Price</div>
      <div class="value">&pound;{{ "%.2f"|format(average_price) }}</div>
    </div>
  </div>

  <h2>Top 5 Most Expensive Books</h2>
  <table>
    <thead><tr><th>Title</th><th>Price</th></tr></thead>
    <tbody>
      {% for book in top_5_expensive %}
      <tr><td>{{ book.title }}</td><td>&pound;{{ "%.2f"|format(book.price) }}</td></tr>
      {% endfor %}
    </tbody>
  </table>

  <h2>Books per Rating</h2>
  <table>
    <thead><tr><th>Rating</th><th>Count</th></tr></thead>
    <tbody>
      {% for row in books_per_rating %}
      <tr><td>{{ row.rating }} star{{ "s" if row.rating != 1 else "" }}</td><td>{{ row.count }}</td></tr>
      {% endfor %}
    </tbody>
  </table>

  <h2>All Books</h2>
  <table>
    <thead><tr><th>#</th><th>Title</th><th>Price</th><th>Rating</th></tr></thead>
    <tbody>
      {% for book in all_books %}
      <tr><td>{{ loop.index }}</td><td>{{ book.title }}</td><td>&pound;{{ "%.2f"|format(book.price) }}</td><td>{{ book.rating }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""


def render_report_pdf(output_path: str = "report.pdf") -> str:
    """Query the data, render it into HTML, then print that HTML to a PDF file."""
    data = get_report_data()
    data["report_date"] = date.today().strftime("%d %B %Y")

    template = Template(TEMPLATE_HTML)
    html = template.render(**data)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(path=output_path, format="A4", print_background=True)
        browser.close()

    return output_path


if __name__ == "__main__":
    path = render_report_pdf()
    print(f"PDF written to: {Path(path).resolve()}")