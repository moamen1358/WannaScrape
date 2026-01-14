"""
Advanced Anti-Detection Module
==============================
Additional anti-detection techniques to make the scraper "unstoppable":
1. Audio fingerprint spoofing
2. Font enumeration spoofing  
3. Speech synthesis spoofing
4. Permissions API spoofing
5. ClientRects noise injection
6. Date/Time precision reduction
7. Keyboard/Mouse event noise
8. Performance API noise
"""

import random
import logging

logger = logging.getLogger("anti_detection")

# ============================================================================
# AUDIO FINGERPRINT SPOOFING
# ============================================================================

AUDIO_FINGERPRINT_SCRIPT = """
(function() {
    // Spoof AudioContext fingerprinting
    const audioContextProto = AudioContext.prototype;
    const offlineContextProto = OfflineAudioContext.prototype;
    
    // Add noise to audio channel data
    const originalGetChannelData = AudioBuffer.prototype.getChannelData;
    AudioBuffer.prototype.getChannelData = function(channel) {
        const data = originalGetChannelData.call(this, channel);
        // Add imperceptible noise
        for (let i = 0; i < data.length; i += 100) {
            data[i] = data[i] + (Math.random() * 0.0001 - 0.00005);
        }
        return data;
    };
    
    // Spoof createAnalyser
    const originalCreateAnalyser = audioContextProto.createAnalyser;
    audioContextProto.createAnalyser = function() {
        const analyser = originalCreateAnalyser.call(this);
        const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
        const originalGetByteFrequencyData = analyser.getByteFrequencyData;
        
        analyser.getFloatFrequencyData = function(array) {
            originalGetFloatFrequencyData.call(this, array);
            for (let i = 0; i < array.length; i += 10) {
                array[i] = array[i] + (Math.random() * 0.1 - 0.05);
            }
        };
        
        analyser.getByteFrequencyData = function(array) {
            originalGetByteFrequencyData.call(this, array);
            for (let i = 0; i < array.length; i += 10) {
                array[i] = Math.max(0, Math.min(255, array[i] + Math.floor(Math.random() * 2 - 1)));
            }
        };
        
        return analyser;
    };
    
    // Spoof sampleRate with realistic values
    const sampleRates = [44100, 48000, 96000];
    Object.defineProperty(AudioContext.prototype, 'sampleRate', {
        get: function() {
            return sampleRates[Math.floor(Math.random() * sampleRates.length)];
        }
    });
})();
"""

# ============================================================================
# FONT ENUMERATION SPOOFING
# ============================================================================

FONT_FINGERPRINT_SCRIPT = """
(function() {
    // Common fonts that should appear installed
    const commonFonts = [
        'Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 'Georgia',
        'Impact', 'Times New Roman', 'Trebuchet MS', 'Verdana', 'Helvetica',
        'Tahoma', 'Lucida Console', 'Palatino Linotype', 'Segoe UI'
    ];
    
    // Randomize which extra fonts appear "installed"
    const extraFonts = [
        'Calibri', 'Cambria', 'Consolas', 'Candara', 'Constantia',
        'Corbel', 'Franklin Gothic', 'Garamond', 'Gill Sans', 'Rockwell'
    ];
    
    const randomExtras = extraFonts.filter(() => Math.random() > 0.5);
    const installedFonts = new Set([...commonFonts, ...randomExtras]);
    
    // Override font detection methods
    const originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
    const originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
    
    // Add slight randomness to font width/height measurements
    if (originalOffsetWidth && originalOffsetWidth.get) {
        Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
            get: function() {
                const width = originalOffsetWidth.get.call(this);
                // Add noise only for font detection spans
                if (this.style && this.style.fontFamily && this.offsetParent === null) {
                    return width + (Math.random() * 0.5 - 0.25);
                }
                return width;
            }
        });
    }
    
    if (originalOffsetHeight && originalOffsetHeight.get) {
        Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
            get: function() {
                const height = originalOffsetHeight.get.call(this);
                if (this.style && this.style.fontFamily && this.offsetParent === null) {
                    return height + (Math.random() * 0.5 - 0.25);
                }
                return height;
            }
        });
    }
})();
"""

# ============================================================================
# SPEECH SYNTHESIS SPOOFING
# ============================================================================

SPEECH_SYNTHESIS_SCRIPT = """
(function() {
    // Randomize available voices
    const fakeVoices = [
        { name: 'Microsoft David - English (United States)', lang: 'en-US', localService: true, voiceURI: 'Microsoft David - English (United States)', default: true },
        { name: 'Microsoft Zira - English (United States)', lang: 'en-US', localService: true, voiceURI: 'Microsoft Zira - English (United States)', default: false },
        { name: 'Google US English', lang: 'en-US', localService: false, voiceURI: 'Google US English', default: false },
    ];
    
    // Random subset
    const numVoices = Math.floor(Math.random() * 3) + 2;
    const selectedVoices = fakeVoices.slice(0, numVoices);
    
    if (window.speechSynthesis) {
        Object.defineProperty(window.speechSynthesis, 'getVoices', {
            value: () => selectedVoices
        });
    }
})();
"""

# ============================================================================
# CLIENTRECTS NOISE INJECTION
# ============================================================================

CLIENTRECTS_NOISE_SCRIPT = """
(function() {
    // Add noise to getBoundingClientRect and getClientRects
    const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;
    const originalGetClientRects = Element.prototype.getClientRects;
    
    const addNoise = (value) => value + (Math.random() * 0.01 - 0.005);
    
    Element.prototype.getBoundingClientRect = function() {
        const rect = originalGetBoundingClientRect.call(this);
        return new DOMRect(
            addNoise(rect.x),
            addNoise(rect.y),
            addNoise(rect.width),
            addNoise(rect.height)
        );
    };
    
    Element.prototype.getClientRects = function() {
        const rects = originalGetClientRects.call(this);
        const noisyRects = [];
        for (let i = 0; i < rects.length; i++) {
            const rect = rects[i];
            noisyRects.push(new DOMRect(
                addNoise(rect.x),
                addNoise(rect.y),
                addNoise(rect.width),
                addNoise(rect.height)
            ));
        }
        return noisyRects;
    };
})();
"""

# ============================================================================
# DATE/TIME PRECISION REDUCTION
# ============================================================================

DATE_TIME_SCRIPT = """
(function() {
    // Reduce timestamp precision to prevent timing attacks
    const originalNow = Date.now;
    const originalPerformanceNow = performance.now;
    
    // Round to nearest 100ms
    Date.now = function() {
        return Math.floor(originalNow() / 100) * 100;
    };
    
    // Round performance.now to nearest 5ms
    performance.now = function() {
        return Math.floor(originalPerformanceNow.call(performance) / 5) * 5;
    };
    
    // Reduce timer precision
    const originalGetTime = Date.prototype.getTime;
    Date.prototype.getTime = function() {
        return Math.floor(originalGetTime.call(this) / 100) * 100;
    };
})();
"""

# ============================================================================
# PERMISSIONS API SPOOFING
# ============================================================================

PERMISSIONS_SCRIPT = """
(function() {
    // Spoof permissions to look like a normal browser
    const originalQuery = navigator.permissions.query;
    
    navigator.permissions.query = function(permissionDesc) {
        return new Promise((resolve) => {
            const fakeResult = {
                state: 'prompt',  // Most permissions should be 'prompt' by default
                onchange: null
            };
            
            // Some permissions are typically granted
            if (permissionDesc.name === 'notifications') {
                fakeResult.state = Math.random() > 0.5 ? 'granted' : 'prompt';
            } else if (permissionDesc.name === 'geolocation') {
                fakeResult.state = 'granted';  // We set geolocation in context
            }
            
            resolve(fakeResult);
        });
    };
})();
"""

# ============================================================================
# PERFORMANCE API NOISE
# ============================================================================

PERFORMANCE_API_SCRIPT = """
(function() {
    // Add noise to performance timing APIs used for fingerprinting
    const originalGetEntries = performance.getEntries;
    const originalGetEntriesByType = performance.getEntriesByType;
    const originalGetEntriesByName = performance.getEntriesByName;
    
    const addTimingNoise = (entries) => {
        return entries.map(entry => {
            if (entry.duration !== undefined) {
                const newEntry = Object.assign({}, entry);
                newEntry.duration = entry.duration + (Math.random() * 2 - 1);
                return newEntry;
            }
            return entry;
        });
    };
    
    performance.getEntries = function() {
        return addTimingNoise(originalGetEntries.call(this));
    };
    
    performance.getEntriesByType = function(type) {
        return addTimingNoise(originalGetEntriesByType.call(this, type));
    };
    
    performance.getEntriesByName = function(name, type) {
        return addTimingNoise(originalGetEntriesByName.call(this, name, type));
    };
})();
"""

# ============================================================================
# MEDIA DEVICES SPOOFING
# ============================================================================

MEDIA_DEVICES_SCRIPT = """
(function() {
    // Spoof media devices enumeration
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        const fakeDevices = [
            { deviceId: 'default', groupId: 'default', kind: 'audioinput', label: '' },
            { deviceId: 'communications', groupId: 'communications', kind: 'audioinput', label: '' },
            { deviceId: 'default', groupId: 'default', kind: 'audiooutput', label: '' },
            { deviceId: 'default', groupId: 'default', kind: 'videoinput', label: '' },
        ];
        
        // Randomize device count slightly
        const numDevices = Math.floor(Math.random() * 2) + 3;
        const selectedDevices = fakeDevices.slice(0, numDevices);
        
        navigator.mediaDevices.enumerateDevices = function() {
            return Promise.resolve(selectedDevices);
        };
    }
})();
"""

# ============================================================================
# DOCUMENT VISIBILITY SPOOFING
# ============================================================================

VISIBILITY_SCRIPT = """
(function() {
    // Always report as visible (bots often have hidden pages)
    Object.defineProperty(document, 'hidden', { get: () => false });
    Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
    
    // Prevent visibility change events from exposing automation
    document.addEventListener('visibilitychange', function(e) {
        e.stopImmediatePropagation();
    }, true);
})();
"""

# ============================================================================
# COMBINED SCRIPT
# ============================================================================

ADVANCED_ANTI_DETECTION_SCRIPT = f"""
// Advanced Anti-Detection Suite
{AUDIO_FINGERPRINT_SCRIPT}
{FONT_FINGERPRINT_SCRIPT}
{SPEECH_SYNTHESIS_SCRIPT}
{CLIENTRECTS_NOISE_SCRIPT}
{DATE_TIME_SCRIPT}
{PERMISSIONS_SCRIPT}
{PERFORMANCE_API_SCRIPT}
{MEDIA_DEVICES_SCRIPT}
{VISIBILITY_SCRIPT}
"""


def inject_advanced_anti_detection(context_or_page, is_context: bool = False):
    """
    Inject advanced anti-detection scripts.
    
    Args:
        context_or_page: Either a BrowserContext or Page object
        is_context: If True, inject at context level (applies to all pages)
    """
    try:
        target = context_or_page
        target_type = "context" if is_context else "page"
        
        target.add_init_script(ADVANCED_ANTI_DETECTION_SCRIPT)
        
        logger.info(f"🛡️ Advanced anti-detection scripts injected at {target_type} level")
        logger.debug("   └─ Audio, Font, Speech, ClientRects, DateTime, Permissions, Performance, MediaDevices, Visibility")
        
        return True
    except Exception as e:
        logger.warning(f"⚠️ Failed to inject advanced anti-detection scripts: {e}")
        return False


# ============================================================================
# DOMAIN RATE LIMITER
# ============================================================================

class DomainRateLimiter:
    """
    Track request frequency per domain to avoid detection.
    """
    
    def __init__(self, 
                 max_requests_per_domain_per_hour: int = 30,
                 min_delay_between_requests: float = 5.0,
                 max_delay_between_requests: float = 15.0):
        self.max_requests_per_hour = max_requests_per_domain_per_hour
        self.min_delay = min_delay_between_requests
        self.max_delay = max_delay_between_requests
        
        # {domain: [timestamp1, timestamp2, ...]}
        self.domain_requests: dict = {}
        
        # {domain: last_request_timestamp}
        self.last_request: dict = {}
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    
    def _clean_old_requests(self, domain: str):
        """Remove requests older than 1 hour."""
        import time
        cutoff = time.time() - 3600  # 1 hour ago
        if domain in self.domain_requests:
            self.domain_requests[domain] = [
                ts for ts in self.domain_requests[domain] if ts > cutoff
            ]
    
    def can_request(self, url: str) -> tuple:
        """
        Check if we can make a request to this domain.
        
        Returns:
            (can_request: bool, wait_time: float, reason: str)
        """
        import time
        
        domain = self._extract_domain(url)
        self._clean_old_requests(domain)
        
        now = time.time()
        
        # Check hourly limit
        requests_in_hour = len(self.domain_requests.get(domain, []))
        if requests_in_hour >= self.max_requests_per_hour:
            oldest = min(self.domain_requests[domain]) if self.domain_requests.get(domain) else now
            wait_time = 3600 - (now - oldest) + random.uniform(60, 300)
            return False, wait_time, f"Rate limit: {requests_in_hour}/{self.max_requests_per_hour} requests to {domain} in last hour"
        
        # Check minimum interval
        last = self.last_request.get(domain, 0)
        elapsed = now - last
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed + random.uniform(0, 3)
            return False, wait_time, f"Too soon since last request to {domain}"
        
        return True, 0, "OK"
    
    def record_request(self, url: str):
        """Record that a request was made."""
        import time
        
        domain = self._extract_domain(url)
        now = time.time()
        
        if domain not in self.domain_requests:
            self.domain_requests[domain] = []
        
        self.domain_requests[domain].append(now)
        self.last_request[domain] = now
        
        logger.debug(f"Recorded request to {domain}. Total in last hour: {len(self.domain_requests[domain])}")
    
    def get_recommended_delay(self, url: str) -> float:
        """Get recommended delay before making request."""
        import time
        
        domain = self._extract_domain(url)
        self._clean_old_requests(domain)
        
        requests_in_hour = len(self.domain_requests.get(domain, []))
        
        # Scale delay based on request frequency
        # More requests = longer delays
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        if requests_in_hour > 10:
            # Add extra delay if we've made many requests
            extra_delay = (requests_in_hour - 10) * 2
            base_delay += min(extra_delay, 60)  # Cap at 60s extra
        
        return base_delay
    
    def get_stats(self, url: str = None) -> dict:
        """Get rate limiting statistics."""
        if url:
            domain = self._extract_domain(url)
            self._clean_old_requests(domain)
            return {
                "domain": domain,
                "requests_last_hour": len(self.domain_requests.get(domain, [])),
                "max_per_hour": self.max_requests_per_hour,
                "last_request": self.last_request.get(domain)
            }
        
        return {
            "domains_tracked": len(self.domain_requests),
            "total_requests_last_hour": sum(len(v) for v in self.domain_requests.values()),
            "max_per_hour_per_domain": self.max_requests_per_hour
        }


# ============================================================================
# SESSION PERSISTENCE
# ============================================================================

class SessionManager:
    """
    Manage browser sessions with cookie persistence.
    Makes the scraper look like a returning visitor.
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        import os
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Track session usage
        self.session_usage: dict = {}  # {domain: {"path": path, "last_used": timestamp, "success_count": int}}
    
    def _get_session_path(self, domain: str) -> str:
        """Get session file path for a domain."""
        import os
        safe_domain = domain.replace(".", "_").replace(":", "_")
        return os.path.join(self.sessions_dir, f"{safe_domain}.json")
    
    def get_session(self, url: str) -> str | None:
        """Get session storage path for URL's domain if it exists."""
        from urllib.parse import urlparse
        import os
        
        domain = urlparse(url).netloc
        path = self._get_session_path(domain)
        
        if os.path.exists(path):
            logger.info(f"🍪 Using saved session for {domain}")
            return path
        
        return None
    
    def save_session(self, context, url: str):
        """Save browser context state (cookies, localStorage) for domain."""
        from urllib.parse import urlparse
        import time
        
        try:
            domain = urlparse(url).netloc
            path = self._get_session_path(domain)
            
            context.storage_state(path=path)
            
            self.session_usage[domain] = {
                "path": path,
                "last_used": time.time(),
                "success_count": self.session_usage.get(domain, {}).get("success_count", 0) + 1
            }
            
            logger.info(f"🍪 Saved session for {domain}")
            return path
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
            return None
    
    def should_use_session(self, url: str) -> bool:
        """Decide if we should use saved session (randomize to look natural)."""
        from urllib.parse import urlparse
        import os
        
        domain = urlparse(url).netloc
        path = self._get_session_path(domain)
        
        if not os.path.exists(path):
            return False
        
        # 80% chance to use saved session (some variance)
        return random.random() < 0.8
    
    def clear_session(self, url: str):
        """Clear saved session for domain."""
        from urllib.parse import urlparse
        import os
        
        domain = urlparse(url).netloc
        path = self._get_session_path(domain)
        
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"🗑️ Cleared session for {domain}")


# ============================================================================
# HUMANIZED KEYBOARD INPUT
# ============================================================================

def type_like_human(page, selector: str, text: str, 
                    min_delay: int = 50, max_delay: int = 150):
    """
    Type text with human-like delays between keystrokes.
    Includes occasional typos and corrections for realism.
    """
    import time
    
    element = page.locator(selector)
    element.focus()
    
    for i, char in enumerate(text):
        # Occasional typo (3% chance)
        if random.random() < 0.03 and char.isalpha():
            # Type wrong character
            wrong_char = chr(ord(char) + random.choice([-1, 1]))
            page.keyboard.type(wrong_char)
            time.sleep(random.uniform(0.1, 0.3))
            # Backspace and correct
            page.keyboard.press("Backspace")
            time.sleep(random.uniform(0.05, 0.15))
        
        # Type the character
        page.keyboard.type(char)
        
        # Variable delay
        delay = random.randint(min_delay, max_delay)
        
        # Longer pause after punctuation
        if char in ".,!?;:":
            delay *= 2
        
        # Occasional longer pause (thinking)
        if random.random() < 0.05:
            delay *= 3
        
        time.sleep(delay / 1000)


# ============================================================================
# NATURAL MOUSE MOVEMENT (BEZIER CURVES)
# ============================================================================

def move_mouse_naturally(page, target_x: int, target_y: int, duration: float = 0.5):
    """
    Move mouse using bezier curves for natural-looking movement.
    """
    import time
    
    try:
        # Get current position (approximate)
        viewport = page.viewport_size
        if not viewport:
            return
        
        # Start from random edge position
        start_x = random.randint(0, viewport['width'])
        start_y = random.randint(0, viewport['height'])
        
        # Generate bezier control points
        ctrl1_x = start_x + (target_x - start_x) * 0.3 + random.randint(-50, 50)
        ctrl1_y = start_y + (target_y - start_y) * 0.3 + random.randint(-50, 50)
        ctrl2_x = start_x + (target_x - start_x) * 0.7 + random.randint(-50, 50)
        ctrl2_y = start_y + (target_y - start_y) * 0.7 + random.randint(-50, 50)
        
        # Number of steps
        steps = int(duration * 60)  # 60 fps
        
        for i in range(steps + 1):
            t = i / steps
            
            # Bezier curve calculation
            u = 1 - t
            x = u**3 * start_x + 3 * u**2 * t * ctrl1_x + 3 * u * t**2 * ctrl2_x + t**3 * target_x
            y = u**3 * start_y + 3 * u**2 * t * ctrl1_y + 3 * u * t**2 * ctrl2_y + t**3 * target_y
            
            page.mouse.move(x, y)
            time.sleep(duration / steps)
            
    except Exception as e:
        logger.debug(f"Natural mouse movement skipped: {e}")
