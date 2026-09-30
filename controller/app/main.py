import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from controller.app.config import settings
from controller.app.database import engine, Base
from controller.app.api import health, nodes, vms, events
from controller.app.services.reconciliation import run_reconciliation_loop

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("controller")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PS-023 Cloud Controller Database schema...")
    Base.metadata.create_all(bind=engine)
    
    # Start background reconciliation loop
    reconciler_task = asyncio.create_task(run_reconciliation_loop())
    logger.info("Cloud Controller started successfully on %s:%s", settings.CONTROLLER_HOST, settings.CONTROLLER_PORT)
    
    yield
    
    reconciler_task.cancel()
    try:
        await reconciler_task
    except asyncio.CancelledError:
        logger.info("Reconciler background task stopped.")

app = FastAPI(
    title="PS-023 Cloud Hypervisor Controller",
    description="Minimal Two-Node Cloud Hypervisor VM Controller",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(nodes.router)
app.include_router(vms.router)
app.include_router(events.router)

# Embedded Web Dashboard UI
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PS-023 — Cloud Hypervisor Controller</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --success: #3fb950;
      --warning: #d29922;
      --danger: #f85149;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      padding: 24px;
      line-height: 1.5;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
    }
    .brand h1 { font-size: 1.4rem; color: #fff; display: flex; align-items: center; gap: 10px; }
    .badge {
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .badge-online { background: rgba(63, 185, 80, 0.15); color: var(--success); border: 1px solid var(--success); }
    .badge-offline { background: rgba(248, 81, 73, 0.15); color: var(--danger); border: 1px solid var(--danger); }
    .badge-running { background: rgba(63, 185, 80, 0.15); color: var(--success); }
    .badge-stopped { background: rgba(210, 153, 34, 0.15); color: var(--warning); }
    .badge-error { background: rgba(248, 81, 73, 0.15); color: var(--danger); }

    .grid-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }
    .stat-card .label { font-size: 0.8rem; color: var(--text-muted); }
    .stat-card .value { font-size: 1.6rem; font-weight: 700; color: #fff; margin-top: 4px; }

    .section-title { font-size: 1.1rem; color: #fff; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    
    .node-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 20px;
      margin-bottom: 28px;
    }
    .node-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
    }
    .node-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .node-name { font-weight: 700; font-size: 1.1rem; color: #fff; }
    .meter { height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; margin: 6px 0 12px; }
    .meter-fill { height: 100%; background: var(--accent); transition: width 0.3s; }

    table { width: 100%; border-collapse: collapse; margin-bottom: 28px; background: var(--card-bg); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
    th, td { padding: 12px 16px; text-align: left; font-size: 0.9rem; border-bottom: 1px solid var(--border); }
    th { background: #21262d; color: var(--text-muted); font-weight: 600; }
    tr:last-child td { border-bottom: none; }
    
    .btn {
      background: #238636;
      color: #fff;
      border: none;
      padding: 8px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.9; }
    .btn-sm { padding: 4px 8px; font-size: 0.75rem; margin-right: 4px; }
    .btn-danger { background: #da3633; }
    .btn-warning { background: #d29922; }
    .btn-secondary { background: #30363d; color: var(--text); }

    .events-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      max-height: 240px;
      overflow-y: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
    }
    .event-line { padding: 4px 0; border-bottom: 1px solid #21262d; display: flex; gap: 12px; }
    .event-time { color: var(--text-muted); }
    .event-type { color: var(--accent); font-weight: 600; }

    /* Modal */
    .modal {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.7);
      align-items: center;
      justify-content: center;
    }
    .modal.active { display: flex; }
    .modal-content {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 24px;
      width: 440px;
      max-width: 90vw;
    }
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px; }
    .form-group input, .form-group select {
      width: 100%;
      background: #0d1117;
      border: 1px solid var(--border);
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-family: inherit;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1>PS-023 Cloud Hypervisor Controller</h1>
      <span style="font-size: 0.85rem; color: var(--text-muted);">Minimal Two-Node Hypervisor Dashboard</span>
    </div>
    <div>
      <span class="badge badge-online" id="cluster-mode">KVM / Mock Auto</span>
      <button class="btn" onclick="openCreateModal()">+ Create VM</button>
    </div>
  </header>

  <div class="grid-stats">
    <div class="stat-card">
      <div class="label">Total Nodes</div>
      <div class="value" id="stat-nodes">0</div>
    </div>
    <div class="stat-card">
      <div class="label">Online Nodes</div>
      <div class="value" id="stat-online-nodes">0</div>
    </div>
    <div class="stat-card">
      <div class="label">Total VMs</div>
      <div class="value" id="stat-vms">0</div>
    </div>
    <div class="stat-card">
      <div class="label">Running VMs</div>
      <div class="value" id="stat-running-vms">0</div>
    </div>
    <div class="stat-card">
      <div class="label">Allocated RAM</div>
      <div class="value" id="stat-ram">0 MB</div>
    </div>
  </div>

  <div class="section-title">Compute Nodes</div>
  <div class="node-grid" id="node-container"></div>

  <div class="section-title">Virtual Machines</div>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Node</th>
        <th>Desired State</th>
        <th>Actual State</th>
        <th>vCPU / RAM</th>
        <th>IP Address</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="vm-table-body">
      <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading virtual machines...</td></tr>
    </tbody>
  </table>

  <div class="section-title">Cluster Audit Log</div>
  <div class="events-box" id="events-log"></div>

  <!-- Create VM Modal -->
  <div class="modal" id="create-modal">
    <div class="modal-content">
      <h3 style="margin-bottom: 16px; color: #fff;">Create Virtual Machine</h3>
      <div class="form-group">
        <label>VM Name</label>
        <input type="text" id="vm-name" value="ubuntu-demo" required>
      </div>
      <div class="form-group">
        <label>vCPUs</label>
        <select id="vm-cpu">
          <option value="1">1 Core</option>
          <option value="2" selected>2 Cores</option>
          <option value="4">4 Cores</option>
        </select>
      </div>
      <div class="form-group">
        <label>Memory (RAM)</label>
        <select id="vm-mem">
          <option value="1024">1024 MB</option>
          <option value="2048" selected>2048 MB</option>
          <option value="4096">4096 MB</option>
        </select>
      </div>
      <div class="form-group">
        <label>Disk Size</label>
        <select id="vm-disk">
          <option value="10" selected>10 GB</option>
          <option value="20">20 GB</option>
        </select>
      </div>
      <div class="form-group">
        <label>Cloud Image</label>
        <select id="vm-image">
          <option value="ubuntu-24.04" selected>ubuntu-24.04 (qcow2)</option>
          <option value="debian-12">debian-12 (qcow2)</option>
          <option value="alpine-3.19">alpine-3.19 (minimal)</option>
        </select>
      </div>
      <div class="form-group">
        <label>Placement Policy</label>
        <select id="vm-node">
          <option value="">Auto (Resource-Aware Scheduler)</option>
          <option value="node-a">Force Node A</option>
          <option value="node-b">Force Node B</option>
        </select>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px;">
        <button class="btn btn-secondary" onclick="closeCreateModal()">Cancel</button>
        <button class="btn" onclick="submitCreateVM()">Provision VM</button>
      </div>
    </div>
  </div>

  <script>
    async function fetchData() {
      try {
        const [nodesRes, vmsRes, metricsRes, eventsRes] = await Promise.all([
          fetch('/nodes'),
          fetch('/vms'),
          fetch('/metrics'),
          fetch('/events?limit=20')
        ]);
        const nodes = await nodesRes.json();
        const vms = await vmsRes.json();
        const metrics = await metricsRes.json();
        const events = await eventsRes.json();

        renderMetrics(metrics);
        renderNodes(nodes);
        renderVMs(vms);
        renderEvents(events);
      } catch (err) {
        console.error('Fetch error:', err);
      }
    }

    function renderMetrics(m) {
      document.getElementById('stat-nodes').innerText = m.total_nodes;
      document.getElementById('stat-online-nodes').innerText = m.online_nodes;
      document.getElementById('stat-vms').innerText = m.total_vms;
      document.getElementById('stat-running-vms').innerText = m.running_vms;
      document.getElementById('stat-ram').innerText = m.allocated_memory_mb + ' MB';
    }

    function renderNodes(nodes) {
      const container = document.getElementById('node-container');
      if (!nodes.length) {
        container.innerHTML = '<div style="color: var(--text-muted)">No compute nodes registered yet. Start Node Agents to register.</div>';
        return;
      }
      container.innerHTML = nodes.map(n => `
        <div class="node-card">
          <div class="node-header">
            <div>
              <div class="node-name">${n.node_id} (${n.hostname})</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">${n.address}:${n.port} • ${n.is_mock ? 'MOCK ENGINE' : 'REAL KVM'}</div>
            </div>
            <span class="badge badge-${n.status.toLowerCase()}">${n.status}</span>
          </div>
          <div>CPU Usage: ${n.cpu_used_percent.toFixed(1)}%</div>
          <div class="meter"><div class="meter-fill" style="width: ${n.cpu_used_percent}%"></div></div>
          <div>RAM Usage: ${n.memory_used_mb} / ${n.memory_total} MB</div>
          <div class="meter"><div class="meter-fill" style="width: ${(n.memory_used_mb / Math.max(n.memory_total, 1)) * 100}%"></div></div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px;">
            <span style="font-size: 0.85rem; color: var(--text-muted);">Active VMs: <b>${n.vm_count || 0}</b></span>
            ${n.status === 'ONLINE' ? `<button class="btn btn-sm btn-warning" onclick="simulateFailure('${n.node_id}')">Simulate Fail</button>` : ''}
          </div>
        </div>
      `).join('');
    }

    function renderVMs(vms) {
      const tbody = document.getElementById('vm-table-body');
      if (!vms.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 20px;">No virtual machines provisioned. Click "+ Create VM" above.</td></tr>';
        return;
      }
      tbody.innerHTML = vms.map(v => `
        <tr>
          <td style="font-weight: 600; color: #fff;">${v.name}</td>
          <td><span style="font-family: monospace;">${v.node_id}</span></td>
          <td><span class="badge badge-${v.desired_state.toLowerCase()}">${v.desired_state}</span></td>
          <td><span class="badge badge-${v.actual_state.toLowerCase()}">${v.actual_state}</span></td>
          <td>${v.cpu} vCPU / ${v.memory_mb} MB</td>
          <td>${v.ip_address || '<span style="color:var(--text-muted)">dhcp waiting...</span>'}</td>
          <td>
            ${v.actual_state === 'STOPPED' ? `<button class="btn btn-sm" onclick="vmAction(${v.id}, 'start')">Start</button>` : ''}
            ${v.actual_state === 'RUNNING' ? `<button class="btn btn-sm btn-warning" onclick="vmAction(${v.id}, 'stop')">Stop</button>` : ''}
            <button class="btn btn-sm btn-secondary" onclick="vmAction(${v.id}, 'restart')">Restart</button>
            <button class="btn btn-sm btn-danger" onclick="deleteVM(${v.id})">Delete</button>
          </td>
        </tr>
      `).join('');
    }

    function renderEvents(events) {
      const log = document.getElementById('events-log');
      if (!events.length) {
        log.innerHTML = '<div style="color: var(--text-muted)">No cluster events recorded yet.</div>';
        return;
      }
      log.innerHTML = events.map(e => `
        <div class="event-line">
          <span class="event-time">${new Date(e.timestamp).toLocaleTimeString()}</span>
          <span class="event-type">${e.event_type}</span>
          <span>[${e.node_id || 'controller'}] ${e.message}</span>
        </div>
      `).join('');
    }

    async function vmAction(id, action) {
      try {
        const res = await fetch(`/vms/${id}/${action}`, { method: 'POST' });
        if (!res.ok) alert('Error: ' + (await res.json()).detail);
        fetchData();
      } catch (err) { alert('Action failed: ' + err); }
    }

    async function deleteVM(id) {
      if (!confirm('Are you sure you want to permanently delete this VM?')) return;
      try {
        const res = await fetch(`/vms/${id}`, { method: 'DELETE' });
        if (!res.ok) alert('Error: ' + (await res.json()).detail);
        fetchData();
      } catch (err) { alert('Delete failed: ' + err); }
    }

    async function simulateFailure(nodeId) {
      try {
        await fetch(`/nodes/${nodeId}/simulate-failure`, { method: 'POST' });
        fetchData();
      } catch (err) { alert('Simulate failed: ' + err); }
    }

    function openCreateModal() { document.getElementById('create-modal').classList.add('active'); }
    function closeCreateModal() { document.getElementById('create-modal').classList.remove('active'); }

    async function submitCreateVM() {
      const payload = {
        name: document.getElementById('vm-name').value.trim(),
        cpu: parseInt(document.getElementById('vm-cpu').value),
        memory_mb: parseInt(document.getElementById('vm-mem').value),
        disk_gb: parseInt(document.getElementById('vm-disk').value),
        image: document.getElementById('vm-image').value,
        preferred_node: document.getElementById('vm-node').value || null
      };

      try {
        const res = await fetch('/vms', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const err = await res.json();
          alert('Provisioning failed: ' + (err.detail || JSON.stringify(err)));
        } else {
          closeCreateModal();
          fetchData();
        }
      } catch (err) {
        alert('Request failed: ' + err);
      }
    }

    // Polling loop
    fetchData();
    setInterval(fetchData, 3000);
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)
