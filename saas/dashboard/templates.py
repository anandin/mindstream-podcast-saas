"""
Dashboard templates for SaaS podcast generator.
"""
import os
from pathlib import Path

# Read template from file
TEMPLATE_DIR = Path(__file__).parent


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mind Stream - Podcast Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid #30363d; margin-bottom: 30px; }
        .logo { font-size: 24px; font-weight: bold; color: #58a6ff; }
        .user-menu { display: flex; align-items: center; gap: 20px; }
        .user-info { text-align: right; }
        .user-email { font-size: 14px; color: #8b949e; }
        .badge { padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .badge-free { background: #238636; color: #fff; }
        .badge-pro { background: #f0883e; color: #fff; }
        .badge-enterprise { background: #a371f7; color: #fff; }
        
        /* Navigation */
        nav { display: flex; gap: 10px; margin-bottom: 30px; }
        nav a { padding: 10px 20px; border-radius: 6px; text-decoration: none; color: #c9d1d9; background: #21262d; transition: all 0.2s; }
        nav a:hover, nav a.active { background: #30363d; color: #fff; }
        
        /* Grid */
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .card-title { font-size: 16px; font-weight: 600; }
        
        /* Stats */
        .stat { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
        .stat:last-child { border-bottom: none; }
        .stat-label { color: #8b949e; }
        .stat-value { font-weight: 600; }
        .stat-value.success { color: #3fb950; }
        .stat-value.warning { color: #d29922; }
        .stat-value.danger { color: #f85149; }
        
        /* Progress bars */
        .progress { height: 8px; background: #30363d; border-radius: 4px; margin-top: 10px; overflow: hidden; }
        .progress-bar { height: 100%; border-radius: 4px; transition: width 0.3s; }
        .progress-bar.green { background: #238636; }
        .progress-bar.yellow { background: #d29922; }
        .progress-bar.red { background: #f85149; }
        
        /* Buttons */
        .btn { padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .btn-primary { background: #238636; color: #fff; }
        .btn-primary:hover { background: #2ea043; }
        .btn-secondary { background: #30363d; color: #c9d1d9; }
        .btn-secondary:hover { background: #3d444d; }
        .btn-danger { background: #da3633; color: #fff; }
        .btn-danger:hover { background: #f85149; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        /* Forms */
        .form-group { margin-bottom: 20px; }
        .form-label { display: block; margin-bottom: 8px; font-weight: 500; }
        .form-input, .form-select, .form-textarea { width: 100%; padding: 10px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #c9d1d9; font-size: 14px; }
        .form-input:focus, .form-select:focus, .form-textarea:focus { outline: none; border-color: #58a6ff; }
        .form-textarea { min-height: 100px; resize: vertical; }
        
        /* Tables */
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #30363d; }
        .table th { font-weight: 600; color: #8b949e; font-size: 12px; text-transform: uppercase; }
        .table tr:hover { background: #21262d; }
        
        /* Status badges */
        .status { padding: 4px 8px; border-radius: 12px; font-size: 12px; }
        .status-draft { background: #30363d; }
        .status-generating { background: #1f6feb; color: #fff; }
        .status-ready { background: #238636; color: #fff; }
        .status-published { background: #a371f7; color: #fff; }
        .status-failed { background: #da3633; color: #fff; }
        
        /* Modal */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; }
        .modal.open { display: flex; align-items: center; justify-content: center; }
        .modal-content { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 30px; max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .modal-title { font-size: 20px; font-weight: 600; }
        .modal-close { background: none; border: none; color: #8b949e; font-size: 24px; cursor: pointer; }
        
        /* Toast */
        .toast { position: fixed; bottom: 20px; right: 20px; padding: 15px 20px; border-radius: 6px; color: #fff; font-weight: 500; transform: translateY(100px); opacity: 0; transition: all 0.3s; z-index: 1001; }
        .toast.show { transform: translateY(0); opacity: 1; }
        .toast.success { background: #238636; }
        .toast.error { background: #da3633; }
        .toast.info { background: #1f6feb; }
        
        /* Tabs */
        .tabs { display: flex; gap: 5px; border-bottom: 1px solid #30363d; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent; color: #8b949e; }
        .tab.active { border-bottom-color: #58a6ff; color: #fff; }
        
        /* Loading */
        .loading { display: inline-block; width: 20px; height: 20px; border: 2px solid #30363d; border-top-color: #58a6ff; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        /* Empty state */
        .empty { text-align: center; padding: 60px 20px; color: #8b949e; }
        .empty-icon { font-size: 48px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🎙️ Mind Stream</div>
            <div class="user-menu">
                <div class="user-info">
                    <div id="user-email">user@example.com</div>
                    <div><span id="user-tier" class="badge badge-free">Free</span></div>
                </div>
                <button class="btn btn-secondary" onclick="logout()">Logout</button>
            </div>
        </header>
        
        <nav>
            <a href="#dashboard" class="active" onclick="showSection('dashboard')">Dashboard</a>
            <a href="#podcasts" onclick="showSection('podcasts')">Podcasts</a>
            <a href="#settings" onclick="showSection('settings')">Settings</a>
            <a href="#billing" onclick="showSection('billing')">Billing</a>
        </nav>
        
        <!-- Dashboard Section -->
        <section id="section-dashboard">
            <div class="grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Usage This Month</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Episodes</span>
                        <span class="stat-value" id="stat-episodes">0 / 3</span>
                    </div>
                    <div class="progress"><div class="progress-bar" id="progress-episodes" style="width: 0%"></div></div>
                    
                    <div class="stat" style="margin-top: 20px">
                        <span class="stat-label">API Calls</span>
                        <span class="stat-value" id="stat-api">0 / 100</span>
                    </div>
                    <div class="progress"><div class="progress-bar" id="progress-api" style="width: 0%"></div></div>
                    
                    <div class="stat" style="margin-top: 20px">
                        <span class="stat-label">Storage</span>
                        <span class="stat-value" id="stat-storage">0 MB / 100 MB</span>
                    </div>
                    <div class="progress"><div class="progress-bar" id="progress-storage" style="width: 0%"></div></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Quick Actions</span>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <button class="btn btn-primary" onclick="generateEpisode()">+ Generate Episode</button>
                        <button class="btn btn-secondary" onclick="showSection('podcasts'); openModal('podcast-modal')">+ New Podcast</button>
                        <button class="btn btn-secondary" onclick="showSection('settings')">⚙️ Configure Voices</button>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Recent Episodes</span>
                    </div>
                    <div id="recent-episodes">
                        <div class="empty">
                            <div class="empty-icon">📻</div>
                            <p>No episodes yet</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Podcasts Section -->
        <section id="section-podcasts" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Your Podcasts</span>
                    <button class="btn btn-primary" onclick="openModal('podcast-modal')">+ New Podcast</button>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Episodes</th>
                            <th>TTS Provider</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="podcasts-table">
                    </tbody>
                </table>
            </div>
        </section>
        
        <!-- Settings Section -->
        <section id="section-settings" style="display: none;">
            <div class="grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Profile Settings</span>
                    </div>
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
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Default TTS Settings</span>
                    </div>
                    <div class="form-group">
                        <label class="form-label">TTS Provider</label>
                        <select class="form-select" id="settings-tts-provider">
                            <option value="elevenlabs">ElevenLabs</option>
                            <option value="openai">OpenAI TTS</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Default Host 1 Voice</label>
                        <input type="text" class="form-input" id="settings-voice-1" placeholder="Voice ID">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Default Host 2 Voice</label>
                        <input type="text" class="form-input" id="settings-voice-2" placeholder="Voice ID">
                    </div>
                    <button class="btn btn-primary" onclick="saveSettings()">Save Settings</button>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">API Keys</span>
                        <span class="badge badge-pro">Pro</span>
                    </div>
                    <div id="api-keys-list">
                        <div class="empty">
                            <div class="empty-icon">🔑</div>
                            <p>No API keys</p>
                        </div>
                    </div>
                    <button class="btn btn-secondary" onclick="openModal('apikey-modal')" style="margin-top: 15px">+ Generate API Key</button>
                </div>
            </div>
        </section>
        
        <!-- Billing Section -->
        <section id="section-billing" style="display: none;">
            <div class="grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Current Plan</span>
                        <span id="billing-tier" class="badge badge-free">Free</span>
                    </div>
                    <div id="plan-features">
                        <div class="stat">
                            <span class="stat-label">Episodes per month</span>
                            <span class="stat-value">3</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">API calls per month</span>
                            <span class="stat-value">100</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Storage</span>
                            <span class="stat-value">100 MB</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Podcasts</span>
                            <span class="stat-value">1</span>
                        </div>
                    </div>
                    <button class="btn btn-primary" style="margin-top: 20px; width: 100%">Upgrade to Pro</button>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Usage History</span>
                    </div>
                    <div id="usage-history">
                        <div class="empty">
                            <div class="empty-icon">📊</div>
                            <p>No usage data yet</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
    
    <!-- Podcast Modal -->
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
                <div class="grid" style="margin-bottom: 20px">
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
                        <option value="elevenlabs" selected>ElevenLabs</option>
                        <option value="openai">OpenAI TTS</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Target Word Count</label>
                    <input type="number" class="form-input" id="podcast-word-count" value="1500">
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('podcast-modal')">Cancel</button>
                    <button type="submit" class="btn btn-primary">Create Podcast</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- API Key Modal -->
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
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('apikey-modal')">Cancel</button>
                    <button type="submit" class="btn btn-primary">Generate Key</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Generate Episode Modal -->
    <div id="generate-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title">Generate Episode</span>
                <button class="modal-close" onclick="closeModal('generate-modal')">&times;</button>
            </div>
            <form onsubmit="submitGenerate(event)">
                <div class="form-group">
                    <label class="form-label">Select Podcast *</label>
                    <select class="form-select" id="generate-podcast" required>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Episode Date</label>
                    <input type="date" class="form-input" id="generate-date">
                </div>
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <input type="checkbox" id="generate-script-only">
                        Script Only (no audio generation)
                    </label>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('generate-modal')">Cancel</button>
                    <button type="submit" class="btn btn-primary">Generate</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Toast -->
    <div id="toast" class="toast"></div>

    <script>
        // State
        let state = {
            user: null,
            podcasts: [],
            episodes: [],
            apiKeys: []
        };
        
        // API Base URL
        const API_BASE = '/api';
        
        // Auth
        let token = localStorage.getItem('access_token');
        
        async function apiCall(endpoint, options = {}) {
            const headers = {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
            };
            const response = await fetch(API_BASE + endpoint, { ...options, headers });
            if (response.status === 401) {
                logout();
                throw new Error('Unauthorized');
            }
            return response;
        }
        
        // Initialize
        async function init() {
            if (!token) {
                window.location.href = '/login';
                return;
            }
            await loadUser();
            await loadPodcasts();
            await loadEpisodes();
            await loadApiKeys();
        }
        
        async function loadUser() {
            try {
                const response = await apiCall('/user/me');
                state.user = await response.json();
                renderUser();
                renderUsage();
            } catch (e) {
                console.error('Failed to load user', e);
            }
        }
        
        async function loadPodcasts() {
            try {
                const response = await apiCall('/podcasts');
                state.podcasts = await response.json();
                renderPodcasts();
                renderPodcastSelect();
            } catch (e) {
                console.error('Failed to load podcasts', e);
            }
        }
        
        async function loadEpisodes() {
            // Load episodes for each podcast
            const allEpisodes = [];
            for (const podcast of state.podcasts) {
                try {
                    const response = await apiCall(`/podcasts/${podcast.id}/episodes`);
                    const episodes = await response.json();
                    allEpisodes.push(...episodes.map(e => ({...e, podcast_title: podcast.title})));
                } catch (e) {
                    console.error('Failed to load episodes for podcast', podcast.id, e);
                }
            }
            state.episodes = allEpisodes.sort((a, b) => new Date(b.date) - new Date(a.date));
            renderEpisodes();
        }
        
        async function loadApiKeys() {
            try {
                const response = await apiCall('/api-keys');
                state.apiKeys = await response.json();
                renderApiKeys();
            } catch (e) {
                // Pro feature, may fail for free tier
                state.apiKeys = [];
            }
        }
        
        // Render functions
        function renderUser() {
            document.getElementById('user-email').textContent = state.user.email;
            document.getElementById('user-tier').textContent = state.user.subscription_tier.toUpperCase();
            document.getElementById('user-tier').className = `badge badge-${state.user.subscription_tier}`;
            document.getElementById('billing-tier').textContent = state.user.subscription_tier.toUpperCase();
            document.getElementById('billing-tier').className = `badge badge-${state.user.subscription_tier}`;
            
            // Settings
            document.getElementById('settings-name').value = state.user.name || '';
            document.getElementById('settings-company').value = state.user.company || '';
            document.getElementById('settings-tts-provider').value = state.user.default_tts_provider || 'elevenlabs';
            document.getElementById('settings-voice-1').value = state.user.default_voice_host_1 || '';
            document.getElementById('settings-voice-2').value = state.user.default_voice_host_2 || '';
        }
        
        function renderUsage() {
            const usage = {
                episodes: state.user.episodes_generated_this_month,
                api: state.user.api_calls_this_month,
                storage: state.user.storage_used_mb
            };
            const limits = {
                episodes: 3,
                api: 100,
                storage: 100
            };
            
            // Update stats
            document.getElementById('stat-episodes').textContent = `${usage.episodes} / ${limits.episodes}`;
            document.getElementById('stat-api').textContent = `${usage.api} / ${limits.api}`;
            document.getElementById('stat-storage').textContent = `${usage.storage.toFixed(1)} MB / ${limits.storage} MB`;
            
            // Update progress bars
            const episodePct = (usage.episodes / limits.episodes) * 100;
            const apiPct = (usage.api / limits.api) * 100;
            const storagePct = (usage.storage / limits.storage) * 100;
            
            const episodeBar = document.getElementById('progress-episodes');
            const apiBar = document.getElementById('progress-api');
            const storageBar = document.getElementById('progress-storage');
            
            episodeBar.style.width = `${Math.min(episodePct, 100)}%`;
            apiBar.style.width = `${Math.min(apiPct, 100)}%`;
            storageBar.style.width = `${Math.min(storagePct, 100)}%`;
            
            // Color coding
            episodeBar.className = `progress-bar ${episodePct > 80 ? 'red' : episodePct > 50 ? 'yellow' : 'green'}`;
            apiBar.className = `progress-bar ${apiPct > 80 ? 'red' : apiPct > 50 ? 'yellow' : 'green'}`;
            storageBar.className = `progress-bar ${storagePct > 80 ? 'red' : storagePct > 50 ? 'yellow' : 'green'}`;
        }
        
        function renderPodcasts() {
            const tbody = document.getElementById('podcasts-table');
            if (state.podcasts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#8b949e">No podcasts yet</td></tr>';
                return;
            }
            tbody.innerHTML = state.podcasts.map(p => `
                <tr>
                    <td><strong>${escapeHtml(p.title)}</strong></td>
                    <td>${p.total_episodes}</td>
                    <td>${p.tts_provider}</td>
                    <td>${new Date(p.created_at).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewPodcast(${p.id})">View</button>
                        <button class="btn btn-danger" onclick="deletePodcast(${p.id})">Delete</button>
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
                    <thead>
                        <tr>
                            <th>Podcast</th>
                            <th>Title</th>
                            <th>Status</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${state.episodes.slice(0, 5).map(e => `
                            <tr>
                                <td>${escapeHtml(e.podcast_title)}</td>
                                <td>${escapeHtml(e.title || '-')}</td>
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
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Prefix</th>
                            <th>Usage</th>
                            <th>Created</th>
                        </tr>
                    </thead>
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
        
        // Actions
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
                const response = await apiCall('/podcasts', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                if (!response.ok) throw new Error('Failed to create podcast');
                closeModal('podcast-modal');
                showToast('Podcast created successfully', 'success');
                await loadPodcasts();
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        async function deletePodcast(id) {
            if (!confirm('Are you sure you want to delete this podcast?')) return;
            try {
                const response = await apiCall(`/podcasts/${id}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('Failed to delete podcast');
                showToast('Podcast deleted', 'success');
                await loadPodcasts();
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        async function saveProfile() {
            const data = {
                name: document.getElementById('settings-name').value,
                company: document.getElementById('settings-company').value
            };
            try {
                const response = await apiCall('/user/me', {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
                if (!response.ok) throw new Error('Failed to save profile');
                showToast('Profile saved', 'success');
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        async function saveSettings() {
            const data = {
                default_tts_provider: document.getElementById('settings-tts-provider').value,
                default_voice_host_1: document.getElementById('settings-voice-1').value,
                default_voice_host_2: document.getElementById('settings-voice-2').value
            };
            try {
                const response = await apiCall('/user/me', {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
                if (!response.ok) throw new Error('Failed to save settings');
                showToast('Settings saved', 'success');
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        async function createApiKey(event) {
            event.preventDefault();
            const data = {
                name: document.getElementById('apikey-name').value,
                rate_limit_per_hour: parseInt(document.getElementById('apikey-rate').value),
                expires_in_days: document.getElementById('apikey-expires').value ? parseInt(document.getElementById('apikey-expires').value) : null
            };
            try {
                const response = await apiCall('/api-keys', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                if (!response.ok) throw new Error('Failed to create API key');
                const result = await response.json();
                closeModal('apikey-modal');
                showToast(`API Key created: ${result.key}`, 'success');
                await loadApiKeys();
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        function generateEpisode() {
            if (state.podcasts.length === 0) {
                showToast('Create a podcast first', 'error');
                return;
            }
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
                const response = await apiCall('/episodes/generate', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Failed to generate episode');
                }
                closeModal('generate-modal');
                showToast('Episode generation started', 'success');
                await loadEpisodes();
                await loadUser();
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        function logout() {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
        
        // UI Helpers
        function showSection(section) {
            document.querySelectorAll('section').forEach(s => s.style.display = 'none');
            document.getElementById(`section-${section}`).style.display = 'block';
            document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        function openModal(id) {
            document.getElementById(id).classList.add('open');
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('open');
        }
        
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
        
        // Initialize on load
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
    <title>Login - Mind Stream</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: #0d1117; 
            color: #c9d1d9; 
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container { width: 100%; max-width: 400px; padding: 20px; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 32px; color: #58a6ff; }
        .logo p { color: #8b949e; margin-top: 10px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 30px; }
        .form-group { margin-bottom: 20px; }
        .form-label { display: block; margin-bottom: 8px; font-weight: 500; }
        .form-input { width: 100%; padding: 12px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #c9d1d9; font-size: 14px; }
        .form-input:focus { outline: none; border-color: #58a6ff; }
        .btn { width: 100%; padding: 12px; border-radius: 6px; border: none; cursor: pointer; font-size: 16px; font-weight: 500; transition: all 0.2s; }
        .btn-primary { background: #238636; color: #fff; }
        .btn-primary:hover { background: #2ea043; }
        .btn-secondary { background: #30363d; color: #c9d1d9; margin-top: 10px; }
        .btn-secondary:hover { background: #3d444d; }
        .error { background: #da3633; color: #fff; padding: 10px; border-radius: 6px; margin-bottom: 20px; display: none; }
        .tabs { display: flex; gap: 5px; margin-bottom: 20px; }
        .tab { flex: 1; padding: 10px; text-align: center; cursor: pointer; border-bottom: 2px solid transparent; color: #8b949e; }
        .tab.active { border-bottom-color: #58a6ff; color: #fff; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🎙️ Mind Stream</h1>
            <p>SaaS Podcast Generator</p>
        </div>
        
        <div class="card">
            <div class="tabs">
                <div class="tab active" id="tab-login" onclick="showTab('login')">Login</div>
                <div class="tab" id="tab-register" onclick="showTab('register')">Register</div>
            </div>
            
            <div id="error" class="error"></div>
            
            <!-- Login Form -->
            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-input" id="login-email" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" class="form-input" id="login-password" required>
                </div>
                <button type="submit" class="btn btn-primary">Login</button>
            </form>
            
            <!-- Register Form -->
            <form id="register-form" onsubmit="handleRegister(event)" style="display: none;">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-input" id="register-email" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" class="form-input" id="register-password" required minlength="8">
                </div>
                <div class="form-group">
                    <label class="form-label">Name (optional)</label>
                    <input type="text" class="form-input" id="register-name">
                </div>
                <div class="form-group">
                    <label class="form-label">Company (optional)</label>
                    <input type="text" class="form-input" id="register-company">
                </div>
                <button type="submit" class="btn btn-primary">Create Account</button>
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
            el.textContent = message;
            el.style.display = 'block';
        }
        
        async function handleLogin(event) {
            event.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            
            try {
                const response = await fetch(API_BASE + '/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Login failed');
                }
                
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                window.location.href = '/dashboard';
            } catch (e) {
                showError(e.message);
            }
        }
        
        async function handleRegister(event) {
            event.preventDefault();
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const name = document.getElementById('register-name').value;
            const company = document.getElementById('register-company').value;
            
            try {
                const response = await fetch(API_BASE + '/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, name, company })
                });
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Registration failed');
                }
                
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                window.location.href = '/dashboard';
            } catch (e) {
                showError(e.message);
            }
        }
    </script>
</body>
</html>
"""


def get_dashboard_html():
    """Return the dashboard HTML template."""
    return DASHBOARD_HTML


def get_login_html():
    """Return the login HTML template."""
    return LOGIN_HTML
