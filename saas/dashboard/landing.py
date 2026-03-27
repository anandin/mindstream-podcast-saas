"""
Mind Stream Landing Page
AI-Powered Podcast Generation Platform
"""

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mind Stream - AI-Powered Podcast Generation</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap\" rel=\"stylesheet\">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --border-color: #27272a;
            --success: #22c55e;
            --warning: #f59e0b;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        /* Background Effects */
        .bg-gradient {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background:
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.15), transparent),
                radial-gradient(ellipse 60% 40% at 90% 60%, rgba(139, 92, 246, 0.1), transparent),
                radial-gradient(ellipse 50% 30% at 10% 80%, rgba(217, 70, 239, 0.08), transparent);
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
            background: rgba(10, 10, 15, 0.8);
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
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .logo-icon {
            font-size: 28px;
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
        
        .nav-cta {
            display: flex;
            gap: 12px;
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
        
        .btn-ghost {
            background: transparent;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .btn-ghost:hover {
            background: var(--bg-card);
            border-color: var(--text-muted);
        }
        
        .btn-primary {
            background: var(--accent-gradient);
            color: white;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }
        
        .btn-large {
            padding: 16px 32px;
            font-size: 16px;
            border-radius: 12px;
        }
        
        /* Hero Section */
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
        
        .hero-badge span {
            color: var(--accent-primary);
        }
        
        .hero h1 {
            font-size: clamp(40px, 8vw, 72px);
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
        
        .hero-stats {
            display: flex;
            justify-content: center;
            gap: 48px;
            margin-top: 80px;
            padding-top: 40px;
            border-top: 1px solid var(--border-color);
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            font-size: 14px;
            color: var(--text-muted);
            margin-top: 4px;
        }
        
        /* Features Section */
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
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .feature-icon {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            background: var(--accent-gradient);
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
        
        /* How It Works */
        .how-it-works {
            padding: 100px 0;
            background: var(--bg-secondary);
        }
        
        .steps {
            display: flex;
            flex-direction: column;
            gap: 48px;
            max-width: 700px;
            margin: 0 auto;
        }
        
        .step {
            display: flex;
            gap: 24px;
            align-items: flex-start;
        }
        
        .step-number {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--accent-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
            flex-shrink: 0;
        }
        
        .step-content h3 {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .step-content p {
            color: var(--text-secondary);
        }
        
        /* Pricing Section */
        .pricing {
            padding: 100px 0;
        }
        
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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
            content: \"Most Popular\";
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
            color: var(--success);
            font-weight: 700;
        }
        
        .pricing-features li.disabled {
            color: var(--text-muted);
            text-decoration: line-through;
        }
        
        .pricing-features li.disabled::before {
            content: \"×\";
            color: var(--text-muted);
        }
        
        .pricing-card .btn {
            width: 100%;
        }
        
        /* CTA Section */
        .cta-section {
            padding: 100px 0;
            text-align: center;
        }
        
        .cta-section h2 {
            font-size: clamp(32px, 5vw, 48px);
            font-weight: 800;
            margin-bottom: 16px;
        }
        
        .cta-section p {
            color: var(--text-secondary);
            font-size: 18px;
            margin-bottom: 32px;
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
        
        /* Wave Animation */
        .wave {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 200px;
            overflow: hidden;
        }
        
        .wave svg {
            position: absolute;
            bottom: 0;
        }
        
        /* Animations */
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .animate-float {
            animation: float 3s ease-in-out infinite;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            nav {
                display: none;
            }
            
            .hero-stats {
                flex-direction: column;
                gap: 24px;
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
    <div class=\"bg-gradient\"></div>
    
    <header>
        <div class=\"container\">
            <div class=\"logo\">
                <span class=\"logo-icon\">🎙️</span>
                <span>Mind Stream</span>
            </div>
            <nav>
                <a href=\"#features\">Features</a>
                <a href=\"#how-it-works\">How It Works</a>
                <a href=\"#pricing\">Pricing</a>
                <div class=\"nav-cta\">
                    <a href=\"/login\" class=\"btn btn-ghost\">Sign In</a>
                    <a href=\"/register\" class=\"btn btn-primary\">Start Free</a>
                </div>
            </nav>
        </div>
    </header>
    
    <section class=\"hero\">
        <div class=\"container\">
            <div class=\"hero-content\">
                <div class=\"hero-badge\">
                    🚀 Introducing AI-Powered Multi-Host Synthesis
                </div>
                <h1>
                    AI-Powered Podcast Generation<br>
                    <span class=\"gradient\">Your ideas, broadcast to the world</span>
                </h1>
                <p>
                    Transform your content into professional podcasts instantly. 
                    Auto-script writing, multi-voice synthesis, and one-click publishing — 
                    all powered by AI.
                </p>
                <div class=\"hero-cta\">
                    <a href=\"/register\" class=\"btn btn-primary btn-large\">Start for free →</a>
                    <a href=\"/dashboard\" class=\"btn btn-ghost btn-large\">View Demo</a>
                </div>
                
                <div class=\"hero-stats\">
                    <div class=\"stat\">
                        <div class=\"stat-value\">50K+</div>
                        <div class=\"stat-label\">Podcasts Generated</div>
                    </div>
                    <div class=\"stat\">
                        <div class=\"stat-value\">3</div>
                        <div class=\"stat-label\">AI Voice Providers</div>
                    </div>
                    <div class=\"stat\">
                        <div class=\"stat-value\">4.9★</div>
                        <div class=\"stat-label\">User Rating</div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"features\" id=\"features\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">Features</div>
                <h2 class=\"section-title\">Everything you need to podcast at scale</h2>
                <p class=\"section-subtitle\">
                    From script to publish in minutes, not hours. Our AI handles the heavy lifting.
                </p>
            </div>
            
            <div class=\"features-grid\">
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">✍️</div>
                    <h3>Auto-Script Writing</h3>
                    <p>Input a topic, URL, or document — our AI generates a well-structured, engaging podcast script with natural dialogue between hosts.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">🎭</div>
                    <h3>Multi-Voice Synthesis</h3>
                    <p>Choose from 11Labs (premium), Voxtral (high quality), or MiniMax (budget) — each with multiple voice profiles for host 1 and host 2.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">🚀</div>
                    <h3>One-Click Publish</h3>
                    <p>Generate your podcast and publish directly to Spotify, Apple Podcasts, and more — or get an RSS feed for your own platform.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">🌍</div>
                    <h3>Multi-Language Support</h3>
                    <p>Generate podcasts in English, Spanish, French, German, and more — with native-sounding voices for each language.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">⚡</div>
                    <h3>Lightning Fast</h3>
                    <p>From script to published audio in under 5 minutes. Our optimized pipeline delivers broadcast-ready content at scale.</p>
                </div>
                
                <div class=\"feature-card\">
                    <div class=\"feature-icon\">🔌</div>
                    <h3>Developer API</h3>
                    <p>Integrate podcast generation into your AI agents and workflows with our REST API. MCP server available for Claude Desktop.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"how-it-works\" id=\"how-it-works\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">How It Works</div>
                <h2 class=\"section-title\">Three steps to podcast glory</h2>
            </div>
            
            <div class=\"steps\">
                <div class=\"step\">
                    <div class=\"step-number\">1</div>
                    <div class=\"step-content\">
                        <h3>Create Your Podcast</h3>
                        <p>Set up your podcast with custom host names, voices, and preferences. Choose your AI voice provider based on quality and budget needs.</p>
                    </div>
                </div>
                
                <div class=\"step\">
                    <div class=\"step-number\">2</div>
                    <div class=\"step-content\">
                        <h3>Add Your Content</h3>
                        <p>Input URLs, paste text, or add RSS feeds. Our AI extracts the key insights and transforms them into an engaging dialogue.</p>
                    </div>
                </div>
                
                <div class=\"step\">
                    <div class=\"step-number\">3</div>
                    <div class=\"step-content\">
                        <h3>Generate & Publish</h3>
                        <p>Click generate and watch the magic happen. Your podcast is synthesized and ready to publish — or automatically posted to your channels.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"pricing\" id=\"pricing\">
        <div class=\"container\">
            <div class=\"section-header\">
                <div class=\"section-label\">Pricing</div>
                <h2 class=\"section-title\">Simple, transparent pricing</h2>
                <p class=\"section-subtitle\">
                    Start free, upgrade when you need more. All plans include access to our AI podcast generation pipeline.
                </p>
            </div>
            
            <div class=\"pricing-grid\">
                <div class=\"pricing-card\">
                    <div class=\"pricing-tier\">Free</div>
                    <div class=\"pricing-price\">
                        <span class=\"pricing-amount\">$0</span>
                        <span class=\"pricing-period\">/month</span>
                    </div>
                    <p class=\"pricing-description\">Perfect for trying out Mind Stream and generating occasional podcasts.</p>
                    <ul class=\"pricing-features\">
                        <li>3 episodes per month</li>
                        <li>100 API calls per month</li>
                        <li>100 MB storage</li>
                        <li>1 podcast show</li>
                        <li>MiniMax voice (standard)</li>
                        <li class=\"disabled\">Custom voice cloning</li>
                        <li class=\"disabled\">Priority generation</li>
                        <li class=\"disabled\">API access</li>
                    </ul>
                    <a href=\"/register\" class=\"btn btn-ghost\">Get Started</a>
                </div>
                
                <div class=\"pricing-card featured\">
                    <div class=\"pricing-tier\">Pro</div>
                    <div class=\"pricing-price\">
                        <span class=\"pricing-currency\">$</span>
                        <span class=\"pricing-amount\">29</span>
                        <span class=\"pricing-period\">/month</span>
                    </div>
                    <p class=\"pricing-description\">For creators and professionals who need reliable, high-quality podcast generation.</p>
                    <ul class=\"pricing-features\">
                        <li>Unlimited episodes</li>
                        <li>2,000 API calls per month</li>
                        <li>5 GB storage</li>
                        <li>5 podcast shows</li>
                        <li>11Labs voice (premium)</li>
                        <li>Custom voice cloning</li>
                        <li>Priority generation</li>
                        <li>API access</li>
                    </ul>
                    <a href=\"/register\" class=\"btn btn-primary\">Start Pro Trial</a>
                </div>
                
                <div class=\"pricing-card\">
                    <div class=\"pricing-tier\">Studio</div>
                    <div class=\"pricing-price\">
                        <span class=\"pricing-currency\">$</span>
                        <span class=\"pricing-amount\">79</span>
                        <span class=\"pricing-period\">/month</span>
                    </div>
                    <p class=\"pricing-description\">For teams and publishers who need maximum scale and customization.</p>
                    <ul class=\"pricing-features\">
                        <li>Unlimited everything</li>
                        <li>Unlimited API calls</li>
                        <li>50 GB storage</li>
                        <li>Unlimited podcast shows</li>
                        <li>All voice providers</li>
                        <li>Custom voice cloning</li>
                        <li>Priority + bulk generation</li>
                        <li>Team collaboration</li>
                    </ul>
                    <a href=\"/register\" class=\"btn btn-ghost\">Contact Sales</a>
                </div>
            </div>
        </div>
    </section>
    
    <section class=\"cta-section\">
        <div class=\"container\">
            <h2>Ready to broadcast your ideas?</h2>
            <p>Join thousands of creators already using Mind Stream to reach their audience.</p>
            <a href=\"/register\" class=\"btn btn-primary btn-large\">Start for free →</a>
        </div>
    </section>
    
    <footer>
        <div class=\"container\">
            <div class=\"logo\">
                <span class=\"logo-icon\">🎙️</span>
                <span>Mind Stream</span>
            </div>
            <div class=\"footer-links\">
                <a href=\"#features\">Features</a>
                <a href=\"#pricing\">Pricing</a>
                <a href=\"/docs\">API Docs</a>
                <a href=\"/dashboard\">Dashboard</a>
            </div>
            <div class=\"footer-copyright\">
                © 2026 Mind Stream. AI-Powered Podcast Generation.
            </div>
        </div>
    </footer>
    
    <script>
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^=\"#\"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
        
        // Check if user is logged in
        const token = localStorage.getItem('access_token');
        if (token) {
            // If logged in, update CTA buttons
            document.querySelectorAll('.hero-cta .btn-primary').forEach(btn => {
                btn.textContent = 'Go to Dashboard →';
                btn.href = '/dashboard';
            });
        }
    </script>
</body>
</html>
"""


def get_landing_html():
    """Return the landing page HTML."""
    return LANDING_HTML
