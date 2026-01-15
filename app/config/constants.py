"""
Constants and configuration values for the web scraper.
"""

# Common viewport sizes (realistic distribution)
COMMON_VIEWPORTS = [
    {"width": 1920, "height": 1080},  # Most common
    {"width": 1366, "height": 768},   # Laptops
    {"width": 1536, "height": 864},   # Scaled displays
    {"width": 1440, "height": 900},   # MacBooks
    {"width": 1280, "height": 720},   # HD
    {"width": 2560, "height": 1440},  # QHD monitors
    {"width": 1680, "height": 1050},  # Older monitors
]

# CAPTCHA detection phrases
CAPTCHA_PHRASES = [
    "press & hold", "verify you are human", "prove you're not a robot",
    "human (and not a bot)", "reference id", "confirm you are",
    "security check", "complete the captcha", "are you a robot"
]

# Access denied title indicators
ACCESS_DENIED_INDICATORS = [
    "access denied", "403 forbidden", "blocked", "you have been blocked",
    "has been denied", "page denied", "not available", "unavailable"
]

# Popup/cookie consent selectors
POPUP_SELECTORS = [
    # Standard cookie consent
    "button:has-text('Accept')",
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "button:has-text('Accept cookies')",
    "button:has-text('Accept Cookies')",
    "button:has-text('I Accept')",
    "button:has-text('I agree')",
    "button:has-text('I Agree')",
    "button:has-text('Agree')",
    "button:has-text('Got it')",
    "button:has-text('OK')",
    "button:has-text('Continue')",
    "button:has-text('Close')",
    "button:has-text('Dismiss')",
    "[class*='accept']",
    "[class*='consent']",
    "[id*='accept']",
    "[id*='consent']",
    "[aria-label*='accept']",
    "[aria-label*='Accept']",
    "[aria-label*='close']",
    "[aria-label*='dismiss']",
    # Modal close buttons
    ".modal-close",
    ".popup-close",
    ".close-button",
    "[class*='modal'] button[class*='close']",
    "[class*='popup'] button[class*='close']",
    # GDPR specific
    "#gdpr-accept",
    "#cookie-accept",
    ".gdpr-accept",
    ".cookie-accept",
    # Newsletter/subscription popups
    "button[class*='newsletter'] [class*='close']",
    "[class*='subscribe'] button[class*='close']",
    "[class*='signup'] button[class*='close']",
]

# Canvas fingerprint noise injection script
CANVAS_NOISE_SCRIPT = """
(function() {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (type === 'image/png' && this.width > 0 && this.height > 0) {
            try {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = originalGetImageData.call(context, 0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + (Math.random() * 2 - 1)));
                        imageData.data[i + 1] = Math.max(0, Math.min(255, imageData.data[i + 1] + (Math.random() * 2 - 1)));
                        imageData.data[i + 2] = Math.max(0, Math.min(255, imageData.data[i + 2] + (Math.random() * 2 - 1)));
                    }
                    context.putImageData(imageData, 0, 0);
                }
            } catch(e) {}
        }
        return originalToDataURL.apply(this, arguments);
    };
})();
"""

# WebGL fingerprint spoofing script
WEBGL_SPOOF_SCRIPT = """
(function() {
    const renderers = [
        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)',
    ];
    const vendors = ['Google Inc. (NVIDIA)', 'Google Inc. (Intel)', 'Google Inc. (AMD)'];

    const selectedRenderer = renderers[Math.floor(Math.random() * renderers.length)];
    const selectedVendor = vendors[Math.floor(Math.random() * vendors.length)];

    ['WebGLRenderingContext', 'WebGL2RenderingContext'].forEach(function(ctx) {
        if (window[ctx] && window[ctx].prototype.getParameter) {
            const original = window[ctx].prototype.getParameter;
            window[ctx].prototype.getParameter = function(param) {
                if (param === 37445) return selectedVendor;
                if (param === 37446) return selectedRenderer;
                return original.call(this, param);
            };
        }
    });
})();
"""

# Browser patches script
BROWSER_PATCHES_SCRIPT = """
(function() {
    const cores = [4, 6, 8, 12, 16][Math.floor(Math.random() * 5)];
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => cores });

    const memory = [4, 8, 16, 32][Math.floor(Math.random() * 4)];
    Object.defineProperty(navigator, 'deviceMemory', { get: () => memory });

    Object.defineProperty(navigator, 'plugins', {
        get: () => ({
            length: 5,
            item: (i) => null,
            namedItem: (name) => null,
            refresh: () => {}
        })
    });

    if (typeof RTCPeerConnection !== 'undefined') {
        const originalRTCPeerConnection = window.RTCPeerConnection;
        window.RTCPeerConnection = function(...args) {
            const config = args[0] || {};
            config.iceServers = [];
            return new originalRTCPeerConnection(config);
        };
        window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
    }

    if (navigator.connection) {
        const connectionTypes = ['wifi', '4g', 'ethernet'];
        Object.defineProperty(navigator.connection, 'type', {
            get: () => connectionTypes[Math.floor(Math.random() * connectionTypes.length)]
        });
        Object.defineProperty(navigator.connection, 'downlink', {
            get: () => Math.floor(Math.random() * 10) + 1
        });
    }

    if (navigator.getBattery) {
        navigator.getBattery = () => Promise.resolve({
            charging: Math.random() > 0.3,
            chargingTime: Math.floor(Math.random() * 3600),
            dischargingTime: Math.floor(Math.random() * 10800) + 3600,
            level: Math.random() * 0.5 + 0.5
        });
    }
})();
"""

# Referrer sources for realistic traffic patterns
REFERRER_SOURCES = [
    "https://www.google.com/",
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://duckduckgo.com/?q=",
    "https://www.facebook.com/",
    "https://twitter.com/",
    "https://www.linkedin.com/",
    "https://www.reddit.com/",
    "https://news.ycombinator.com/",
]

# Default configuration values
DEFAULT_CONFIG = {
    "browser": {
        "headless": True,
        "slow_mo": 50,
        "timeout": 30000
    },
    "retry": {
        "max_attempts": 3,
        "min_wait": 1,
        "max_wait": 5
    },
    "rate_limiting": {
        "max_requests_per_domain_per_hour": 60,
        "min_delay_between_requests": 2,
        "max_delay_between_requests": 8
    },
    "human_behavior": {
        "mouse_movements": {"min": 2, "max": 3},
        "scroll_actions": {"min": 2, "max": 3}
    }
}
