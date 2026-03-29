"""
Dashboard templates for SaaS podcast generator.
"""
import os
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindStream Studio</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@500;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg:        #06060d;
            --surface:   #0b0b18;
            --card:      #0f0f1e;
            --elevated:  #15152a;
            --input-bg:  #0c0c1c;
            --a1: #6366f1;
            --a2: #8b5cf6;
            --a3: #d946ef;
            --grad: linear-gradient(135deg, #6366f1 0%, #8b5cf6 55%, #d946ef 100%);
            --t1: #eeeeff;
            --t2: #7878a8;
            --t3: #3d3d62;
            --border: rgba(99,102,241,.13);
            --border-s: rgba(255,255,255,.05);
            --ok: #22c55e;
            --warn: #f59e0b;
            --err: #ef4444;
            --sw: 244px;
            --radius: 10px;
        }

        html, body { height: 100%; }
        body {
            font-family: 'DM Sans', system-ui, sans-serif;
            background: var(--bg);
            color: var(--t1);
            min-height: 100vh;
            font-size: 14px;
            line-height: 1.55;
            -webkit-font-smoothing: antialiased;
        }

        /* ── Layout ───────────────────────────────────────── */
        .app { display: flex; min-height: 100vh; }

        /* ── Sidebar ──────────────────────────────────────── */
        .sidebar {
            width: var(--sw);
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            position: fixed;
            top: 0; left: 0; bottom: 0;
            z-index: 30;
        }
        .sidebar::after {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: var(--grad);
            opacity: .7;
        }

        .sb-logo {
            padding: 22px 18px 18px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid var(--border-s);
        }
        .sb-logo-mark {
            width: 36px; height: 36px;
            background: var(--grad);
            border-radius: 9px;
            display: flex; align-items: center; justify-content: center;
            font-size: 17px; flex-shrink: 0;
            box-shadow: 0 4px 14px rgba(99,102,241,.35);
        }
        .sb-logo-name {
            font-family: 'Syne', sans-serif;
            font-weight: 700; font-size: 15.5px;
            letter-spacing: -.025em;
            line-height: 1.1;
        }
        .sb-logo-tag {
            font-size: 10px; color: var(--t3);
            letter-spacing: .08em; text-transform: uppercase; margin-top: 2px;
        }

        nav {
            flex: 1; padding: 10px 10px;
            display: flex; flex-direction: column; gap: 1px;
            overflow-y: auto;
        }
        .nav-group {
            font-size: 10px; font-weight: 700;
            letter-spacing: .09em; text-transform: uppercase;
            color: var(--t3);
            padding: 10px 10px 4px;
        }
        nav a {
            display: flex; align-items: center; gap: 9px;
            padding: 8px 12px;
            border-radius: 8px;
            text-decoration: none;
            color: var(--t2);
            font-size: 13.5px; font-weight: 500;
            transition: background .12s, color .12s;
            cursor: pointer;
        }
        nav a:hover { background: rgba(99,102,241,.07); color: var(--t1); }
        nav a.active {
            background: rgba(99,102,241,.13);
            color: var(--t1);
            box-shadow: inset 3px 0 0 var(--a1);
        }
        nav a .ni { font-size: 14px; width: 16px; text-align: center; pointer-events: none; flex-shrink: 0; }
        nav a .nl { pointer-events: none; }

        .sb-foot {
            padding: 12px;
            border-top: 1px solid var(--border-s);
        }
        .user-chip {
            display: flex; align-items: center; gap: 9px;
            padding: 9px 10px;
            border-radius: 9px;
            background: rgba(255,255,255,.03);
            border: 1px solid var(--border-s);
        }
        .user-avi {
            width: 30px; height: 30px; border-radius: 7px;
            background: var(--grad);
            display: flex; align-items: center; justify-content: center;
            font-family: 'Syne', sans-serif;
            font-weight: 800; font-size: 12px; color: #fff;
            flex-shrink: 0;
        }
        .user-meta { flex: 1; min-width: 0; }
        #user-email {
            font-size: 11.5px; color: var(--t1); font-weight: 500;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        .badge {
            display: inline-flex; align-items: center;
            padding: 1px 6px; border-radius: 20px;
            font-size: 9.5px; font-weight: 800;
            letter-spacing: .05em; text-transform: uppercase;
        }
        .badge-free       { background: rgba(99,102,241,.18); color: #a5b4fc; }
        .badge-pro        { background: rgba(245,158,11,.18); color: #fcd34d; }
        .badge-enterprise { background: rgba(217,70,239,.18); color: #f0abfc; }

        .btn-logout {
            background: none; border: none; color: var(--t3); cursor: pointer;
            padding: 4px; border-radius: 5px; font-size: 15px; line-height: 1;
            transition: color .15s; flex-shrink: 0;
        }
        .btn-logout:hover { color: var(--err); }

        /* ── Main ─────────────────────────────────────────── */
        .main { flex: 1; margin-left: var(--sw); }

        section { display: none; min-height: 100vh; }
        #section-dashboard { display: block; }

        .pg-topbar {
            padding: 15px 28px;
            display: flex; align-items: center; justify-content: space-between;
            border-bottom: 1px solid var(--border-s);
            background: rgba(6,6,13,.85);
            backdrop-filter: blur(10px);
            position: sticky; top: 0; z-index: 10;
        }
        .pg-title {
            font-family: 'Syne', sans-serif;
            font-size: 17px; font-weight: 700;
            letter-spacing: -.025em;
        }
        .content { padding: 24px 28px; }

        /* ── Cards ────────────────────────────────────────── */
        .grid { display: grid; gap: 16px; margin-bottom: 20px; }
        .g3 { grid-template-columns: repeat(3, 1fr); }
        .g2 { grid-template-columns: repeat(2, 1fr); }
        .g-auto { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
        .g-wide { grid-template-columns: 2fr 1fr; }

        .card {
            background: var(--card);
            border: 1px solid var(--border-s);
            border-radius: 12px;
            padding: 20px;
            transition: border-color .2s;
        }
        .card:hover { border-color: var(--border); }
        .card-accent { border-color: rgba(99,102,241,.28); box-shadow: 0 0 28px rgba(99,102,241,.05); }

        .ch { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
        .ct {
            font-family: 'Syne', sans-serif;
            font-size: 13.5px; font-weight: 700;
            letter-spacing: -.01em;
        }

        /* Metric cards */
        .metric {
            background: var(--card);
            border: 1px solid var(--border-s);
            border-radius: 12px;
            padding: 18px 20px;
        }
        .m-label { font-size: 11.5px; color: var(--t2); font-weight: 500; margin-bottom: 6px; }
        .m-value {
            font-family: 'Syne', sans-serif;
            font-size: 26px; font-weight: 700;
            line-height: 1; color: var(--t1);
        }
        .m-bar { margin-top: 12px; }

        /* ── Progress ─────────────────────────────────────── */
        .progress {
            height: 4px; background: rgba(255,255,255,.05);
            border-radius: 99px; overflow: hidden;
        }
        .progress-bar {
            height: 100%; border-radius: 99px;
            background: var(--grad);
            transition: width .5s cubic-bezier(.4,0,.2,1);
        }
        .progress-bar.green { background: var(--ok); }
        .progress-bar.yellow { background: var(--warn); }
        .progress-bar.red { background: var(--err); }

        /* ── Stats ────────────────────────────────────────── */
        .stat {
            display: flex; justify-content: space-between; align-items: center;
            padding: 9px 0;
            border-bottom: 1px solid var(--border-s);
        }
        .stat:last-child { border-bottom: none; }
        .stat-label { color: var(--t2); font-size: 13px; }
        .stat-value { font-weight: 600; font-size: 13px; }
        .stat-value.success { color: var(--ok); }
        .stat-value.warning { color: var(--warn); }
        .stat-value.danger  { color: var(--err); }

        /* ── Buttons ──────────────────────────────────────── */
        .btn {
            display: inline-flex; align-items: center; gap: 5px;
            padding: 8px 15px;
            border-radius: 8px; border: none;
            cursor: pointer;
            font-size: 13px; font-weight: 600;
            font-family: 'DM Sans', sans-serif;
            transition: all .15s; white-space: nowrap;
            text-decoration: none;
        }
        .btn-primary {
            background: var(--grad); color: #fff;
            box-shadow: 0 2px 12px rgba(99,102,241,.28);
        }
        .btn-primary:hover { opacity: .88; transform: translateY(-1px); box-shadow: 0 4px 18px rgba(99,102,241,.4); }
        .btn-secondary {
            background: rgba(255,255,255,.05); color: var(--t1);
            border: 1px solid var(--border-s);
        }
        .btn-secondary:hover { background: rgba(255,255,255,.09); border-color: rgba(255,255,255,.1); }
        .btn-danger { background: rgba(239,68,68,.12); color: #f87171; border: 1px solid rgba(239,68,68,.2); }
        .btn-danger:hover { background: rgba(239,68,68,.2); }
        .btn:disabled { opacity: .38; cursor: not-allowed; transform: none !important; }

        /* Action tiles */
        .action-tile {
            display: flex; align-items: center; gap: 10px;
            padding: 11px 14px; border-radius: 9px;
            background: rgba(255,255,255,.03);
            border: 1px solid var(--border-s);
            color: var(--t1); cursor: pointer;
            font-size: 13.5px; font-weight: 500;
            font-family: 'DM Sans', sans-serif;
            transition: all .15s; width: 100%; text-align: left;
        }
        .action-tile:hover { background: rgba(99,102,241,.09); border-color: rgba(99,102,241,.25); }
        .action-tile .ai { font-size: 17px; flex-shrink: 0; }

        /* ── Forms ────────────────────────────────────────── */
        .form-group { margin-bottom: 15px; }
        .form-label { display: block; margin-bottom: 5px; font-size: 12.5px; font-weight: 600; color: var(--t2); }
        .form-input, .form-select, .form-textarea {
            width: 100%; padding: 9px 11px;
            border: 1px solid var(--border-s); border-radius: 8px;
            background: var(--input-bg); color: var(--t1);
            font-size: 13.5px; font-family: 'DM Sans', sans-serif;
            transition: border-color .15s;
        }
        .form-input::placeholder, .form-textarea::placeholder { color: var(--t3); }
        .form-input:focus, .form-select:focus, .form-textarea:focus {
            outline: none;
            border-color: rgba(99,102,241,.5);
            box-shadow: 0 0 0 3px rgba(99,102,241,.09);
        }
        .form-textarea { min-height: 88px; resize: vertical; }
        .form-hint { font-size: 11.5px; color: var(--t3); margin-top: 4px; }

        /* ── Tables ───────────────────────────────────────── */
        .table { width: 100%; border-collapse: collapse; }
        .table th {
            padding: 9px 14px;
            text-align: left; font-size: 10.5px; font-weight: 700;
            letter-spacing: .07em; text-transform: uppercase;
            color: var(--t3); border-bottom: 1px solid var(--border-s);
        }
        .table td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border-s);
            font-size: 13.5px;
        }
        .table tbody tr:hover td { background: rgba(99,102,241,.03); }
        .table tbody tr:last-child td { border-bottom: none; }

        /* ── Status badges ────────────────────────────────── */
        .status {
            display: inline-flex; align-items: center; gap: 5px;
            padding: 3px 9px; border-radius: 20px;
            font-size: 11px; font-weight: 600;
        }
        .status::before {
            content: ''; width: 5px; height: 5px;
            border-radius: 50%; background: currentColor; opacity: .7;
        }
        .status-draft      { background: rgba(255,255,255,.06); color: var(--t2); }
        .status-generating { background: rgba(99,102,241,.15); color: #a5b4fc; }
        .status-ready      { background: rgba(34,197,94,.12); color: #86efac; }
        .status-published  { background: rgba(139,92,246,.15); color: #c4b5fd; }
        .status-failed     { background: rgba(239,68,68,.12); color: #fca5a5; }

        /* ── Modal ────────────────────────────────────────── */
        .modal {
            display: none; position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(2,2,10,.8);
            backdrop-filter: blur(5px);
            z-index: 1000;
        }
        .modal.open { display: flex; align-items: center; justify-content: center; }
        .modal-content {
            background: var(--elevated);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 26px;
            max-width: 540px; width: 90%;
            max-height: 90vh; overflow-y: auto;
            box-shadow: 0 24px 80px rgba(0,0,0,.65), 0 0 0 1px rgba(99,102,241,.09);
            animation: min .2s ease;
        }
        @keyframes min {
            from { opacity: 0; transform: translateY(10px) scale(.98); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        .modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
        .modal-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 700; letter-spacing: -.02em; }
        .modal-close {
            background: rgba(255,255,255,.05); border: 1px solid var(--border-s);
            color: var(--t2); font-size: 17px; cursor: pointer;
            width: 28px; height: 28px; border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            transition: all .15s;
        }
        .modal-close:hover { background: rgba(239,68,68,.12); color: #f87171; border-color: rgba(239,68,68,.2); }

        /* ── Toast ────────────────────────────────────────── */
        .toast {
            position: fixed; bottom: 22px; right: 22px;
            padding: 11px 16px;
            border-radius: 10px; color: #fff;
            font-weight: 500; font-size: 13px;
            transform: translateY(120%); opacity: 0;
            transition: all .28s cubic-bezier(.4,0,.2,1);
            z-index: 2000;
            border: 1px solid rgba(255,255,255,.1);
            backdrop-filter: blur(8px);
            max-width: 300px;
            box-shadow: 0 8px 28px rgba(0,0,0,.45);
        }
        .toast.show { transform: translateY(0); opacity: 1; }
        .toast.success { background: rgba(22,163,74,.92); }
        .toast.error   { background: rgba(220,38,38,.92); }
        .toast.info    { background: rgba(79,70,229,.92); }

        /* ── Tabs ─────────────────────────────────────────── */
        .tabs { display: flex; border-bottom: 1px solid var(--border-s); margin-bottom: 18px; }
        .tab {
            padding: 8px 18px; cursor: pointer;
            border-bottom: 2px solid transparent; margin-bottom: -1px;
            color: var(--t2); font-size: 13.5px; font-weight: 500;
            transition: all .15s;
        }
        .tab:hover { color: var(--t1); }
        .tab.active { border-bottom-color: var(--a1); color: var(--t1); }

        /* ── Loading ──────────────────────────────────────── */
        .loading {
            display: inline-block; width: 17px; height: 17px;
            border: 2px solid var(--border-s); border-top-color: var(--a1);
            border-radius: 50%; animation: spin .75s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Empty state ──────────────────────────────────── */
        .empty { text-align: center; padding: 44px 20px; color: var(--t3); }
        .empty-icon { font-size: 36px; margin-bottom: 10px; opacity: .55; }
        .empty p { font-size: 13px; }

        code {
            font-family: 'Fira Code', 'Courier New', monospace;
            font-size: 12px; background: rgba(99,102,241,.1);
            padding: 2px 6px; border-radius: 4px; color: #a5b4fc;
        }
    </style>
</head>
<body>
<div class="app">

    <!-- ── Sidebar ─────────────────────────────────── -->
    <aside class="sidebar">
        <div class="sb-logo">
            <div class="sb-logo-mark">🎙</div>
            <div>
                <div class="sb-logo-name">MindStream</div>
                <div class="sb-logo-tag">Studio</div>
            </div>
        </div>

        <nav>
            <a href="#dashboard" class="active" onclick="showSection('dashboard')">
                <span class="ni">◈</span><span class="nl">Overview</span>
            </a>
            <a href="#podcasts" onclick="showSection('podcasts')">
                <span class="ni">🎙</span><span class="nl">Podcasts</span>
            </a>

            <div class="nav-group">Create</div>
            <a href="#scriptflow" onclick="showSection('scriptflow')">
                <span class="ni">✍</span><span class="nl">ScriptFlow</span>
            </a>

            <div class="nav-group">Account</div>
            <a href="#settings" onclick="showSection('settings')">
                <span class="ni">⚙</span><span class="nl">Settings</span>
            </a>
            <a href="#billing" onclick="showSection('billing')">
                <span class="ni">◇</span><span class="nl">Billing</span>
            </a>
        </nav>

        <div class="sb-foot">
            <div class="user-chip">
                <div class="user-avi">U</div>
                <div class="user-meta">
                    <div id="user-email">user@example.com</div>
                    <span id="user-tier" class="badge badge-free">free</span>
                </div>
                <button class="btn-logout" onclick="logout()" title="Sign out">↪</button>
            </div>
        </div>
    </aside>

    <!-- ── Main ────────────────────────────────────── -->
    <div class="main">

        <!-- Overview -->
        <section id="section-dashboard">
            <div class="pg-topbar">
                <span class="pg-title">Overview</span>
                <button class="btn btn-primary" onclick="generateEpisode()">+ New Episode</button>
            </div>
            <div class="content">
                <div class="grid g3">
                    <div class="metric">
                        <div class="m-label">Episodes This Month</div>
                        <div class="m-value" id="stat-episodes">—</div>
                        <div class="m-bar">
                            <div class="progress"><div class="progress-bar" id="progress-episodes" style="width:0%"></div></div>
                        </div>
                    </div>
                    <div class="metric">
                        <div class="m-label">API Calls</div>
                        <div class="m-value" id="stat-api">—</div>
                        <div class="m-bar">
                            <div class="progress"><div class="progress-bar" id="progress-api" style="width:0%"></div></div>
                        </div>
                    </div>
                    <div class="metric">
                        <div class="m-label">Storage Used</div>
                        <div class="m-value" id="stat-storage">—</div>
                        <div class="m-bar">
                            <div class="progress"><div class="progress-bar" id="progress-storage" style="width:0%"></div></div>
                        </div>
                    </div>
                </div>

                <div class="grid g-wide">
                    <div class="card">
                        <div class="ch"><span class="ct">Recent Episodes</span></div>
                        <div id="recent-episodes">
                            <div class="empty"><div class="empty-icon">📻</div><p>No episodes yet</p></div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="ch"><span class="ct">Quick Actions</span></div>
                        <div style="display:flex;flex-direction:column;gap:8px">
                            <button class="action-tile" onclick="generateEpisode()">
                                <span class="ai">✦</span> Generate Episode
                            </button>
                            <button class="action-tile" onclick="showSection('podcasts'); openModal('podcast-modal')">
                                <span class="ai">＋</span> New Podcast
                            </button>
                            <button class="action-tile" onclick="showSection('settings')">
                                <span class="ai">⚙</span> Configure Voices
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Podcasts -->
        <section id="section-podcasts">
            <div class="pg-topbar">
                <span class="pg-title">Podcasts</span>
                <button class="btn btn-primary" onclick="openModal('podcast-modal')">+ New Podcast</button>
            </div>
            <div class="content">
                <div class="card">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Title</th><th>Episodes</th><th>TTS Provider</th><th>Created</th><th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="podcasts-table"></tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ScriptFlow -->
        <section id="section-scriptflow">
            <div class="pg-topbar"><span class="pg-title">ScriptFlow</span></div>
            <div class="content">
                <div class="empty" style="padding:80px 20px">
                    <div class="empty-icon">✍️</div>
                    <p>Script editor — open from a podcast's episode tab</p>
                </div>
            </div>
        </section>

        <!-- Settings -->
        <section id="section-settings">
            <div class="pg-topbar"><span class="pg-title">Settings</span></div>
            <div class="content">
                <div class="grid g2">
                    <div class="card">
                        <div class="ch"><span class="ct">Profile</span></div>
                        <div class="form-group">
                            <label class="form-label">Name</label>
                            <input type="text" class="form-input" id="settings-name" placeholder="Your name">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Company</label>
                            <input type="text" class="form-input" id="settings-company" placeholder="Company name">
                        </div>
                        <button class="btn btn-primary" onclick="saveProfile()">Save Profile</button>
                    </div>

                    <div class="card card-accent">
                        <div class="ch">
                            <span class="ct">🎙 Voice Settings</span>
                            <span class="badge badge-pro">Recommended</span>
                        </div>
                        <div class="form-group">
                            <label class="form-label">TTS Provider</label>
                            <select class="form-select" id="settings-tts-provider">
                                <option value="elevenlabs">ElevenLabs (Premium)</option>
                                <option value="voxtral">Voxtral (High Quality)</option>
                                <option value="minimax">MiniMax (Budget)</option>
                                <option value="openai">OpenAI TTS</option>
                            </select>
                            <div class="form-hint">Pro → 11Labs · Growth → Voxtral · Free → MiniMax</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Host 1 Voice ID</label>
                            <input type="text" class="form-input" id="settings-voice-1" placeholder="Voice ID">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Host 2 Voice ID</label>
                            <input type="text" class="form-input" id="settings-voice-2" placeholder="Voice ID">
                        </div>
                        <button class="btn btn-primary" onclick="saveSettings()">Save Settings</button>
                    </div>

                    <div class="card">
                        <div class="ch">
                            <span class="ct">API Keys</span>
                            <span class="badge badge-pro">Pro</span>
                        </div>
                        <div id="api-keys-list">
                            <div class="empty"><div class="empty-icon">🔑</div><p>No API keys</p></div>
                        </div>
                        <button class="btn btn-secondary" onclick="openModal('apikey-modal')" style="margin-top:14px">+ Generate API Key</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- Billing -->
        <section id="section-billing">
            <div class="pg-topbar"><span class="pg-title">Billing</span></div>
            <div class="content">
                <div class="grid g2">
                    <div class="card">
                        <div class="ch">
                            <span class="ct">Current Plan</span>
                            <span id="billing-tier" class="badge badge-free">Free</span>
                        </div>
                        <div id="plan-features">
                            <div class="stat"><span class="stat-label">Episodes / month</span><span class="stat-value">3</span></div>
                            <div class="stat"><span class="stat-label">API calls / month</span><span class="stat-value">100</span></div>
                            <div class="stat"><span class="stat-label">Storage</span><span class="stat-value">100 MB</span></div>
                            <div class="stat"><span class="stat-label">Podcasts</span><span class="stat-value">1</span></div>
                        </div>
                        <button class="btn btn-primary" style="margin-top:20px;width:100%">Upgrade to Pro</button>
                    </div>
                    <div class="card">
                        <div class="ch"><span class="ct">Usage History</span></div>
                        <div id="usage-history">
                            <div class="empty"><div class="empty-icon">📊</div><p>No usage data yet</p></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

    </div><!-- .main -->
</div><!-- .app -->

<!-- ── Modals ───────────────────────────────────────── -->

<div id="podcast-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <span class="modal-title">Create Podcast</span>
            <button class="modal-close" onclick="closeModal('podcast-modal')">&times;</button>
        </div>
        <form onsubmit="createPodcast(event)">
            <div class="form-group">
                <label class="form-label">Title *</label>
                <input type="text" class="form-input" id="podcast-title" required placeholder="My Podcast">
            </div>
            <div class="form-group">
                <label class="form-label">Description</label>
                <textarea class="form-textarea" id="podcast-description" placeholder="What is this podcast about?"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Language</label>
                <select class="form-select" id="podcast-language">
                    <option value="en" selected>English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                </select>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:15px">
                <div>
                    <label class="form-label">Host 1 Name</label>
                    <input type="text" class="form-input" id="podcast-host-1" value="Alex">
                </div>
                <div>
                    <label class="form-label">Host 2 Name</label>
                    <input type="text" class="form-input" id="podcast-host-2" value="Maya">
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">TTS Provider</label>
                <select class="form-select" id="podcast-tts">
                    <option value="elevenlabs" selected>ElevenLabs (Premium)</option>
                    <option value="voxtral">Voxtral (High Quality)</option>
                    <option value="minimax">MiniMax (Budget)</option>
                    <option value="openai">OpenAI TTS</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Target Word Count</label>
                <input type="number" class="form-input" id="podcast-word-count" value="1500">
            </div>
            <div style="display:flex;gap:10px;justify-content:flex-end">
                <button type="button" class="btn btn-secondary" onclick="closeModal('podcast-modal')">Cancel</button>
                <button type="submit" id="btn-create-podcast" class="btn btn-primary">Create Podcast</button>
            </div>
        </form>
    </div>
</div>

<div id="apikey-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <span class="modal-title">Generate API Key</span>
            <button class="modal-close" onclick="closeModal('apikey-modal')">&times;</button>
        </div>
        <form onsubmit="createApiKey(event)">
            <div class="form-group">
                <label class="form-label">Key Name *</label>
                <input type="text" class="form-input" id="apikey-name" required placeholder="Production API">
            </div>
            <div class="form-group">
                <label class="form-label">Rate Limit (calls/hour)</label>
                <input type="number" class="form-input" id="apikey-rate" value="100">
            </div>
            <div class="form-group">
                <label class="form-label">Expires In (days, optional)</label>
                <input type="number" class="form-input" id="apikey-expires" placeholder="Never">
            </div>
            <div style="display:flex;gap:10px;justify-content:flex-end">
                <button type="button" class="btn btn-secondary" onclick="closeModal('apikey-modal')">Cancel</button>
                <button type="submit" class="btn btn-primary">Generate Key</button>
            </div>
        </form>
    </div>
</div>

<div id="generate-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <span class="modal-title">Generate Episode</span>
            <button class="modal-close" onclick="closeModal('generate-modal')">&times;</button>
        </div>
        <form onsubmit="submitGenerate(event)">
            <div class="form-group">
                <label class="form-label">Select Podcast *</label>
                <select class="form-select" id="generate-podcast" required></select>
            </div>
            <div class="form-group">
                <label class="form-label">Episode Date</label>
                <input type="date" class="form-input" id="generate-date">
            </div>
            <div class="form-group">
                <label style="display:flex;align-items:center;gap:9px;cursor:pointer;color:var(--t2);font-size:13.5px">
                    <input type="checkbox" id="generate-script-only">
                    Script only (no audio generation)
                </label>
            </div>
            <div style="display:flex;gap:10px;justify-content:flex-end">
                <button type="button" class="btn btn-secondary" onclick="closeModal('generate-modal')">Cancel</button>
                <button type="submit" class="btn btn-primary">Generate</button>
            </div>
        </form>
    </div>
</div>

<div id="toast" class="toast"></div>

<script>
    let state = { user: null, podcasts: [], episodes: [], apiKeys: [] };
    const API_BASE = '/api/v1';
    let token = localStorage.getItem('access_token');

    async function apiCall(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
        const response = await fetch(API_BASE + endpoint, { ...options, headers });
        if (response.status === 401) { logout(); throw new Error('Unauthorized'); }
        return response;
    }

    async function init() {
        if (!token) { window.location.href = '/login'; return; }
        await loadUser();
        await loadPodcasts();
        await loadEpisodes();
        if (state.user && state.user.subscription_tier !== 'free') {
            await loadApiKeys();
        }
    }

    async function loadUser() {
        try {
            const response = await apiCall('/user/me');
            state.user = await response.json();
            renderUser(); renderUsage();
        } catch (e) { console.error('Failed to load user', e); }
    }

    async function loadPodcasts() {
        try {
            const response = await apiCall('/podcasts');
            state.podcasts = await response.json();
            renderPodcasts(); renderPodcastSelect();
        } catch (e) { console.error('Failed to load podcasts', e); }
    }

    async function loadEpisodes() {
        const allEpisodes = [];
        for (const podcast of state.podcasts) {
            try {
                const response = await apiCall(`/podcasts/${podcast.id}/episodes`);
                const episodes = await response.json();
                allEpisodes.push(...episodes.map(e => ({...e, podcast_title: podcast.title})));
            } catch (e) { console.error('Failed to load episodes for podcast', podcast.id, e); }
        }
        state.episodes = allEpisodes.sort((a, b) => new Date(b.date) - new Date(a.date));
        renderEpisodes();
    }

    async function loadApiKeys() {
        try {
            const response = await apiCall('/api-keys');
            state.apiKeys = await response.json();
            renderApiKeys();
        } catch (e) { state.apiKeys = []; }
    }

    function renderUser() {
        document.getElementById('user-email').textContent = state.user.email;
        document.getElementById('user-tier').textContent = state.user.subscription_tier.toUpperCase();
        document.getElementById('user-tier').className = `badge badge-${state.user.subscription_tier}`;
        document.getElementById('billing-tier').textContent = state.user.subscription_tier.toUpperCase();
        document.getElementById('billing-tier').className = `badge badge-${state.user.subscription_tier}`;
        document.getElementById('settings-name').value = state.user.name || '';
        document.getElementById('settings-company').value = state.user.company || '';
        document.getElementById('settings-tts-provider').value = state.user.default_tts_provider || 'elevenlabs';
        document.getElementById('settings-voice-1').value = state.user.default_voice_host_1 || '';
        document.getElementById('settings-voice-2').value = state.user.default_voice_host_2 || '';
        // Update avatar initial
        const avi = document.querySelector('.user-avi');
        if (avi && state.user.email) avi.textContent = state.user.email[0].toUpperCase();
    }

    function renderUsage() {
        const usage = {
            episodes: state.user.episodes_generated_this_month,
            api: state.user.api_calls_this_month,
            storage: state.user.storage_used_mb
        };
        const limits = { episodes: 3, api: 100, storage: 100 };
        document.getElementById('stat-episodes').textContent = `${usage.episodes} / ${limits.episodes}`;
        document.getElementById('stat-api').textContent = `${usage.api} / ${limits.api}`;
        document.getElementById('stat-storage').textContent = `${usage.storage.toFixed(1)} MB / ${limits.storage} MB`;
        const episodePct = (usage.episodes / limits.episodes) * 100;
        const apiPct = (usage.api / limits.api) * 100;
        const storagePct = (usage.storage / limits.storage) * 100;
        const episodeBar = document.getElementById('progress-episodes');
        const apiBar = document.getElementById('progress-api');
        const storageBar = document.getElementById('progress-storage');
        episodeBar.style.width = `${Math.min(episodePct, 100)}%`;
        apiBar.style.width = `${Math.min(apiPct, 100)}%`;
        storageBar.style.width = `${Math.min(storagePct, 100)}%`;
        episodeBar.className = `progress-bar ${episodePct > 80 ? 'red' : episodePct > 50 ? 'yellow' : 'green'}`;
        apiBar.className = `progress-bar ${apiPct > 80 ? 'red' : apiPct > 50 ? 'yellow' : 'green'}`;
        storageBar.className = `progress-bar ${storagePct > 80 ? 'red' : storagePct > 50 ? 'yellow' : 'green'}`;
    }

    function renderPodcasts() {
        const tbody = document.getElementById('podcasts-table');
        if (state.podcasts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--t3);padding:32px">No podcasts yet — create one to get started</td></tr>';
            return;
        }
        tbody.innerHTML = state.podcasts.map(p => `
            <tr>
                <td><strong>${escapeHtml(p.title)}</strong></td>
                <td>${p.total_episodes}</td>
                <td>${p.tts_provider}</td>
                <td>${new Date(p.created_at).toLocaleDateString()}</td>
                <td style="display:flex;gap:6px">
                    <button class="btn btn-secondary" style="padding:5px 11px;font-size:12px" onclick="viewPodcast(${p.id})">View</button>
                    <button class="btn btn-danger" style="padding:5px 11px;font-size:12px" onclick="deletePodcast(${p.id})">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    function renderPodcastSelect() {
        const select = document.getElementById('generate-podcast');
        select.innerHTML = state.podcasts.map(p => `<option value="${p.id}">${escapeHtml(p.title)}</option>`).join('');
    }

    function renderEpisodes() {
        const container = document.getElementById('recent-episodes');
        if (state.episodes.length === 0) {
            container.innerHTML = '<div class="empty"><div class="empty-icon">📻</div><p>No episodes yet</p></div>';
            return;
        }
        container.innerHTML = `
            <table class="table">
                <thead><tr><th>Podcast</th><th>Title</th><th>Status</th><th>Date</th></tr></thead>
                <tbody>
                    ${state.episodes.slice(0, 5).map(e => `
                        <tr>
                            <td>${escapeHtml(e.podcast_title)}</td>
                            <td>${escapeHtml(e.title || '—')}</td>
                            <td><span class="status status-${e.status}">${e.status}</span></td>
                            <td>${new Date(e.date).toLocaleDateString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    function renderApiKeys() {
        const container = document.getElementById('api-keys-list');
        if (state.apiKeys.length === 0) {
            container.innerHTML = '<div class="empty"><div class="empty-icon">🔑</div><p>No API keys</p></div>';
            return;
        }
        container.innerHTML = `
            <table class="table">
                <thead><tr><th>Name</th><th>Prefix</th><th>Usage</th><th>Created</th></tr></thead>
                <tbody>
                    ${state.apiKeys.map(k => `
                        <tr>
                            <td>${escapeHtml(k.name)}</td>
                            <td><code>${k.prefix}****</code></td>
                            <td>${k.total_calls} calls</td>
                            <td>${new Date(k.created_at).toLocaleDateString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    async function createPodcast(event) {
        event.preventDefault();
        const data = {
            title: document.getElementById('podcast-title').value,
            description: document.getElementById('podcast-description').value,
            language: document.getElementById('podcast-language').value,
            host_1_name: document.getElementById('podcast-host-1').value,
            host_2_name: document.getElementById('podcast-host-2').value,
            tts_provider: document.getElementById('podcast-tts').value,
            target_word_count: parseInt(document.getElementById('podcast-word-count').value)
        };
        try {
            const response = await apiCall('/podcasts', { method: 'POST', body: JSON.stringify(data) });
            if (!response.ok) throw new Error('Failed to create podcast');
            closeModal('podcast-modal');
            showToast('Podcast created', 'success');
            await loadPodcasts();
        } catch (e) { showToast(e.message, 'error'); }
    }

    async function deletePodcast(id) {
        if (!confirm('Delete this podcast and all its episodes?')) return;
        try {
            const response = await apiCall(`/podcasts/${id}`, { method: 'DELETE' });
            if (!response.ok) throw new Error('Failed to delete podcast');
            showToast('Podcast deleted', 'success');
            await loadPodcasts();
        } catch (e) { showToast(e.message, 'error'); }
    }

    function viewPodcast(id) {
        showToast('Podcast detail view coming soon', 'info');
    }

    async function saveProfile() {
        const data = {
            name: document.getElementById('settings-name').value,
            company: document.getElementById('settings-company').value
        };
        try {
            const response = await apiCall('/user/me', { method: 'PUT', body: JSON.stringify(data) });
            if (!response.ok) throw new Error('Failed to save profile');
            showToast('Profile saved', 'success');
        } catch (e) { showToast(e.message, 'error'); }
    }

    async function saveSettings() {
        const data = {
            default_tts_provider: document.getElementById('settings-tts-provider').value,
            default_voice_host_1: document.getElementById('settings-voice-1').value,
            default_voice_host_2: document.getElementById('settings-voice-2').value
        };
        try {
            const response = await apiCall('/user/me', { method: 'PUT', body: JSON.stringify(data) });
            if (!response.ok) throw new Error('Failed to save settings');
            showToast('Settings saved', 'success');
        } catch (e) { showToast(e.message, 'error'); }
    }

    async function createApiKey(event) {
        event.preventDefault();
        const data = {
            name: document.getElementById('apikey-name').value,
            rate_limit_per_hour: parseInt(document.getElementById('apikey-rate').value),
            expires_in_days: document.getElementById('apikey-expires').value ? parseInt(document.getElementById('apikey-expires').value) : null
        };
        try {
            const response = await apiCall('/api-keys', { method: 'POST', body: JSON.stringify(data) });
            if (!response.ok) throw new Error('Failed to create API key');
            const result = await response.json();
            closeModal('apikey-modal');
            showToast(`API Key: ${result.key}`, 'success');
            await loadApiKeys();
        } catch (e) { showToast(e.message, 'error'); }
    }

    function generateEpisode() {
        if (state.podcasts.length === 0) { showToast('Create a podcast first', 'error'); return; }
        openModal('generate-modal');
        document.getElementById('generate-date').value = new Date().toISOString().split('T')[0];
    }

    async function submitGenerate(event) {
        event.preventDefault();
        const data = {
            podcast_id: parseInt(document.getElementById('generate-podcast').value),
            date: document.getElementById('generate-date').value,
            script_only: document.getElementById('generate-script-only').checked
        };
        try {
            const response = await apiCall('/episodes/generate', { method: 'POST', body: JSON.stringify(data) });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to generate episode');
            }
            closeModal('generate-modal');
            showToast('Episode generation started', 'success');
            await loadEpisodes(); await loadUser();
        } catch (e) { showToast(e.message, 'error'); }
    }

    function logout() {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    }

    function showSection(section) {
        document.querySelectorAll('section').forEach(s => s.style.display = 'none');
        document.getElementById(`section-${section}`).style.display = 'block';
        document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
        event.target.classList.add('active');
    }

    function openModal(id)  { document.getElementById(id).classList.add('open'); }
    function closeModal(id) { document.getElementById(id).classList.remove('open'); }

    function showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type} show`;
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    init();
</script>
</body>
</html>
"""


LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindStream — Sign In</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@500;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
            --bg: #06060d;
            --card: #0f0f1e;
            --input-bg: #0c0c1c;
            --a1: #6366f1;
            --a2: #8b5cf6;
            --a3: #d946ef;
            --grad: linear-gradient(135deg, #6366f1 0%, #8b5cf6 55%, #d946ef 100%);
            --t1: #eeeeff;
            --t2: #7878a8;
            --t3: #3d3d62;
            --border: rgba(99,102,241,.15);
            --border-s: rgba(255,255,255,.05);
            --err: #ef4444;
        }
        html, body { height: 100%; }
        body {
            font-family: 'DM Sans', system-ui, sans-serif;
            background: var(--bg);
            color: var(--t1);
            min-height: 100vh;
            display: flex;
            -webkit-font-smoothing: antialiased;
        }

        /* ── Left panel ─────────────────────────────── */
        .auth-left {
            width: 42%;
            background: var(--bg);
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 60px 52px;
            overflow: hidden;
            border-right: 1px solid var(--border-s);
        }
        .auth-left::before {
            content: '';
            position: absolute; top: -30%; left: -20%;
            width: 80%; height: 80%;
            background: radial-gradient(ellipse, rgba(99,102,241,.18) 0%, transparent 70%);
            pointer-events: none;
        }
        .auth-left::after {
            content: '';
            position: absolute; bottom: -20%; right: -10%;
            width: 70%; height: 70%;
            background: radial-gradient(ellipse, rgba(217,70,239,.11) 0%, transparent 70%);
            pointer-events: none;
        }

        .left-content { position: relative; z-index: 1; }

        .brand {
            display: flex; align-items: center; gap: 12px;
            margin-bottom: 48px;
        }
        .brand-mark {
            width: 42px; height: 42px;
            background: var(--grad);
            border-radius: 11px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
            box-shadow: 0 6px 20px rgba(99,102,241,.4);
        }
        .brand-name {
            font-family: 'Syne', sans-serif;
            font-size: 20px; font-weight: 800;
            letter-spacing: -.03em;
        }

        .left-headline {
            font-family: 'Syne', sans-serif;
            font-size: 32px; font-weight: 800;
            line-height: 1.12; letter-spacing: -.04em;
            margin-bottom: 16px;
        }
        .left-headline span {
            background: var(--grad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .left-sub {
            color: var(--t2); font-size: 15px; font-weight: 400;
            line-height: 1.6; margin-bottom: 40px;
            max-width: 320px;
        }

        .feature-list { display: flex; flex-direction: column; gap: 12px; }
        .feature-item {
            display: flex; align-items: center; gap: 12px;
            font-size: 14px; color: var(--t2);
        }
        .feature-dot {
            width: 28px; height: 28px; border-radius: 8px;
            background: rgba(99,102,241,.12);
            border: 1px solid rgba(99,102,241,.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 13px; flex-shrink: 0;
        }

        /* ── Right panel ─────────────────────────────── */
        .auth-right {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 28px;
            background: #080810;
        }

        .auth-card {
            width: 100%; max-width: 400px;
        }

        .auth-header { text-align: center; margin-bottom: 28px; }
        .auth-title {
            font-family: 'Syne', sans-serif;
            font-size: 22px; font-weight: 700;
            letter-spacing: -.03em; margin-bottom: 6px;
        }
        .auth-sub { color: var(--t2); font-size: 14px; }

        /* Tabs */
        .tabs {
            display: flex;
            background: rgba(255,255,255,.04);
            border: 1px solid var(--border-s);
            border-radius: 10px;
            padding: 4px; gap: 4px;
            margin-bottom: 24px;
        }
        .tab {
            flex: 1; padding: 8px 12px;
            text-align: center; cursor: pointer;
            border-radius: 7px;
            font-size: 13.5px; font-weight: 600;
            color: var(--t2);
            transition: all .15s;
            border: none; background: none;
        }
        .tab.active {
            background: rgba(99,102,241,.18);
            color: var(--t1);
        }

        /* Form */
        .form-group { margin-bottom: 14px; }
        .form-label { display: block; margin-bottom: 5px; font-size: 12.5px; font-weight: 600; color: var(--t2); }
        .form-input {
            width: 100%; padding: 10px 13px;
            border: 1px solid var(--border-s); border-radius: 9px;
            background: var(--input-bg); color: var(--t1);
            font-size: 14px; font-family: 'DM Sans', sans-serif;
            transition: border-color .15s;
        }
        .form-input::placeholder { color: var(--t3); }
        .form-input:focus {
            outline: none;
            border-color: rgba(99,102,241,.5);
            box-shadow: 0 0 0 3px rgba(99,102,241,.09);
        }

        .btn-submit {
            width: 100%; padding: 11px;
            border-radius: 9px; border: none;
            background: var(--grad); color: #fff;
            font-size: 14.5px; font-weight: 700;
            font-family: 'DM Sans', sans-serif;
            cursor: pointer; margin-top: 6px;
            transition: all .15s;
            box-shadow: 0 2px 14px rgba(99,102,241,.3);
        }
        .btn-submit:hover { opacity: .88; transform: translateY(-1px); box-shadow: 0 4px 20px rgba(99,102,241,.45); }
        .btn-submit:disabled { opacity: .4; cursor: not-allowed; transform: none; }

        .error {
            background: rgba(239,68,68,.1); color: #fca5a5;
            border: 1px solid rgba(239,68,68,.2);
            padding: 10px 14px; border-radius: 8px;
            margin-bottom: 16px; font-size: 13.5px;
            display: none;
        }

        @media (max-width: 720px) {
            .auth-left { display: none; }
            .auth-right { background: var(--bg); }
        }
    </style>
</head>
<body>

    <!-- Left panel -->
    <div class="auth-left">
        <div class="left-content">
            <div class="brand">
                <div class="brand-mark">🎙</div>
                <div class="brand-name">MindStream</div>
            </div>
            <h1 class="left-headline">
                Your ideas,<br><span>broadcast-ready</span>
            </h1>
            <p class="left-sub">
                AI writes the script, clones the voices, and publishes — all from a single memo.
            </p>
            <div class="feature-list">
                <div class="feature-item">
                    <div class="feature-dot">✦</div>
                    AI script generation from any source
                </div>
                <div class="feature-item">
                    <div class="feature-dot">🎙</div>
                    Multi-voice TTS with ElevenLabs & MiniMax
                </div>
                <div class="feature-item">
                    <div class="feature-dot">⚡</div>
                    Auto-publish to Transistor.fm
                </div>
            </div>
        </div>
    </div>

    <!-- Right panel -->
    <div class="auth-right">
        <div class="auth-card">
            <div class="auth-header">
                <div class="auth-title">Welcome back</div>
                <div class="auth-sub">Sign in to your studio</div>
            </div>

            <div class="tabs">
                <button class="tab active" id="tab-login" onclick="showTab('login')">Sign In</button>
                <button class="tab" id="tab-register" onclick="showTab('register')">Create Account</button>
            </div>

            <div id="error" class="error"></div>

            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-input" id="login-email" required placeholder="you@example.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" class="form-input" id="login-password" required placeholder="••••••••">
                </div>
                <button type="submit" class="btn-submit">Sign In</button>
            </form>

            <form id="register-form" onsubmit="handleRegister(event)" style="display:none">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-input" id="register-email" required placeholder="you@example.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" class="form-input" id="register-password" required minlength="8" placeholder="Min 8 characters">
                </div>
                <div class="form-group">
                    <label class="form-label">Name <span style="color:var(--t3)">(optional)</span></label>
                    <input type="text" class="form-input" id="register-name" placeholder="Your name">
                </div>
                <div class="form-group">
                    <label class="form-label">Company <span style="color:var(--t3)">(optional)</span></label>
                    <input type="text" class="form-input" id="register-company" placeholder="Company name">
                </div>
                <button type="submit" class="btn-submit">Create Account</button>
            </form>
        </div>
    </div>

<script>
    const API_BASE = '/api/v1';
    let currentTab = 'login';

    function showTab(tab) {
        currentTab = tab;
        document.getElementById('tab-login').classList.toggle('active', tab === 'login');
        document.getElementById('tab-register').classList.toggle('active', tab === 'register');
        document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
        document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';
        document.getElementById('error').style.display = 'none';
    }

    function showError(message) {
        const el = document.getElementById('error');
        el.textContent = message; el.style.display = 'block';
    }

    async function handleLogin(event) {
        event.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Signing in…'; submitBtn.disabled = true;
        try {
            const response = await fetch(API_BASE + '/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (!response.ok) { const err = await response.json(); throw new Error(err.detail || 'Login failed'); }
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            window.location.href = '/dashboard';
        } catch (e) {
            showError(e.message);
            submitBtn.textContent = originalText; submitBtn.disabled = false;
        }
    }

    async function handleRegister(event) {
        event.preventDefault();
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const name = document.getElementById('register-name').value;
        const company = document.getElementById('register-company').value;
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Creating account…'; submitBtn.disabled = true;
        try {
            const response = await fetch(API_BASE + '/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, name, company })
            });
            if (!response.ok) { const err = await response.json(); throw new Error(err.detail || 'Registration failed'); }
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            window.location.href = '/dashboard';
        } catch (e) {
            showError(e.message);
            submitBtn.textContent = originalText; submitBtn.disabled = false;
        }
    }
</script>
</body>
</html>
"""


def get_dashboard_html():
    """Return the dashboard HTML template."""
    return DASHBOARD_HTML


def get_login_html(default_tab: str = "login"):
    """Return the login HTML template with optional default tab."""
    if default_tab == "register":
        inject = '<script>document.addEventListener("DOMContentLoaded", function() { showTab("register"); document.title = "MindStream \u2014 Create Account"; });</script>'
        return LOGIN_HTML.replace("</body>", f"{inject}</body>")
    return LOGIN_HTML
