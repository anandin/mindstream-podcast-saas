"""
CastAPI Developer Portal
Podcast generation API for AI agents and developers
"""

CASTAPI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CastAPI - Podcast Generation API for Developers</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700;800&display=swap\" rel=\"stylesheet\">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #0f0f14;
            --bg-card: #16161d;
            --bg-terminal: #0d1117;
            --accent-primary: #22c55e;
            --accent-secondary: #16a34a;
            --accent-gradient: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --border-color: #27272a;
            --terminal-green: #22c55e;
            --terminal-yellow: #eab308;
            --terminal-blue: #3b82f6;
            --terminal-red: #ef4444;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .bg-grid {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image:
                linear-gradient(rgba(34, 197, 94, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(34, 197, 94, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
            z-index: 0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            position: relative;
            z-index: 1;
        }
        
        /* Header */
        header {
            padding: 20px 0;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(10, 10, 15, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
        }
        
        header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 24px;
            font-weight: 800;
        }
        
        .logo-icon {
            font-size: 28px;
        }
        
        .logo-text {
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        nav {
            display: flex;
            align-items: center;
            gap: 32px;
        }
        
        nav a {
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 14px;
            transition: color 0.2s;
        }
        
        nav a:hover {
            color: var(--text-primary);
        }
        
        .btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            border: none;
        }
        
        .btn-primary {
            background: var(--accent-gradient);
            color: white;
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
        }
        
        .btn-ghost {
            background: transparent;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .btn-ghost:hover {
            background: var(--bg-card);
            border-color: var(--text-muted);
        }
        
        .btn-large {
            padding: 16px 32px;
            font-size: 16px;
            border-radius: 12px;
        }
        
        /* Hero */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 120px 0 80px;
        }
        
        .hero-content {
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
        }
        
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 100px;
            font-size: 13px;
            color: var(--text-secondary);
            margin-bottom: 24px;
        }
        
        .hero-badge .dot {
            width: 8px;
            height: 8px;
            background: var(--accent-primary);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .hero h1 {
            font-size: clamp(40px, 8vw, 64px);
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 24px;
            letter-spacing: -0.02em;
        }
        
        .hero h1 .gradient {
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .hero p {
            font-size: 20px;
            color: var(--text-secondary);
            margin-bottom: 40px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .hero-cta {
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        /* Terminal */
        .terminal {
            background: var(--bg-terminal);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            margin: 40px auto;
            max-width: 700px;
            text-align: left;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .terminal-header {
            background: #1a1a24;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .terminal-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .terminal-dot.red { background: #ef4444; }
        .terminal-dot.yellow { background: #eab308; }
        .terminal-dot.green { background: #22c55e; }
        
        .terminal-title {
            flex: 1;
            text-align: center;
            font-size: 13px;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }
        
        .terminal-body {
            padding: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            line-height: 1.8;
        }
        
        .terminal-line {
            margin-bottom: 8px;
        }
        
        .terminal-prompt {
            color: var(--terminal-green);
        }
        
        .terminal-command {
            color: var(--text-primary);
        }
        
        .terminal-output {
            color: var(--text-secondary);
            padding-left: 20px;
        }
        
        .terminal-json {
            color: var(--terminal-blue);
        }
        
        .terminal-string {
            color: var(--terminal-yellow);
        }
        
        /* Features */
        .features {
            padding: 100px 0;
        }
        
        .section-header {
            text-align: center;
            margin-bottom: 64px;
        }
        
        .section-label {
            font-size: 13px;
            font-weight: 600;
            color: var(--accent-primary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 16px;
        }
        
        .section-title {
            font-size: clamp(32px, 5vw, 48px);
            font-weight: 800;
            margin-bottom: 16px;
        }
        
        .section-subtitle {
            font-size: 18px;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
        }
        
        .feature-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 32px;
            transition: all 0.3s;
        }
        
        .feature-card:hover {
            border-color: var(--accent-primary);
            transform: translateY(-4px);
        }
        
        .feature-icon {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin-bottom: 20px;
        }
        
        .feature-card h3 {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        
        .feature-card p {
            color: var(--text-secondary);
            font-size: 15px;
        }
        
        /* Code Examples */
        .code-examples {
            padding: 100px 0;
            background: var(--bg-secondary);
        }
        
        .code-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            justify-content: center;
        }
        
        .code-tab {
            padding: 10px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-secondary);
        }
        
        .code-tab.active {
            background: var(--accent-primary);
            color: white;
            border-color: var(--accent-primary);
        }
        
        .code-tab:hover:not(.active) {
            border-color: var(--text-muted);
            color: var(--text-primary);
        }
        
        .code-block {
            background: var(--bg-terminal);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .code-block-header {
            background: #1a1a24;
            padding: 12px 16px;
            font-size: 13px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border-color);
            font-family: 'JetBrains Mono', monospace;
        }
        
        .code-block pre {
            padding: 20px;
            margin: 0;
            overflow-x: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            line-height: 1.8;
        }
        
        .code-block code {
            color: var(--text-secondary);
        }
        
        .code-keyword { color: #c678dd; }
        .code-string { color: #98c379; }
        .code-function { color: #61afef; }
        .code-comment { color: #5c6370; font-style: italic; }
        .code-variable { color: #e5c07b; }
        .code-property { color: #d19a66; }
        
        /* Pricing */
        .pricing {
            padding: 100px 0;
        }
        
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .pricing-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 40px 32px;
            position: relative;
            transition: all 0.3s;
        }
        
        .pricing-card:hover {
            transform: translateY(-4px);
        }
        
        .pricing-card.featured {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 1px var(--accent-primary);
        }
        
        .pricing-card.featured::before {
            content: \"Best Value\";
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--accent-gradient);
            padding: 4px 16px;
            border-radius: 100px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .pricing-tier {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .pricing-price {
            display: flex;
            align-items: baseline;
            gap: 4px;
            margin-bottom: 24px;
        }
        
        .pricing-currency {
            font-size: 24px;
            font-weight: 600;
            color: var(--text-secondary);
        }
        
        .pricing-amount {
            font-size: 56px;
            font-weight: 800;
            line-height: 1;
        }
        
        .pricing-period {
            font-size: 16px;
            color: var(--text-muted);
        }
        
        .pricing-description {
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .pricing-features {
            list-style: none;
            margin-bottom: 32px;
        }
        
        .pricing-features li {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0;
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .pricing-features li::before {
            content: \"✓\";
            color: var(--accent-primary);
            font-weight: 700;
        }
        
        .pricing-card .btn {
            width: 100%;
        }
        
        /* MCP Section */
        .mcp-section {
            padding: 100px 0;
            background: var(--bg-secondary);
        }
        
        .mcp-content {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .mcp-steps {
            margin-top: 40px;
        }
        
        .mcp-step {
            display: flex;
            gap: 20px;
            margin-bottom: 32px;
        }
        
        .mcp-step-number {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--accent-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }
        
        .mcp-step-content h4 {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .mcp-step-content p {
            color: var(--text-secondary);
            font-size: 15px;
        }
        
        .mcp-code {
            background: var(--bg-terminal);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            margin-top: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }
        
        /* Sandbox */
        .sandbox {
            padding: 100px 0;
        }
        
        .sandbox-form {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        .form-label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .form-input, .form-select, .form-textarea {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-terminal);
            color: var(--text-primary);
            font-size: 14px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .form-input:focus, .form-select:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--accent-primary);
        }
        
        .form-textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        /* Footer */
        footer {
            padding: 40px 0;
            border-top: 1px solid var(--border-color);
        }
        
        footer .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        
        .footer-links {
            display: flex;
            gap: 24px;
        }
        
        .footer-links a {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 14px;
            transition: color 0.2s;
        }
        
        .footer-links a:hover {
            color: var(--text-primary);
        }
        
        .footer-copyright {
            color: var(--text-muted);
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            nav {
                display: none;
            }
            
            .pricing-grid {
                grid-template-columns: 1fr;
            }
            
            footer .container {
                flex-direction: column;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class=\"bg-grid\"></div>
    
    <header>
        <div class=\"container\">
            <div class=\"logo\">
                <span class=\"logo-icon\">🔌</span>
                <span class=\"logo-text\">CastAPI</span>
            </div>
            <nav>
                <a href=\"#features\">Features</a>
                <a href=\"#code-examples\">Examples</a>
                <a href=\"#sandbox\">Sandbox</a>
                <a href=\"#pricing\">Pricing</a>
                <a href=\"#mcp\">MCP Setup</a>
                <a href=\"/dashboard\" class=\"btn btn-ghost\">Dashboard</a>
                <a href=\"/register\" class=\"btn btn-primary\">Get API Key</a>
            </nav>
        </div>
    </header>
    
    <section class=\"hero\">
        <div class=\"container\">
            <div class=\"hero-content\">
                <div class=\"hero-badge\">
                    <span class=\"dot\"></span>
                    API is live and ready to use
                </div>
                <h1>
                    Podcast generation API<br>
                    <span class=\"gradient\">for AI agents and developers</span>
                </h1>
                <p>
                    CastAPI gives your AI agents the ability to generate, synthesize, 
                    and publish audio content — in production. REST API + MCP Server included.
                </p>
                <div class=\"hero-cta\">
                    <a href=\"/register\" class=\"btn btn-primary btn-large\">Get API Key →</a>
                    <a href=\"#sandbox\" class=\"btn btn-ghost btn-large\">Try Sandbox</a>
                </div>
                
                <div class=\"terminal\">
                    <div class=\"terminal-header\">
                        <span class=\"terminal-dot red\"></span>
                        <span class=\"terminal-dot yellow\"></span>
                        <span class=\"terminal-dot green\"></span>
                        <span class=\"terminal-title\">bash — castapi</span>
                    </div>
                    <div class=\"terminal-body\">
                        <div class=\"terminal-line\">
                            <span class=\"terminal-prompt\">$</span>
                            <span class=\"terminal-command\"> curl -X POST https://api.castapi.dev/v1/generate \</span>
                        </div>
                        <div class=\"terminal-line\">
                            <span class=\"terminal-command\">   -H \"Authorization: Bearer YOUR_API_KEY\" \</span>
                        </div>
                        <div class=\"terminal-line\">
                            <span class=\"terminal-command\">   -H \"Content-Type: application/json\" \</span>
                        </div>
                        <div class=\"terminal-line\">
                            <span class=\"terminal-command\">   -d '{</span>
                        </div>
                        <div class=\"terminal-line\">
                            <span class=\"terminal-output\"><span class=\"terminal-string\">\"url\"</span>: <span class=\"terminal-string\">\"https://techcrunch.com/feed/\"</span>,</span>
                        </div>
                        <div class=\"terminal-line\">
                            <span class=\"terminal-output\"><span class=\"terminal-string\">\"host_1\"</span>: <span class=\"terminal-string\">\"drew\"</span>,</span>
                        </div>
                        <div class=\"terminal-line\">
                            <span class=\"terminal-output\"><span class=\"terminal-string\">\"host_2\"</span>: <span class=\"terminal-string\">\"jessie\"</span></span>
                        </div>
                        <div class=\"terminal-line\">
                            <span class=\"terminal-command\">   }'</span>
                        </div>
                        <br>
                        <div class=\"terminal-line terminal-output\">
                            {<br>
                            &nbsp;&nbsp;<span class=\"terminal-string\">\"status\"</span>: <span class=\"terminal-string\">\"ready\"</span>,<br>
                            &nbsp;&nbsp;<span class=\"terminal-string\">\"audio_url\"</span>: <span class=\"terminal-string\">\"https://cdn.castapi.dev/abc123.mp3\"</span>,<br>
                            &nbsp;&nbsp;<span class=\"terminal-string\">\"script\"</span>: <span class=\"terminal-string\">\"...\"</span>,<br>
                            &nbsp;&nbsp;<span class=\"terminal-string\">\"duration_seconds\"</span>: <span class=\"terminal-json\">287</span><br>
                            }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"features\" id=\"features\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">Features</div>
                <h2 class=\"section-title\">Built for developers</h2>
                <p class=\"section-subtitle\">
                    Production-ready API with all the features you need for podcast generation at scale.
                </p>
            </div>
            
            <div class=\"features-grid\">
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">⚡</div>
                    <h3>REST API</h3>
                    <p>Full REST API with OpenAPI documentation. Generate podcasts with a simple POST request and get structured JSON responses.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">🔗</div>
                    <h3>MCP Server</h3>
                    <p>Direct integration with Claude Desktop and other MCP-compatible AI agents. No HTTP calls needed — it's just there.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">📊</div>
                    <h3>Usage Analytics</h3>
                    <p>Real-time usage tracking with detailed metrics. Rate limit headers so you can throttle your own requests.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">🌐</div>
                    <h3>Webhooks</h3>
                    <p>Get notified when generation completes via webhook. Perfect for async workflows and agent loops.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">🎭</div>
                    <h3>Multi-Voice</h3>
                    <p>Choose from Voxtral (Mistral), 11Labs, or MiniMax voices. Different providers for different cost/quality needs.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">📦</div>
                    <h3>Batch Processing</h3>
                    <p>Process multiple content sources at once with our batch endpoint. Scale your content pipeline effortlessly.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"code-examples\" id=\"code-examples\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">Code Examples</div>
                <h2 class=\"section-title\">Integrate in minutes</h2>
                <p class=\"section-subtitle\">
                    Full code examples in Python, JavaScript, and curl.
                </p>
            </div>
            
            <div class=\"code-tabs\">
                <button class=\"code-tab active\" onclick=\"showCode('python')\">Python</button>
                <button class=\"code-tab\" onclick=\"showCode('javascript')\">JavaScript</button>
                <button class=\"code-tab\" onclick=\"showCode('curl')\">curl</button>
            </div>
            
            <div class=\"code-block\" id=\"code-python\">
                <div class=\"code-block-header\">generate_podcast.py</div>
                <pre><code><span class=\"code-keyword\">import</span> requests

<span class=\"code-comment\"># Initialize client</span>
api_key = <span class=\"code-string\">\"your_api_key_here\"</span>
base_url = <span class=\"code-string\">\"https://api.castapi.dev/v1\"</span>

<span class=\"code-comment\"># Generate podcast from URL</span>
response = requests.post(
    <span class=\"code-string\">f\"{base_url}/generate\"</span>,
    headers={
        <span class=\"code-string\">\"Authorization\"</span>: <span class=\"code-string\">f\"Bearer {api_key}\"</span>,
        <span class=\"code-string\">\"Content-Type\"</span>: <span class=\"code-string\">\"application/json\"</span>
    },
    json={
        <span class=\"code-string\">\"url\"</span>: <span class=\"code-string\">\"https://techcrunch.com/feed/\"</span>,
        <span class=\"code-string\">\"host_1\"</span>: <span class=\"code-string\">\"drew\"</span>,
        <span class=\"code-string\">\"host_2\"</span>: <span class=\"code-string\">\"jessie\"</span>,
        <span class=\"code-string\">\"provider\"</span>: <span class=\"code-string\">\"voxtral\"</span>
    }
)

<span class=\"code-keyword\">if</span> response.status_code == <span class=\"code-number\">200</span>:
    result = response.json()
    <span class=\"code-function\">print</span>(<span class=\"code-string\">f\"Audio ready: {result['audio_url']}\"</span>)
    <span class=\"code-function\">print</span>(<span class=\"code-string\">f\"Duration: {result['duration_seconds']}s\"</span>)
<span class=\"code-keyword\">else</span>:
    <span class=\"code-function\">print</span>(<span class=\"code-string\">f\"Error: {response.text}\"</span>)</code></pre>
            </div>
            
            <div class=\"code-block\" id=\"code-javascript\" style=\"display: none;\">
                <div class=\"code-block-header\">generate_podcast.js</div>
                <pre><code><span class=\"code-keyword\">const</span> response = <span class=\"code-keyword\">await</span> fetch(<span class=\"code-string\">'https://api.castapi.dev/v1/generate'</span>, {
    method: <span class=\"code-string\">'POST'</span>,
    headers: {
        <span class=\"code-string\">'Authorization'</span>: <span class=\"code-string\">'Bearer YOUR_API_KEY'</span>,
        <span class=\"code-string\">'Content-Type'</span>: <span class=\"code-string\">'application/json'</span>
    },
    body: JSON.stringify({
        url: <span class=\"code-string\">'https://techcrunch.com/feed/'</span>,
        host_1: <span class=\"code-string\">'drew'</span>,
        host_2: <span class=\"code-string\">'jessie'</span>,
        provider: <span class=\"code-string\">'voxtral'</span>
    })
});

<span class=\"code-keyword\">const</span> result = <span class=\"code-keyword\">await</span> response.json();
console.<span class=\"code-function\">log</span>(<span class=\"code-string\">`Audio ready: ${result.audio_url}`</span>);
console.<span class=\"code-function\">log</span>(<span class=\"code-string\">`Duration: ${result.duration_seconds}s`</span>);</code></pre>
            </div>
            
            <div class=\"code-block\" id=\"code-curl\" style=\"display: none;\">
                <div class=\"code-block-header\">terminal</div>
                <pre><code><span class=\"code-comment\"># Generate podcast from URL</span>
curl -X POST https://api.castapi.dev/v1/generate \\
    -H <span class=\"code-string\">\"Authorization: Bearer YOUR_API_KEY\"</span> \\
    -H <span class=\"code-string\">\"Content-Type: application/json\"</span> \\
    -d <span class=\"code-string\">'{
        \"url\": \"https://techcrunch.com/feed/\",
        \"host_1\": \"drew\",
        \"host_2\": \"jessie\",
        \"provider\": \"voxtral\"
    }'</span>

<span class=\"code-comment\"># Response</span>
{
    <span class=\"code-string\">\"id\"</span>: <span class=\"code-string\">\"ep_abc123\"</span>,
    <span class=\"code-string\">\"status\"</span>: <span class=\"code-string\">\"ready\"</span>,
    <span class=\"code-string\">\"audio_url\"</span>: <span class=\"code-string\">\"https://cdn.castapi.dev/abc123.mp3\"</span>,
    <span class=\"code-string\">\"script\"</span>: <span class=\"code-string\">\"Welcome to today's episode...\"</span>,
    <span class=\"code-string\">\"duration_seconds\"</span>: <span class=\"code-number\">287</span>,
    <span class=\"code-string\">\"created_at\"</span>: <span class=\"code-string\">\"2026-03-27T10:30:00Z\"</span>
}</code></pre>
            </div>
        </div>
    </section>
    
    <section class=\"sandbox\" id=\"sandbox\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">API Sandbox</div>
                <h2 class=\"section-title\">Try it out</h2>
                <p class=\"section-subtitle\">
                    Test the API directly from your browser. Enter your API key or use the demo key.
                </p>
            </div>
            
            <div class=\"sandbox-form\">
                <div class=\"form-group\">
                    <label class=\"form-label\">API Key</label>
                    <input type=\"text\" class=\"form-input\" id=\"sandbox-api-key\" placeholder=\"sk_live_...\" value=\"sk_demo_key\">
                </div>
                
                <div class=\"form-group\">
                    <label class=\"form-label\">Content URL or Text</label>
                    <textarea class=\"form-textarea\" id=\"sandbox-content\" placeholder=\"Enter a URL (RSS feed or article) or paste text content here...\">
https://techcrunch.com/feed/</textarea>
                </div>
                
                <div class=\"form-group\">
                    <label class=\"form-label\">Voice Provider</label>
                    <select class=\"form-select\" id=\"sandbox-provider\">
                        <option value=\"voxtral\">Voxtral (Mistral) - High Quality</option>
                        <option value=\"11labs\">11Labs - Premium Quality</option>
                        <option value=\"minimax\">MiniMax - Budget</option>
                    </select>
                </div>
                
                <div class=\"grid\" style=\"display: grid; grid-template-columns: 1fr 1fr; gap: 16px;\">
                    <div class=\"form-group\">
                        <label class=\"form-label\">Host 1 Voice</label>
                        <select class=\"form-select\" id=\"sandbox-host-1\">
                            <option value=\"drew\">Drew (Male - Calm)</option>
                            <option value=\"bob\">Bob (Male - Deep)</option>
                            <option value=\"jessie\">Jessie (Female - Friendly)</option>
                            <option value=\"alice\">Alice (Female - Warm)</option>
                        </select>
                    </div>
                    <div class=\"form-group\">
                        <label class=\"form-label\">Host 2 Voice</label>
                        <select class=\"form-select\" id=\"sandbox-host-2\">
                            <option value=\"jessie\">Jessie (Female - Friendly)</option>
                            <option value=\"alice\">Alice (Female - Warm)</option>
                            <option value=\"drew\">Drew (Male - Calm)</option>
                            <option value=\"bob\">Bob (Male - Deep)</option>
                        </select>
                    </div>
                </div>
                
                <button class=\"btn btn-primary btn-large\" style=\"width: 100%;\" onclick=\"testApi()\">
                    🚀 Test API
                </button>
                
                <div id=\"sandbox-result\" style=\"margin-top: 24px; display: none;\">
                    <label class=\"form-label\">Response</label>
                    <pre id=\"sandbox-response\" style=\"background: var(--bg-terminal); padding: 16px; border-radius: 8px; overflow-x: auto; font-family: 'JetBrains Mono', monospace; font-size: 13px;\"></pre>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"pricing\" id=\"pricing\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">Pricing</div>
                <h2 class=\"section-title\">Simple, volume-based pricing</h2>
                <p class=\"section-subtitle\">
                    Start free, scale as you grow. No hidden fees.
                </p>
            </div>
            
            <div class=\"pricing-grid\">
                <div class=\"pricing-card\">
                    <div class=\"pricing-tier\">Dev</div>
                    <div class=\"pricing-price\">
                        <span class=\"pricing-amount\">$0</span>
                        <span class=\"pricing-period\">/month</span>
                    </div>
                    <p class=\"pricing-description\">Perfect for development and testing. Limited calls but full API access.</p>
                    <ul class=\"pricing-features\">
                        <li>100 API calls / month</li>
                        <li>All endpoints</li>
                        <li>Voxtral voice only</li>
                        <li>Watermark on audio</li>
                        <li>Community support</li>
                    </ul>
                    <a href=\"/register\" class=\"btn btn-ghost\">Get Started</a>
                </div>
                
                <div class=\"pricing-card featured\">
                    <div class=\"pricing-tier\">Growth</div>
                    <div class=\"pricing-price\">
                        <span class=\"pricing-currency\">$</span>
                        <span class=\"pricing-amount\">49</span>
                        <span class=\"pricing-period\">/month</span>
                    </div>
                    <p class=\"pricing-description\">For growing applications and production workloads.</p>
                    <ul class=\"pricing-features\">
                        <li>2,000 API calls / month</li>
                        <li>All endpoints</li>
                        <li>All voice providers</li>
                        <li>No watermark</li>
                        <li>Webhook support</li>
                        <li>Priority email support</li>
                    </ul>
                    <a href=\"/register\" class=\"btn btn-primary\">Start Trial</a>
                </div>
                
                <div class=\"pricing-card\">
                    <div class=\"pricing-tier\">Scale</div>
                    <div class=\"pricing-price\">
                        <span class=\"pricing-currency\">$</span>
                        <span class=\"pricing-amount\">199</span>
                        <span class=\"pricing-period\">/month</span>
                    </div>
                    <p class=\"pricing-description\">For high-volume production and enterprise needs.</p>
                    <ul class=\"pricing-features\">
                        <li>10,000 API calls / month</li>
                        <li>All endpoints</li>
                        <li>All voice providers</li>
                        <li>No watermark</li>
                        <li>Webhook + Batch API</li>
                        <li>Dedicated Slack support</li>
                    </ul>
                    <a href=\"/register\" class=\"btn btn-ghost\">Contact Sales</a>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"mcp-section\" id=\"mcp\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">MCP Server</div>
                <h2 class=\"section-title\">Setup in Claude Desktop</h2>
                <p class=\"section-subtitle\">
                    Add CastAPI as an MCP server for direct podcast generation in your AI conversations.
                </p>
            </div>
            
            <div class=\"mcp-content\">
                <div class=\"mcp-steps\">
                    <div class=\"mcp-step\">
                        <div class=\"mcp-step-number\">1</div>
                        <div class=\"mcp-step-content\">
                            <h4>Install the MCP Server</h4>
                            <p>Add the CastAPI MCP server to your Claude Desktop configuration.</p>
                            <div class=\"mcp-code\">
{
  "mcpServers": {
    "castapi": {
      "command": "npx",
      "args": ["-y", "@castapi/mcp-server"]
    }
  }
}
                            </div>
                        </div>
                    </div>
                    
                    <div class=\"mcp-step\">
                        <div class=\"mcp-step-number\">2</div>
                        <div class=\"mcp-step-content\">
                            <h4>Set Your API Key</h4>
                            <p>Set the CASTAPI_API_KEY environment variable with your API key.</p>
                            <div class=\"mcp-code\">
CASTAPI_API_KEY=sk_live_your_key_here
                            </div>
                        </div>
                    </div>
                    
                    <div class=\"mcp-step\">
                        <div class=\"mcp-step-number\">3</div>
                        <div class=\"mcp-step-content\">
                            <h4>Start Using</h4>
                            <p>Claude can now generate podcasts directly. Just ask!</p>
                            <div class=\"mcp-code\">
<span style=\"color: var(--text-muted);\">// In Claude Desktop:</span>
<span style=\"color: var(--text-secondary);\">\"Generate a podcast from this RSS feed: 
https://news.ycombinator.com/rss\"</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"cta-section\" style=\"padding: 100px 0; text-align: center;\">
        <div class=\"container\">
            <h2 style=\"font-size: clamp(32px, 5vw, 48px); font-weight: 800; margin-bottom: 16px;\">
                Ready to build?
            </h2>
            <p style=\"color: var(--text-secondary); font-size: 18px; margin-bottom: 32px;\">
                Get your API key and start generating podcasts in minutes.
            </p>
            <a href=\"/register\" class=\"btn btn-primary btn-large\">Get API Key →</a>
        </div>
    </section>
    
    <footer>
        <div class=\"container\">
            <div class=\"logo\">
                <span class=\"logo-icon\">🔌</span>
                <span class=\"logo-text\">CastAPI</span>
            </div>
            <div class=\"footer-links\">
                <a href=\"#features\">Features</a>
                <a href=\"#pricing\">Pricing</a>
                <a href=\"/docs\">API Docs</a>
                <a href=\"/dashboard\">Dashboard</a>
            </div>
            <div class=\"footer-copyright\">
                © 2026 CastAPI. Podcast generation for developers.
            </div>
        </div>
    </footer>
    
    <script>
        function showCode(lang) {
            document.querySelectorAll('.code-block').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.code-tab').forEach(el => el.classList.remove('active'));
            document.getElementById('code-' + lang).style.display = 'block';
            event.target.classList.add('active');
        }
        
        function testApi() {
            const resultDiv = document.getElementById('sandbox-result');
            const responseDiv = document.getElementById('sandbox-response');
            
            resultDiv.style.display = 'block';
            responseDiv.innerHTML = '<span style=\"color: var(--text-muted);\">Sending request...</span>';
            
            setTimeout(() => {
                responseDiv.innerHTML = '<span style=\"color: var(--terminal-yellow);\">Note: This is a demo. In production, this would call the actual API.</span>\\n\\n<span style=\"color: var(--text-secondary);\">To test with real API:\\n1. Get an API key from /register\\n2. Replace the demo key above\\n3. Enter your content URL\\n4. Click Test API again</span>';
            }, 1000);
        }
        
        // Smooth scroll
        document.querySelectorAll('a[href^=\"#\"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    </script>
</body>
</html>
"""


def get_castapi_html():
    """Return the CastAPI developer portal HTML."""
    return CASTAPI_HTML
