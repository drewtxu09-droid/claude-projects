import subprocess
import os
import base64
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def img_b64(path):
    try:
        with open(path, 'rb') as f:
            return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()
    except:
        return ''

VISTRA_SRC = img_b64(os.path.join(BASE, 'Vistra.png'))

ICONS = {
    'chart': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>',
    'bolt':  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    'upload':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    'clock': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    'cal':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    'bell':  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    'eye':   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    'alarm': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2"/><path d="M5 3L2 6"/><path d="M22 6l-3-3"/></svg>',
    'timer': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="18.66" y1="5.34" x2="17.25" y2="6.75"/></svg>',
}

SCRIPTS = [
    {
        "id": "oncor_dashboard",
        "group": "Oncor Dashboard",
        "group_color": "#3b82f6",
        "name": "Rate Dashboard",
        "file": "run.bat",
        "dir": os.path.join(BASE, "oncor-dashboard"),
        "description": "Start Oncor TDU Rate Dashboard at localhost:8050",
        "icon": "chart",
    },
    {
        "id": "rtspp_v2",
        "group": "RTSPP Extract",
        "group_color": "#8b5cf6",
        "name": "Extract v2 (Auto)",
        "file": "run_rtspp_extract_v2.bat",
        "dir": os.path.join(BASE, "RTSPP"),
        "description": "Automated monthly SAP pull with Teams alert on failure",
        "icon": "bolt",
    },
    {
        "id": "rtspp_save",
        "group": "RTSPP Extract",
        "group_color": "#8b5cf6",
        "name": "Save Extract",
        "file": "save_rtspp_extract.bat",
        "dir": os.path.join(BASE, "RTSPP"),
        "description": "Save extracted RTSPP data to network share",
        "icon": "upload",
    },
    # ARCHIVED — hidden from dashboard, kept for reference
    # {
    #     "id": "rtspp_run",
    #     "group": "RTSPP Extract",
    #     "group_color": "#8b5cf6",
    #     "name": "Extract (Legacy)",
    #     "file": "run_rtspp_extract.bat",
    #     "dir": os.path.join(BASE, "RTSPP"),
    #     "description": "Original SAP extract — requires Excel + SAP GUI scripting",
    #     "icon": "clock",
    # },
    {
        "id": "rtspp_schedule",
        "group": "RTSPP Extract",
        "group_color": "#8b5cf6",
        "name": "Setup Schedule",
        "file": "setup_scheduled_task.bat",
        "dir": os.path.join(BASE, "RTSPP"),
        "description": "Auto-run extract on 2nd of month at 8 AM (requires admin)",
        "icon": "cal",
    },
    {
        "id": "che_alert",
        "group": "Price Comparison",
        "group_color": "#10b981",
        "name": "4CHE Scrape & Alert",
        "file": "run_4CHE_alert.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Scrape ComparePower prices and send price alerts",
        "icon": "bell",
    },
    {
        "id": "che_monitor",
        "group": "Price Comparison",
        "group_color": "#10b981",
        "name": "4CHE Monitor",
        "file": "run_4CHE_monitor.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Log ComparePower monitoring data to monitor_log.txt",
        "icon": "eye",
    },
    {
        "id": "che_schedule_alerts",
        "group": "Price Comparison",
        "group_color": "#10b981",
        "name": "Setup Alert Tasks",
        "file": "setup_scheduled_tasks.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Register daily alert tasks at 8 AM, 12 PM, and 5 PM",
        "icon": "alarm",
    },
    {
        "id": "che_schedule_monitor",
        "group": "Price Comparison",
        "group_color": "#10b981",
        "name": "Setup Monitor Task",
        "file": "setup_monitor_task.bat",
        "dir": os.path.join(BASE, "Price Comparison"),
        "description": "Register monitor task to run every 30 minutes",
        "icon": "timer",
    },
]

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Rate Management</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #0d1117;
  color: #e6edf3;
  min-height: 100vh;
}

/* ── HEADER ── */
header {
  background: #0d1117;
  border-bottom: 2px solid #2d8a4e;
  padding: 0 28px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}
.brand img {
  height: 34px;
  object-fit: contain;
}
.brand-divider {
  width: 1px;
  height: 28px;
  background: #30363d;
}
.brand-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #e6edf3;
  letter-spacing: 0.01em;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.customize-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #30363d;
  background: transparent;
  color: #8b949e;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.customize-btn:hover { border-color: #58a6ff; color: #58a6ff; }
.customize-btn.active { border-color: #f0a030; color: #f0a030; background: rgba(240,160,48,0.08); }
.customize-btn svg { width: 14px; height: 14px; }
.reset-btn {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #30363d;
  background: transparent;
  color: #8b949e;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  display: none;
}
.reset-btn:hover { border-color: #f87171; color: #f87171; }
.reset-btn.visible { display: block; }

/* ── LEGEND ── */
.legend {
  display: flex;
  gap: 20px;
  padding: 14px 28px 0;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #8b949e;
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* ── GRID ── */
.grid-area { padding: 18px 24px 40px; }
#grid {
  display: grid;
  grid-template-columns: repeat(var(--cols, 4), 172px);
  gap: 16px;
}
.col-picker {
  display: none;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #8b949e;
}
.col-picker.visible { display: flex; }
.col-btn {
  width: 28px; height: 28px;
  border-radius: 5px;
  border: 1px solid #30363d;
  background: transparent;
  color: #8b949e;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
}
.col-btn:hover { border-color: #f0a030; color: #f0a030; }
.col-btn.active { border-color: #f0a030; color: #f0a030; background: rgba(240,160,48,0.12); }

/* ── CARD ── */
.app-card {
  width: 172px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
  user-select: none;
}
.app-card:hover {
  border-color: #484f58;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.icon-area {
  width: 100%;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.icon-area svg {
  width: 40px;
  height: 40px;
  color: rgba(255,255,255,0.9);
}
.card-body {
  width: 100%;
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  flex: 1;
}
.card-name {
  font-weight: 600;
  font-size: 0.82rem;
  color: #e6edf3;
  text-align: center;
  line-height: 1.3;
}
.card-group {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 2px 7px;
  border-radius: 20px;
  background: rgba(255,255,255,0.07);
}
.card-desc {
  font-size: 0.71rem;
  color: #8b949e;
  text-align: center;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-top: 2px;
}
.card-file {
  font-size: 0.65rem;
  color: #484f58;
  font-family: monospace;
  margin-top: 2px;
}
.run-btn {
  margin-top: 8px;
  width: 100%;
  padding: 7px 0;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  color: #fff;
  transition: opacity 0.15s, transform 0.1s;
  letter-spacing: 0.03em;
}
.run-btn:hover { opacity: 0.85; }
.run-btn:active { transform: scale(0.97); }
.run-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.app-status {
  font-size: 0.7rem;
  min-height: 14px;
  text-align: center;
  margin-top: 3px;
  width: 100%;
}
.app-status.ok  { color: #3fb950; }
.app-status.err { color: #f85149; }
.app-status.running { color: #d29922; }

/* ── CUSTOMIZE MODE ── */
#grid.customizing .app-card {
  cursor: grab;
  border-style: dashed;
  border-color: #444c56;
}
#grid.customizing .app-card:active { cursor: grabbing; }
.app-card.dragging { opacity: 0.35; transform: scale(0.97); }
.app-card.drag-over {
  border-color: #f0a030 !important;
  border-style: solid !important;
  transform: scale(1.04);
  box-shadow: 0 0 0 2px rgba(240,160,48,0.3);
}
.drag-hint {
  display: none;
  font-size: 0.75rem;
  color: #d29922;
  padding: 6px 28px 0;
}
.drag-hint.visible { display: block; }
</style>
</head>
<body>

<header>
  <div class="brand">
    {% if vistra_src %}
    <img src="{{ vistra_src }}" alt="Vistra">
    <div class="brand-divider"></div>
    {% endif %}
    <span class="brand-title">Rate Management</span>
  </div>
  <div class="header-actions">
    <div class="col-picker" id="colPicker">
      <span>Columns:</span>
      <button class="col-btn" onclick="setCols(3)">3</button>
      <button class="col-btn" onclick="setCols(4)">4</button>
      <button class="col-btn" onclick="setCols(5)">5</button>
      <button class="col-btn" onclick="setCols(6)">6</button>
    </div>
    <button class="reset-btn" id="resetBtn" onclick="resetLayout()">Reset Layout</button>
    <button class="customize-btn" id="customizeBtn" onclick="toggleCustomize()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
      Customize Layout
    </button>
  </div>
</header>

<div class="legend">
  {% for g in groups %}
  <div class="legend-item">
    <div class="legend-dot" style="background:{{ g.color }}"></div>
    <span>{{ g.name }}</span>
  </div>
  {% endfor %}
</div>

<div class="drag-hint" id="dragHint">Drag cards to rearrange — click <strong>Done</strong> to save.</div>

<div class="grid-area">
  <div id="grid">
    {% for s in scripts %}
    <div class="app-card" data-id="{{ s.id }}">
      <div class="icon-area" style="background: linear-gradient(135deg, {{ s.group_color }}33 0%, {{ s.group_color }}1a 100%);">
        {{ icons[s.icon] | safe }}
      </div>
      <div class="card-body">
        <div class="card-name">{{ s.name }}</div>
        <div class="card-group" style="color:{{ s.group_color }}">{{ s.group }}</div>
        <div class="card-desc">{{ s.description }}</div>
        <div class="card-file">{{ s.file }}</div>
        <button class="run-btn" style="background:{{ s.group_color }}" onclick="runScript('{{ s.id }}', this)">▶ Run</button>
        <div class="app-status" id="status-{{ s.id }}"></div>
      </div>
    </div>
    {% endfor %}
  </div>
</div>

<script>
let dragId = null;

// ── Drag & Drop ──────────────────────────────────────────
const grid = document.getElementById('grid');

grid.addEventListener('dragstart', e => {
  const card = e.target.closest('.app-card');
  if (!card) return;
  dragId = card.dataset.id;
  card.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
});

grid.addEventListener('dragend', e => {
  const card = e.target.closest('.app-card');
  if (card) card.classList.remove('dragging');
  document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
  saveOrder();
});

grid.addEventListener('dragover', e => {
  e.preventDefault();
  const card = e.target.closest('.app-card');
  document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
  if (card && card.dataset.id !== dragId) card.classList.add('drag-over');
});

grid.addEventListener('drop', e => {
  e.preventDefault();
  const target = e.target.closest('.app-card');
  if (!target || target.dataset.id === dragId) return;
  const dragging = grid.querySelector('[data-id="' + dragId + '"]');
  const all = [...grid.querySelectorAll('.app-card')];
  const di = all.indexOf(dragging), ti = all.indexOf(target);
  if (di < ti) target.after(dragging); else target.before(dragging);
  saveOrder();
});

// ── Columns ──────────────────────────────────────────────
function setCols(n) {
  grid.style.setProperty('--cols', n);
  localStorage.setItem('launcher_cols', n);
  document.querySelectorAll('.col-btn').forEach(b => {
    b.classList.toggle('active', parseInt(b.textContent) === n);
  });
}

function loadCols() {
  const saved = parseInt(localStorage.getItem('launcher_cols') || '4');
  setCols(saved);
}

// ── Customize toggle ─────────────────────────────────────
function toggleCustomize() {
  const isOn = grid.classList.toggle('customizing');
  const btn = document.getElementById('customizeBtn');
  const resetBtn = document.getElementById('resetBtn');
  const hint = document.getElementById('dragHint');
  const colPicker = document.getElementById('colPicker');
  grid.querySelectorAll('.app-card').forEach(c => { c.draggable = isOn; });
  if (isOn) {
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><polyline points="20 6 9 17 4 12"/></svg> Done';
  } else {
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/></svg> Customize Layout';
  }
  btn.classList.toggle('active', isOn);
  resetBtn.classList.toggle('visible', isOn);
  hint.classList.toggle('visible', isOn);
  colPicker.classList.toggle('visible', isOn);
}

// ── Layout persistence ───────────────────────────────────
function saveOrder() {
  const order = [...grid.querySelectorAll('.app-card')].map(c => c.dataset.id);
  localStorage.setItem('launcher_order', JSON.stringify(order));
}

function loadOrder() {
  const saved = localStorage.getItem('launcher_order');
  if (!saved) return;
  try {
    JSON.parse(saved).forEach(id => {
      const card = grid.querySelector('[data-id="' + id + '"]');
      if (card) grid.appendChild(card);
    });
  } catch {}
}

function resetLayout() {
  localStorage.removeItem('launcher_order');
  location.reload();
}

// ── Run script ───────────────────────────────────────────
async function runScript(id, btn) {
  if (grid.classList.contains('customizing')) return;
  const status = document.getElementById('status-' + id);
  btn.disabled = true;
  status.className = 'app-status running';
  status.textContent = 'Launching...';
  try {
    const res = await fetch('/run/' + id, { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      status.className = 'app-status ok';
      status.textContent = 'Launched ✓';
    } else {
      status.className = 'app-status err';
      status.textContent = data.error;
    }
  } catch {
    status.className = 'app-status err';
    status.textContent = 'Request failed';
  }
  btn.disabled = false;
  setTimeout(() => { status.textContent = ''; status.className = 'app-status'; }, 4000);
}

loadOrder();
loadCols();
</script>
</body>
</html>"""

@app.route("/")
def index():
    groups_seen = {}
    for s in SCRIPTS:
        if s["group"] not in groups_seen:
            groups_seen[s["group"]] = s["group_color"]
    groups = [{"name": k, "color": v} for k, v in groups_seen.items()]
    return render_template_string(HTML,
        scripts=SCRIPTS,
        icons=ICONS,
        groups=groups,
        vistra_src=VISTRA_SRC,
    )

@app.route("/run/<script_id>", methods=["POST"])
def run_script(script_id):
    script = next((s for s in SCRIPTS if s["id"] == script_id), None)
    if not script:
        return jsonify({"ok": False, "error": "Unknown script"})
    bat = os.path.join(script["dir"], script["file"])
    if not os.path.exists(bat):
        return jsonify({"ok": False, "error": f"File not found: {bat}"})
    try:
        subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", bat], cwd=script["dir"], shell=False)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

if __name__ == "__main__":
    print("Launcher running at http://localhost:5151")
    app.run(port=5151, debug=False)
