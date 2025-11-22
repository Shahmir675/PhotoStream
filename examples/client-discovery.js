/**
 * PhotoStream Client - Geographic Server Discovery
 *
 * This module automatically discovers and connects to the nearest PhotoStream server
 * for optimal performance without requiring a custom domain.
 *
 * Usage:
 *   import { PhotoStreamClient } from './client-discovery.js';
 *
 *   const client = new PhotoStreamClient();
 *   await client.initialize();
 *
 *   // Make API calls
 *   const photos = await client.get('/api/photos');
 */

class PhotoStreamClient {
    constructor(options = {}) {
        // Default options
        this.options = {
            // Primary discovery endpoint (any regional server works)
            discoveryEndpoint: 'https://photostream-api-us-west.onrender.com',
            // Cache server selection in localStorage
            cacheServer: true,
            // Re-discover after this many hours (0 = never)
            rediscoverAfterHours: 24,
            // Fallback server if discovery fails
            fallbackServer: 'https://photostream-api-us-west.onrender.com',
            // Enable debug logging
            debug: false,
            ...options
        };

        this.currentServer = null;
        this.initialized = false;
    }

    /**
     * Initialize the client by discovering the best server
     */
    async initialize() {
        if (this.initialized) {
            return;
        }

        this.log('Initializing PhotoStream client...');

        // Check if we have a cached server
        if (this.options.cacheServer) {
            const cached = this._getCachedServer();
            if (cached) {
                this.currentServer = cached.server;
                this.log(`Using cached server: ${this.currentServer} (region: ${cached.region})`);
                this.initialized = true;

                // Check if we should rediscover
                if (this._shouldRediscover(cached.timestamp)) {
                    this.log('Cached server expired, rediscovering in background...');
                    this._discoverInBackground();
                }

                return;
            }
        }

        // No cached server, discover now
        await this.discover();
        this.initialized = true;
    }

    /**
     * Discover the best server for this client
     */
    async discover() {
        this.log('Discovering best server...');

        try {
            const response = await fetch(`${this.options.discoveryEndpoint}/api/discover`);

            if (!response.ok) {
                throw new Error(`Discovery failed: ${response.status}`);
            }

            const data = await response.json();

            this.currentServer = data.server;
            this.log(`Discovered server: ${this.currentServer} (region: ${data.region})`);

            // Cache the result
            if (this.options.cacheServer) {
                this._cacheServer(data.server, data.region);
            }

            return data;

        } catch (error) {
            console.error('Server discovery failed:', error);
            this.currentServer = this.options.fallbackServer;
            this.log(`Using fallback server: ${this.currentServer}`);
        }
    }

    /**
     * Alternative: Test latency to all servers and pick the fastest
     */
    async discoverByLatency() {
        this.log('Testing latency to all servers...');

        const servers = [
            'https://photostream-api-us-west.onrender.com',
            'https://photostream-api-us-east.onrender.com',
            'https://photostream-api-eu.onrender.com'
        ];

        const results = await Promise.all(
            servers.map(async (server) => {
                const start = Date.now();
                try {
                    await fetch(`${server}/ping`, { method: 'GET' });
                    const latency = Date.now() - start;
                    this.log(`${server}: ${latency}ms`);
                    return { server, latency };
                } catch (error) {
                    this.log(`${server}: offline`);
                    return { server, latency: Infinity };
                }
            })
        );

        // Sort by latency
        results.sort((a, b) => a.latency - b.latency);

        const fastest = results[0];
        this.currentServer = fastest.server;
        this.log(`Fastest server: ${this.currentServer} (${fastest.latency}ms)`);

        // Cache the result
        if (this.options.cacheServer) {
            this._cacheServer(fastest.server, 'latency-tested');
        }

        return fastest;
    }

    /**
     * Get list of all available regions and their health
     */
    async getRegions() {
        try {
            const response = await fetch(`${this.options.discoveryEndpoint}/api/regions`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch regions:', error);
            return null;
        }
    }

    /**
     * Make a GET request to the API
     */
    async get(endpoint, options = {}) {
        await this._ensureInitialized();
        const url = `${this.currentServer}${endpoint}`;
        return this._fetch(url, { ...options, method: 'GET' });
    }

    /**
     * Make a POST request to the API
     */
    async post(endpoint, data, options = {}) {
        await this._ensureInitialized();
        const url = `${this.currentServer}${endpoint}`;
        return this._fetch(url, {
            ...options,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: JSON.stringify(data)
        });
    }

    /**
     * Make a PUT request to the API
     */
    async put(endpoint, data, options = {}) {
        await this._ensureInitialized();
        const url = `${this.currentServer}${endpoint}`;
        return this._fetch(url, {
            ...options,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: JSON.stringify(data)
        });
    }

    /**
     * Make a DELETE request to the API
     */
    async delete(endpoint, options = {}) {
        await this._ensureInitialized();
        const url = `${this.currentServer}${endpoint}`;
        return this._fetch(url, { ...options, method: 'DELETE' });
    }

    /**
     * Upload a file
     */
    async upload(endpoint, file, additionalData = {}, options = {}) {
        await this._ensureInitialized();
        const url = `${this.currentServer}${endpoint}`;

        const formData = new FormData();
        formData.append('file', file);

        // Add additional form fields
        for (const [key, value] of Object.entries(additionalData)) {
            formData.append(key, value);
        }

        return this._fetch(url, {
            ...options,
            method: 'POST',
            body: formData
            // Don't set Content-Type, browser will set it with boundary
        });
    }

    /**
     * Set authentication token
     */
    setAuthToken(token) {
        this.authToken = token;
    }

    /**
     * Clear authentication token
     */
    clearAuthToken() {
        this.authToken = null;
    }

    /**
     * Get current server URL
     */
    getServerUrl() {
        return this.currentServer;
    }

    // ========================================
    // Private methods
    // ========================================

    async _fetch(url, options = {}) {
        // Add auth token if available
        if (this.authToken) {
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${this.authToken}`
            };
        }

        const response = await fetch(url, options);

        // Handle errors
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            error.response = response;

            try {
                error.data = await response.json();
            } catch (e) {
                // Response is not JSON
            }

            throw error;
        }

        // Return JSON if response has content
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return response;
    }

    async _ensureInitialized() {
        if (!this.initialized) {
            await this.initialize();
        }
    }

    _getCachedServer() {
        if (typeof localStorage === 'undefined') {
            return null;
        }

        try {
            const cached = localStorage.getItem('photostream_server');
            if (cached) {
                return JSON.parse(cached);
            }
        } catch (error) {
            console.error('Failed to read cached server:', error);
        }

        return null;
    }

    _cacheServer(server, region) {
        if (typeof localStorage === 'undefined') {
            return;
        }

        try {
            const data = {
                server,
                region,
                timestamp: Date.now()
            };
            localStorage.setItem('photostream_server', JSON.stringify(data));
        } catch (error) {
            console.error('Failed to cache server:', error);
        }
    }

    _shouldRediscover(cachedTimestamp) {
        if (this.options.rediscoverAfterHours === 0) {
            return false;
        }

        const hoursSinceCache = (Date.now() - cachedTimestamp) / (1000 * 60 * 60);
        return hoursSinceCache > this.options.rediscoverAfterHours;
    }

    _discoverInBackground() {
        // Rediscover asynchronously without blocking
        this.discover().catch(error => {
            console.error('Background rediscovery failed:', error);
        });
    }

    log(message) {
        if (this.options.debug) {
            console.log(`[PhotoStream] ${message}`);
        }
    }
}

// ========================================
// Usage Examples
// ========================================

/**
 * Example 1: Basic usage with automatic discovery
 */
async function example1() {
    const client = new PhotoStreamClient({ debug: true });
    await client.initialize();

    // Fetch photos
    const photos = await client.get('/api/photos');
    console.log('Photos:', photos);
}

/**
 * Example 2: Manual latency-based discovery
 */
async function example2() {
    const client = new PhotoStreamClient();
    await client.discoverByLatency();

    // Make API calls
    const photos = await client.get('/api/photos');
    console.log('Photos:', photos);
}

/**
 * Example 3: With authentication
 */
async function example3() {
    const client = new PhotoStreamClient();
    await client.initialize();

    // Login
    const loginData = await client.post('/api/auth/login', {
        username: 'user@example.com',
        password: 'password123'
    });

    // Set auth token
    client.setAuthToken(loginData.access_token);

    // Now make authenticated requests
    const profile = await client.get('/api/auth/me');
    console.log('Profile:', profile);
}

/**
 * Example 4: File upload
 */
async function example4() {
    const client = new PhotoStreamClient();
    await client.initialize();

    // Assume we have a file input element
    const fileInput = document.querySelector('input[type="file"]');
    const file = fileInput.files[0];

    // Upload photo
    const result = await client.upload('/api/photos/upload', file, {
        title: 'My Photo',
        description: 'Beautiful sunset'
    });

    console.log('Upload result:', result);
}

/**
 * Example 5: Check available regions
 */
async function example5() {
    const client = new PhotoStreamClient({ debug: true });

    const regions = await client.getRegions();
    console.log('Available regions:', regions);

    // Display region status
    regions.regions.forEach(region => {
        console.log(`${region.region}: ${region.status} (${region.response_time_ms}ms)`);
    });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PhotoStreamClient };
}
