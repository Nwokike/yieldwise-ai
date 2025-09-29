// Offline functionality for YieldWise AI

class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.init();
    }
    
    init() {
        // Listen for online/offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Check connection status periodically
        setInterval(() => this.checkConnection(), 30000);
        
        // Show initial status
        if (!this.isOnline) {
            this.showOfflineMessage();
        }
    }
    
    handleOnline() {
        this.isOnline = true;
        this.hideOfflineMessage();
        NotificationManager.success('Connection restored! You\'re back online.');
        
        // Sync any pending data
        this.syncPendingData();
    }
    
    handleOffline() {
        this.isOnline = false;
        this.showOfflineMessage();
        NotificationManager.info('You\'re offline. Some features may be limited.');
    }
    
    async checkConnection() {
        try {
            const response = await fetch('/api/health', { 
                method: 'HEAD',
                cache: 'no-cache'
            });
            
            if (response.ok && !this.isOnline) {
                this.handleOnline();
            }
        } catch (error) {
            if (this.isOnline) {
                this.handleOffline();
            }
        }
    }
    
    showOfflineMessage() {
        let offlineBar = document.getElementById('offline-bar');
        if (!offlineBar) {
            offlineBar = document.createElement('div');
            offlineBar.id = 'offline-bar';
            offlineBar.innerHTML = `
                <div style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background-color: #ff9800;
                    color: white;
                    text-align: center;
                    padding: 10px;
                    font-weight: 600;
                    z-index: 1001;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    📡 You're offline - Some features may be limited
                </div>
            `;
            document.body.appendChild(offlineBar);
            
            // Adjust body padding to account for offline bar
            document.body.style.paddingTop = '50px';
        }
    }
    
    hideOfflineMessage() {
        const offlineBar = document.getElementById('offline-bar');
        if (offlineBar) {
            document.body.removeChild(offlineBar);
            document.body.style.paddingTop = '0';
        }
    }
    
    // Save data for later sync when online
    savePendingData(key, data) {
        const pending = StorageManager.load('pending_sync') || {};
        pending[key] = {
            data: data,
            timestamp: Date.now()
        };
        StorageManager.save('pending_sync', pending);
    }
    
    // Sync pending data when connection is restored
    async syncPendingData() {
        const pending = StorageManager.load('pending_sync');
        if (!pending) return;
        
        const syncPromises = [];
        
        for (const [key, item] of Object.entries(pending)) {
            // Only sync data that's less than 24 hours old
            if (Date.now() - item.timestamp < 24 * 60 * 60 * 1000) {
                syncPromises.push(this.syncItem(key, item.data));
            }
        }
        
        try {
            await Promise.all(syncPromises);
            StorageManager.remove('pending_sync');
            NotificationManager.success('Offline data synced successfully!');
        } catch (error) {
            console.error('Failed to sync some offline data:', error);
        }
    }
    
    async syncItem(key, data) {
        // Implement specific sync logic based on data type
        if (key.startsWith('draft_')) {
            // Handle draft data sync
            console.log('Syncing draft data:', key);
        }
        // Add more sync handlers as needed
    }
}

// Service Worker registration for offline caching
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            const registration = await navigator.serviceWorker.register('/static/js/sw.js');
            console.log('ServiceWorker registered successfully');
        } catch (error) {
            console.log('ServiceWorker registration failed:', error);
        }
    });
}

// Initialize offline manager
const offlineManager = new OfflineManager();

// Export for use in other scripts
window.OfflineManager = OfflineManager;