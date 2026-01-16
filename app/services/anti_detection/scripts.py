"""
Anti-Detection JavaScript Scripts
=================================
JavaScript injection scripts for browser fingerprint spoofing.

These scripts modify browser APIs to add noise and prevent fingerprinting:
1. Audio fingerprint spoofing
2. Font enumeration spoofing
3. Speech synthesis spoofing
4. Permissions API spoofing
5. ClientRects noise injection
6. Date/Time precision reduction
7. Performance API noise
8. Media devices spoofing
9. Document visibility spoofing
"""

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

# Export all scripts
__all__ = [
    'AUDIO_FINGERPRINT_SCRIPT',
    'FONT_FINGERPRINT_SCRIPT',
    'SPEECH_SYNTHESIS_SCRIPT',
    'CLIENTRECTS_NOISE_SCRIPT',
    'DATE_TIME_SCRIPT',
    'PERMISSIONS_SCRIPT',
    'PERFORMANCE_API_SCRIPT',
    'MEDIA_DEVICES_SCRIPT',
    'VISIBILITY_SCRIPT',
    'ADVANCED_ANTI_DETECTION_SCRIPT',
]
