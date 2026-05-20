"""
generate_pdf.py — Generer PDF fra rapport med korrekt formelrendering
Bruker Playwright + Chromium som venter på MathJax før utskrift.
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
SOURCE = BASE / "012 fase 2 - plan" / "Prosjekt_LOG650 ME"
HTML   = BASE / "005 report" / "rapport_temp.html"
PDF    = BASE / "005 report" / "rapport_pandoc.pdf"

def build_html():
    """Konverter Markdown til HTML med MathJax via Pandoc."""
    cmd = [
        "pandoc", str(SOURCE),
        "-o", str(HTML),
        "--standalone",
        "--metadata", "title=Rapport LOG650 – Morten Eidsvåg",
        "--template", str(BASE / "pdf_template.html"),
        "--mathjax",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Pandoc feil: {result.stderr}")
        sys.exit(1)
    print(f"HTML generert: {HTML.name}")

def build_pdf():
    """Skriv ut HTML til PDF med Playwright — venter på MathJax."""
    from playwright.sync_api import sync_playwright

    url = HTML.as_uri()
    print(f"Åpner: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        )
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)

        # Vent til MathJax 3 er ferdig med rendering
        try:
            page.wait_for_function(
                """() => {
                    if (typeof MathJax === 'undefined') return true;
                    if (MathJax.version && MathJax.startup && MathJax.startup.promise) {
                        return MathJax.startup.promise.then(() => true);
                    }
                    return true;
                }""",
                timeout=30000
            )
        except Exception:
            pass

        # Ekstra buffer for slow renders
        page.wait_for_timeout(4000)

        page.pdf(
            path=str(PDF),
            format="A4",
            margin={"top": "2.5cm", "bottom": "2.5cm",
                    "left": "2.5cm", "right": "2.5cm"},
            print_background=True,
        )
        browser.close()

    print(f"PDF generert: {PDF} ({PDF.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    build_html()
    build_pdf()
    HTML.unlink(missing_ok=True)
    print("Ferdig!")
