import subprocess
import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPTS = [
    {
        "id": "oncor_dashboard",
        "group": "Oncor TDU Rate Dashboard",
        "name": "Run Dashboard",
        "file": "run.bat",
        "dir": os.path.join(BASE, "oncor-dashboard"),
        "description": "Installs dependencies and starts the Oncor TDU Rate Dashboard. Opens at http://localhost:8050 in your browser.",
        "color": "#2563eb",
    },
    {
        "id": "rtspp_v2",
        "group": "RTSPP Extract",
        "name": "Run RTSPP Extract v2",
        "file": "run_rtspp_extract_v2.bat",
        "dir": os.path.join(BASE, "RTSPP"),
        "description": "Automated monthly RTSPP data pull from SAP. Sends Teams alert on failure. Review results before saving.",
        "color": "#7c3aed",
    },
    {
        "id": "rtspp_save",
        "group": "RTSPP Extract",
        "name": "Save RTSPP Extract",
        "file": "save_rtspp_extract.bat",
        "dir": os.path.join(BASE, "RTSPP"),
        "description": "Saves extracted RTSPP data to the network share. Requires Excel open with filename in ReadMe!E2 and year in ReadMe!B3.",
        "color": "#7c3aed",
    },
    {
        "id": "rtspp_run",
        "group": "RTSPP Extract",
        "name": "Run RTSPP Extract (Legacy)",
        "file": "run_rtspp_extract.bat",
        "dir": os.path.join(BASE, "RTSPP"),
        "description": "Original RTSPP extract from SAP. Requires Excel with RTSPP_Extract_Tool_DW.xlsm open and SAP GUI scripting enabled.",
        "color": "#7c3aed",
    },
    {
        "id": "rtspp_schedule",
        "group": "RTSPP Extract",
        "name": "Setup Scheduled Task",
        "file": "setup_scheduled_task.bat",
        "dir": os.path.join(BASE, "RTSPP"),
        "description": "Registers a Windows Scheduled Task to auto-run RTSPP extract on the 2nd of every month at 8:00 AM. Requires admin.",
        "color": "#7c3aed",
    },
    {
        "id": "che_alert",
        "group": "Price Comparison — 4CHE",
        "name": "Run 4CHE Scrape & Alert",
        "file": "run_4CHE_alert.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Runs ComparePower_4CHE_Scrape.py to scrape prices and send alerts. Output appended to scrape_log.txt.",
        "color": "#059669",
    },
    {
        "id": "che_monitor",
        "group": "Price Comparison — 4CHE",
        "name": "Run 4CHE Monitor",
        "file": "run_4CHE_monitor.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Runs ComparePower_4CHE_Monitor.py and logs monitoring activity to monitor_log.txt.",
        "color": "#059669",
    },
    {
        "id": "che_schedule_alerts",
        "group": "Price Comparison — 4CHE",
        "name": "Setup Alert Scheduled Tasks",
        "file": "setup_scheduled_tasks.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Registers 3 Windows Scheduled Tasks to run the 4CHE scrape alert daily at 8:00 AM, 12:00 PM, and 5:00 PM.",
        "color": "#059669",
    },
    {
        "id": "che_schedule_monitor",
        "group": "Price Comparison — 4CHE",
        "name": "Setup Monitor Scheduled Task",
        "file": "setup_monitor_task.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Registers a Windows Scheduled Task to run the 4CHE Monitor every 30 minutes.",
        "color": "#059669",
    },
]

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Script Launcher</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 2rem; }
  h1 { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; color: #f8fafc; }
  .subtitle { color: #94a3b8; margin-bottom: 2.5rem; font-size: 0.95rem; }
  .group { margin-bottom: 2rem; }
  .group-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid #1e293b; }
  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
  .card { background: #1e293b; border-radius: 0.75rem; padding: 1.25rem 1.5rem; border: 1px solid #334155; display: flex; flex-direction: column; gap: 0.75rem; }
  .card-header { display: flex; align-items: center; gap: 0.6rem; }
  .dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .card-name { font-weight: 600; font-size: 1rem; color: #f1f5f9; }
  .card-desc { font-size: 0.85rem; color: #94a3b8; line-height: 1.5; flex: 1; }
  .card-file { font-size: 0.75rem; color: #475569; font-family: monospace; }
  .btn { margin-top: 0.25rem; padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600; cursor: pointer; transition: opacity 0.15s, transform 0.1s; color: #fff; }
  .btn:hover { opacity: 0.85; }
  .btn:active { transform: scale(0.97); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .status { font-size: 0.78rem; min-height: 1.1rem; margin-top: 0.1rem; }
  .status.ok { color: #34d399; }
  .status.err { color: #f87171; }
  .status.running { color: #fbbf24; }
</style>
</head>
<body>
<h1>Script Launcher</h1>
<p class="subtitle">Click a button to run a script. Scripts open in a new terminal window.</p>

{% for group_name, cards in groups.items() %}
<div class="group">
  <div class="group-title">{{ group_name }}</div>
  <div class="cards">
    {% for s in cards %}
    <div class="card">
      <div class="card-header">
        <div class="dot" style="background:{{ s.color }}"></div>
        <span class="card-name">{{ s.name }}</span>
      </div>
      <div class="card-desc">{{ s.description }}</div>
      <div class="card-file">{{ s.file }}</div>
      <button class="btn" style="background:{{ s.color }}" onclick="runScript('{{ s.id }}', this)">Run</button>
      <div class="status" id="status-{{ s.id }}"></div>
    </div>
    {% endfor %}
  </div>
</div>
{% endfor %}

<script>
async function runScript(id, btn) {
  const status = document.getElementById('status-' + id);
  btn.disabled = true;
  status.className = 'status running';
  status.textContent = 'Launching...';
  try {
    const res = await fetch('/run/' + id, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      status.className = 'status ok';
      status.textContent = 'Launched successfully.';
    } else {
      status.className = 'status err';
      status.textContent = 'Error: ' + data.error;
    }
  } catch (e) {
    status.className = 'status err';
    status.textContent = 'Request failed.';
  }
  btn.disabled = false;
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    groups = {}
    for s in SCRIPTS:
        groups.setdefault(s["group"], []).append(s)
    return render_template_string(HTML, groups=groups)

@app.route("/run/<script_id>", methods=["POST"])
def run_script(script_id):
    script = next((s for s in SCRIPTS if s["id"] == script_id), None)
    if not script:
        return jsonify({"ok": False, "error": "Unknown script"})
    bat = os.path.join(script["dir"], script["file"])
    if not os.path.exists(bat):
        return jsonify({"ok": False, "error": f"File not found: {bat}"})
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/k", bat],
            cwd=script["dir"],
            shell=False,
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

if __name__ == "__main__":
    print("Launcher running at http://localhost:5050")
    app.run(port=5050, debug=False)
