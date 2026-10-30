#!/usr/bin/env python3
"""
MelanoScan simple proxy + static file server.
Keeps the Roboflow key on the server side.
"""
import os
import json
import cgi
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROBOFLOW_KEY = os.environ.get("ROBOFLOW_PRIVATE_KEY") or os.environ.get("ROBOFLOW_PUBLIC_KEY") or "rf_1Bl00IYBBrOYOnh2k7snb9VOFoY2"
CLASS_MODEL = "techguru-3vxeq/skin_lesion_classification-lyqqy"
CLASS_VER = "1"
DET_MODEL = "techguru-3vxeq/skin-cancer-detection-3tjv9"
DET_VER = "1"
PORT = int(os.environ.get("PORT", 8080))

def call_roboflow(host, path, image_bytes, filename="lesion.jpg", content_type="image/jpeg"):
    boundary = "----MelanoScanBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()

    url = f"https://{host}{path}?api_key={ROBOFLOW_KEY}"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))

    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode())

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        if self.path == "/api/health" or self.path.startswith("/api/health?"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "service": "MelanoScan Proxy",
                "models": {"classification": CLASS_MODEL, "detection": DET_MODEL}
            }).encode())
            return
        if self.path == "/" or not os.path.exists(self.translate_path(self.path)):
            self.path = "/index.html"
        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path.startswith("/api/analyze"):
            try:
                ctype, pdict = cgi.parse_header(self.headers.get("Content-Type", ""))
                if ctype != "multipart/form-data":
                    self._json_error(400, "Expected multipart/form-data")
                    return
                pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type")},
                    keep_blank_values=True
                )
                if "file" not in form:
                    self._json_error(400, "No file field")
                    return
                fileitem = form["file"]
                image_bytes = fileitem.file.read()
                filename = fileitem.filename or "lesion.jpg"
                content_type = fileitem.type or "image/jpeg"

                class_data = None
                detect_data = None
                try:
                    class_data = call_roboflow(
                        "classify.roboflow.com",
                        f"/{CLASS_MODEL}/{CLASS_VER}",
                        image_bytes, filename, content_type
                    )
                except Exception as e:
                    print("Classification error:", e)

                try:
                    detect_data = call_roboflow(
                        "detect.roboflow.com",
                        f"/{DET_MODEL}/{DET_VER}",
                        image_bytes, filename, content_type
                    )
                except Exception as e:
                    print("Detection skipped:", e)

                if not class_data:
                    self._json_error(502, "Roboflow classification failed")
                    return

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "classification": class_data,
                    "detection": detect_data,
                    "source": "roboflow-proxy"
                }).encode())
            except Exception as e:
                print("Proxy error:", e)
                self._json_error(500, str(e))
            return
        self._json_error(404, "Not found")

    def _json_error(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg, "fallback": True}).encode())

    def log_message(self, format, *args):
        print("[%s] %s" % (self.log_date_time_string(), format % args))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"MelanoScan running at http://localhost:{PORT}")
    print("Proxy: POST /api/analyze")
    server.serve_forever()
