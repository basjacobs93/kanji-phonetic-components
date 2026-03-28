"""Dev server: serves the static site on http://localhost:8000"""

import http.server
import os

if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), "site"))
    server = http.server.HTTPServer(("", 8000), http.server.SimpleHTTPRequestHandler)
    print("Serving at http://localhost:8000")
    server.serve_forever()
