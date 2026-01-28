from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import random

class FlakyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        # Simulate race condition vulnerability or randomness
        if random.random() < 0.3:
            time.sleep(0.1)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error (Simulated)")
        else:
            time.sleep(0.01)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Data Saved")

if __name__ == "__main__":
    print("Starting flaky server on port 8999...")
    HTTPServer(("localhost", 8999), FlakyHandler).serve_forever()
