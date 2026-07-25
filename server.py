#!/c/Users/ismai/Documents/DiabloPi/.venv/Scripts/python.exe

from flask import Flask, request, jsonify, render_template_string
import base64
import os
import json
from datetime import datetime
import sys

# --- ADD THE LOCAL D4 OCR TOOL ---
sys.path.insert(0, r'C:\DiabloAI') # Add your project folder to Python path

try:
    from d4_item_tooltip_ocr import Diablo4ItemTooltipOCR
    ocr_engine = Diablo4ItemTooltipOCR()
    ocr_ready = True
    print(" OCR Engine Ready!")
except Exception as e:
    ocr_ready = False
    print(f" OCR Error: {e}")

app = Flask(__name__)

# Global storage for the last scanned item
last_scanned_item = None

# --- DASHBOARD HTML ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Diablo Loot Scanner</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Arial', sans-serif; 
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            background: rgba(30, 30, 30, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
            border: 2px solid #444;
        }
        h1 { 
            color: #f1c40f;
            text-align: center;
            text-shadow: 2px 2px 4px #000;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        .status { 
            text-align: center;
            color: #aaa;
            font-size: 1.1em;
            margin-bottom: 15px;
        }
        img { 
            max-width: 100%;
            border: 3px solid #555;
            border-radius: 8px;
            margin: 20px 0;
            display: none;
        }
        .verdict { 
            font-size: 2.2em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
        }
        .upgrade { 
            background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
            color: #fff;
            box-shadow: 0 0 20px rgba(39, 174, 96, 0.5);
        }
        .keep { 
            background: linear-gradient(135deg, #c0392b 0%, #a93226 100%);
            color: #fff;
            box-shadow: 0 0 20px rgba(192, 57, 43, 0.5);
        }
        .error {
            background: linear-gradient(135deg, #7f8c8d 0%, #566573 100%);
            color: #fff;
        }
        .data { 
            background: rgba(50, 50, 50, 0.8);
            padding: 15px;
            text-align: left;
            font-family: 'Courier New', monospace;
            margin-top: 20px;
            border-radius: 8px;
            border-left: 4px solid #f1c40f;
            font-size: 0.95em;
            line-height: 1.6;
        }
        .time { 
            text-align: center;
            color: #f39c12;
            font-size: 0.9em;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Diablo Loot Scanner</h1>
        <div class="status" id="status"> Waiting for scan...</div>
        <img id="photo" alt="Item Image">
        <div id="verdict" class="verdict"></div>
        <div class="data" id="details"></div>
        <div class="time">Last Updated: <span id="time">--:--:--</span></div>
    </div>

    <script>
        setInterval(() => {
            fetch('/latest')
                .then(r => r.json())
                .then(data => {
                    if(data.image) {
                        document.getElementById('photo').src = 'data:image/jpeg;base64,' + data.image;
                        document.getElementById('photo').style.display = 'block';
                        document.getElementById('verdict').innerText = data.verdict || "Processing...";
                        document.getElementById('status').innerText = "Last scan: " + data.time;
                        document.getElementById('time').innerText = data.time;
                        
                        if(data.data) {
                            let details = `<strong>Item:</strong> ${data.data.item_name}<br>`;
                            details += `<strong>Power:</strong> ${data.data.item_power}<br>`;
                            details += `<strong>Stats:</strong><br>`;
                            if(typeof data.data.stats === 'object') {
                                for(let key in data.data.stats) {
                                    details += `&nbsp;&nbsp;${key}: ${data.data.stats[key]}<br>`;
                                }
                            }
                            document.getElementById('details').innerHTML = details;
                        }
                        
                        // Color the verdict
                        let verdict = document.getElementById('verdict');
                        verdict.className = 'verdict';
                        if(data.verdict.includes('UPGRADE')) {
                            verdict.classList.add('upgrade');
                        } else if(data.verdict.includes('ERROR')) {
                            verdict.classList.add('error');
                        } else {
                            verdict.classList.add('keep');
                        }
                    }
                })
                .catch(err => console.log("Error:", err));
        }, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/scan', methods=['POST'])
def receive_scan():
    global last_scanned_item
    
    if 'image' not in request.files:
        return jsonify({"error": "No image"}), 400
    
    file = request.files['image']
    filename = "latest_scan.jpg"
    file.save(filename)
    
    verdict = "Analyzing..."
    item_name = "Unknown"
    item_power = 0
    stats = {}
    
    if ocr_ready:
        try:
            print(f" Running OCR on {filename}...")
            # Run the OCR engine
            result = ocr_engine.infer(filename)
            
            item_name = result.get('item_name', 'Unknown')
            item_power = result.get('item_power', 0)
            stats = result.get('stats', {})
            
            print(f" OCR Result:")
            print(f" Item: {item_name}")
            print(f" Power: {item_power}")
            print(f" Stats: {stats}")
            
            # Simple verdict logic
            if item_power > 725:
                verdict = f" UPGRADE! Power: {item_power}"
            elif item_power > 700:
                verdict = f"MAYBE (Power: {item_power})"
            else:
                verdict = f" KEEP (Power: {item_power})"
                
        except Exception as e:
            verdict = f" OCR Error: {str(e)}"
            print(f" Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        verdict = "OCR Not Ready"
    
    last_scanned_item = {
        "item_name": item_name,
        "item_power": item_power,
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }

    with open(filename, "rb") as img_file:
        b64 = base64.b64encode(img_file.read()).decode()

    return jsonify({
        "image": b64,
        "verdict": verdict,
        "time": datetime.now().strftime("%H:%M:%S"),
        "data": last_scanned_item
    })

@app.route('/latest')
def latest():
    if last_scanned_item and os.path.exists("latest_scan.jpg"):
        with open("latest_scan.jpg", "rb") as img_file:
            b64 = base64.b64encode(img_file.read()).decode()
        return jsonify({
            "image": b64,
            "verdict": f"Power: {last_scanned_item['item_power']}",
            "time": datetime.now().strftime("%H:%M:%S"),
            "data": last_scanned_item
        })
    return jsonify({})

@app.route('/update', methods=['POST'])
def update_equipped():
    global last_scanned_item
    if not last_scanned_item:
        return jsonify({"error": "No item scanned yet!"}), 400
    
    slot = request.args.get('slot', 'Unknown')
    
    try:
        if not os.path.exists("character.json"):
            char_data = {"build_focus": [], "equipped": {}}
        else:
            with open("character.json", "r") as f:
                char_data = json.load(f)
        
        # Add the new item to the slot
        char_data["equipped"][slot] = last_scanned_item
        
        with open("character.json", "w") as f:
            json.dump(char_data, f, indent=2)
        
        print(f" Saved {slot} to character.json")
        return jsonify({"success": True, "message": f"Equipped {slot}!"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/init-scan', methods=['POST'])
def init_scan():
    global last_scanned_item
    if not last_scanned_item:
        return jsonify({"error": "No item scanned yet!"}), 400
    
    slot = request.args.get('slot', 'Unknown')
    
    try:
        if not os.path.exists("character.json"):
            char_data = {"build_focus": [], "equipped": {}}
        else:
            with open("character.json", "r") as f:
                char_data = json.load(f)
        
        char_data["equipped"][slot] = last_scanned_item
        
        with open("character.json", "w") as f:
            json.dump(char_data, f, indent=2)
            
        print(f"Initial setup: Saved {slot} as base gear.")
        return jsonify({"success": True, "message": f"Initialized {slot}!"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(" Server started!")
    print("Open http://YOUR_PC_IP:5000 on your phone")
    print("Waiting for images from Pi...")
    app.run(host='0.0.0.0', port=5000, debug=False)