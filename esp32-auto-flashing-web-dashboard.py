import subprocess
import threading
import time
import os
from flask import Flask
from flask_socketio import SocketIO

# --- 1. INITIALIZE WEB SERVER ---
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- 2. CONFIGURATION & DEVICE MAPPING ---
FIRMWARE_A = "/home/thingsboardclass/ESP_CODE/vibration_sound.ino.merged.bin"
FIRMWARE_B = "/home/thingsboardclass/ESP_CODE/contactless_haii.ino.merged.bin"
FIRMWARE_C = "/home/thingsboardclass/ESP_CODE/local_hello.ino.merged.bin"
FIRMWARE_D = "/home/thingsboardclass/ESP_CODE/obstacle_no_sound.ino.merged.bin"

DEVICE_ASSIGNMENTS = {
    "c0:cd:d6:cf:37:74": FIRMWARE_A,
    "c0:cd:d6:ce:0a:60": FIRMWARE_B,
    "fc:f5:c4:65:d2:f8": FIRMWARE_C,
    "14:33:5c:09:e1:28": FIRMWARE_D
    # Add your remaining 4 MACs here...
}

# Trackers
active_slots = {}  # { usb_path: mac }
fail_counts = {}   # { usb_path: count }

# --- 3. HELPER FUNCTIONS ---

def stream_log(message):
    """Sends logs to the browser and the terminal"""
    timestamp = time.strftime("%H:%M:%S")
    socketio.emit('new_log', {'time': timestamp, 'msg': message})
    print(f"[{timestamp}] {message}")

def get_usb_info(port):
    """Identifies the device MAC and its physical USB slot"""
    try:
        mac_res = subprocess.check_output(
            f"esptool --port {port} --baud 115200 read_mac", 
            shell=True, stderr=subprocess.STDOUT, timeout=8
        ).decode()
        mac = next(line.split("MAC: ")[1].strip() for line in mac_res.split('\n') if "MAC: " in line)
        
        path_res = subprocess.check_output(f"udevadm info -q path -n {port}", shell=True).decode()
        usb_path = path_res.strip().split('/')[-3] 
        return mac, usb_path
    except:
        return None, None

# --- 4. THE CORE FLASHING ENGINE (RUNS IN BACKGROUND) ---

def flasher_backend():
    stream_log("🚀 Flashing Engine Started. Waiting for devices...")
    
    while True:
        ports = [f"/dev/{p}" for p in os.listdir('/dev') if p.startswith('ttyUSB')]
        current_paths = []

        for port in ports:
            mac, usb_path = get_usb_info(port)
            
            if usb_path:
                current_paths.append(usb_path)
                
                # Logic: Flash if Slot is not 'Locked' and hasn't failed too many times
                if usb_path not in active_slots and fail_counts.get(usb_path, 0) < 5:
                    firmware = DEVICE_ASSIGNMENTS.get(mac)
                    
                    if firmware:
                        attempt = fail_counts.get(usb_path, 0) + 1
                        stream_log(f"⚡ [Slot {usb_path}] New Device {mac}. Attempt {attempt}...")
                        
                        try:
                            # 60s Timeout for stability over Hubs
                            # Stability flags: -fm dio (flash mode) and -ff 26m (flash freq)
                            subprocess.run([
                                "esptool", "--port", port, "--baud", "460800", 
                                "write-flash", "-z", "-fm", "dio", "-ff", "26m", "0x0", firmware
                            ], check=True, timeout=60, stdout=subprocess.DEVNULL)
                            
                            active_slots[usb_path] = mac
                            fail_counts[usb_path] = 0 
                            stream_log(f"✅ [Slot {usb_path}] SUCCESS! Running {os.path.basename(firmware)}")
                            
                        except subprocess.TimeoutExpired:
                            fail_counts[usb_path] = fail_counts.get(usb_path, 0) + 1
                            stream_log(f"🛑 [Slot {usb_path}] TIMEOUT. Will retry.")
                        except Exception as e:
                            fail_counts[usb_path] = fail_counts.get(usb_path, 0) + 1
                            stream_log(f"❌ [Slot {usb_path}] FAILED. Errors detected.")
                    else:
                        stream_log(f"⚠️ Unknown MAC {mac} at {usb_path}. Ignoring.")

        # Cleanup: Remove disconnected slots so they can be re-flashed later
        for p in list(active_slots.keys()):
            if p not in current_paths:
                stream_log(f"🔌 Slot {p} unplugged. Memory cleared.")
                del active_slots[p]
                if p in fail_counts: del fail_counts[p]

        time.sleep(3)

# --- 5. WEB INTERFACE (HTML/CSS/JS) ---

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IoT Provisioning Dashboard</title>
        <style>
            body { background: #0f0f0f; color: #00ff41; font-family: 'Courier New', Courier, monospace; margin: 0; padding: 20px; }
            .terminal { 
                background: #000; border: 2px solid #333; height: 80vh; 
                padding: 15px; overflow-y: auto; box-shadow: 0 0 20px rgba(0,255,0,0.1);
            }
            .entry { margin-bottom: 8px; border-bottom: 1px solid #1a1a1a; padding-bottom: 4px; }
            .time { color: #008f11; font-weight: bold; margin-right: 15px; }
            h2 { color: #fff; text-shadow: 0 0 10px #00ff41; }
            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h2>📡 ESP32 PROVISIONING CONSOLE</h2>
        <div class="terminal" id="terminal">
            <div class="entry">--- Waiting for first connection ---</div>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            var socket = io();
            var term = document.getElementById('terminal');
            
            socket.on('new_log', function(data) {
                var div = document.createElement('div');
                div.className = 'entry';
                div.innerHTML = '<span class="time">[' + data.time + ']</span> ' + data.msg;
                term.appendChild(div);
                term.scrollTop = term.scrollHeight; // Auto-scroll to bottom
            });
        </script>
    </body>
    </html>
    """

# --- 6. START THE ENGINE ---

if __name__ == '__main__':
    # Start the flasher in a separate background thread
    daemon_thread = threading.Thread(target=flasher_backend, daemon=True)
    daemon_thread.start()
    
    # Start the web server on Port 5000
    # Accessible via http://your-pi-ip:5000
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
