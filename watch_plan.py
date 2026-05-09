"""
watch_plan.py — Live preview av rapport og prosjektstyringsplan
Kjør: python watch_plan.py
Starter lokal webserver på http://localhost:8765 og åpner Chrome.
"""

import os
import subprocess
import time
import threading
import http.server
import socketserver
import webbrowser
import socket

PORT = 8765

FILES = [
    {
        "watch": "012 fase 2 - plan/Prosjekt_LOG650 ME",
        "output": "rapport_live.html",
        "title": "Rapport LOG650 – Morten Eidsvåg",
    },
    {
        "watch": "012 fase 2 - plan/Prosjektstyrings plan 1.0",
        "output": "plan_live.html",
        "title": "Prosjektstyringsplan LOG650",
    },
]

def pandoc_cmd(watch_file, output_html, title):
    return [
        "pandoc", watch_file,
        "-o", output_html,
        "--standalone",
        "--metadata", f"title={title}",
        "--css", "plan_style.css",
        "--template", "plan_template.html",
        "--mathjax",
    ]

def build(f):
    cmd = pandoc_cmd(f["watch"], f["output"], f["title"])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  [OK] {f['output']}")
    else:
        print(f"  [FEIL] {f['output']}: {result.stderr.strip()}")

def start_server():
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None  # Skru av logg-støy
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

def watch():
    mtimes = {f["watch"]: 0 for f in FILES}

    print(f"Bygger filer...")
    for f in FILES:
        build(f)

    print(f"\nStarter webserver på http://localhost:{PORT}")
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Vent til serveren faktisk svarer (maks 10 sekunder)
    for _ in range(20):
        try:
            s = socket.create_connection(("localhost", PORT), timeout=0.5)
            s.close()
            break
        except OSError:
            time.sleep(0.5)
    else:
        print("FEIL: Klarte ikke starte webserveren. Sjekk om port 8765 er i bruk.")
        return

    rapport_url = f"http://localhost:{PORT}/rapport_live.html"
    plan_url    = f"http://localhost:{PORT}/plan_live.html"

    print(f"\nÅpner i nettleser:")
    print(f"  Rapport:         {rapport_url}")
    print(f"  Prosjektplan:    {plan_url}")
    print(f"\nTrykk Ctrl+C for å avslutte.\n")

    webbrowser.open(rapport_url)
    webbrowser.open(plan_url)

    while True:
        try:
            for f in FILES:
                mtime = os.path.getmtime(f["watch"])
                if mtime != mtimes[f["watch"]]:
                    if mtimes[f["watch"]] != 0:
                        print(f"Endring oppdaget i {f['watch']} ({time.strftime('%H:%M:%S')})...")
                        build(f)
                    mtimes[f["watch"]] = mtime
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nAvslutter.")
            break
        except FileNotFoundError as e:
            print(f"Finner ikke filen: {e}")
            break

if __name__ == "__main__":
    watch()
