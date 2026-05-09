"""
generer_pdf.py
Genererer PDF av rapport_live.html via Chrome headless.
Kjør: python generer_pdf.py
"""

import os
import re
import subprocess
import threading
import time
import http.server
import socketserver

# --- Konfigurasjon ---
KILDE_HTML   = "rapport_live.html"
OUTPUT_PDF   = r"005 report\Prosjekt_LOG650_ME_Morten_Eidsvag.pdf"
TEMP_HTML    = "rapport_print_temp.html"
PORT         = 8766
CHROME       = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# --- Lag print-versjon av HTML ---
with open(KILDE_HTML, "r", encoding="utf-8") as f:
    html = f.read()

# Fjern auto-refresh
html = re.sub(r'<meta http-equiv="refresh"[^>]*>\s*', "", html)

# Injiser print-CSS og MathJax-klar-signal
print_css = """
<style>
  @page { size: A4; margin: 2.5cm 3cm; }
  body::after { display: none !important; }
  body { background: white !important; padding: 0 !important; }
  .container { box-shadow: none !important; }
</style>
<script>
  // Sett window.mjReady = true når MathJax er ferdig
  window.mjReady = false;
  document.addEventListener('DOMContentLoaded', function() {
    if (window.MathJax && window.MathJax.startup) {
      window.MathJax.startup.promise.then(function() {
        window.mjReady = true;
      });
    } else {
      // Fallback hvis MathJax ikke lastes
      window.mjReady = true;
    }
  });
</script>
"""
html = html.replace("</head>", print_css + "</head>")

with open(TEMP_HTML, "w", encoding="utf-8") as f:
    f.write(html)

# --- Start lokal HTTP-server ---
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

httpd = socketserver.TCPServer(("", PORT), QuietHandler)
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()

# Vent til serveren svarer
for _ in range(20):
    try:
        import socket
        s = socket.create_connection(("localhost", PORT), timeout=0.5)
        s.close()
        break
    except OSError:
        time.sleep(0.3)

print(f"Server klar på http://localhost:{PORT}")
print(f"Genererer PDF: {OUTPUT_PDF}")

# --- Kjør Chrome headless ---
abs_output = os.path.abspath(OUTPUT_PDF)
url = f"http://localhost:{PORT}/{TEMP_HTML}"

result = subprocess.run([
    CHROME,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--print-to-pdf=" + abs_output,
    "--virtual-time-budget=10000",
    url,
], capture_output=True, text=True, timeout=60)

# --- Rydd opp ---
httpd.shutdown()
os.remove(TEMP_HTML)

# --- Resultat ---
if result.returncode == 0 and os.path.exists(abs_output):
    size_kb = os.path.getsize(abs_output) // 1024
    print(f"PDF generert: {abs_output} ({size_kb} KB)")
else:
    print(f"FEIL (kode {result.returncode})")
    if result.stderr:
        print(result.stderr[:500])
