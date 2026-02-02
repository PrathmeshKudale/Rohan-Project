// Language management
function changeLanguage(lang) {
    fetch('/change-language', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: lang })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showToast(`Language changed to ${lang}`);
            
            // Reload page content based on language
            updateContentForLanguage(lang);
        }
    })
    .catch(error => {
        console.error('Language change error:', error);
        showToast('Error changing language', 'error');
    });
}

function updateContentForLanguage(lang) {
    // Update UI text based on language
    const translations = {
        'hindi': {
            'welcome': 'स्वागत है किसान!',
            'scanCrop': 'फसल स्कैन करें',
            'askAI': 'एआई से पूछें'
        },
        'english': {
            'welcome': 'Welcome Farmer!',
            'scanCrop': 'Scan Crop',
            'askAI': 'Ask AI'
        }
    };
    
    const translation = translations[lang] || translations['english'];
    
    // Update elements with data-translate attribute
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        if (translation[key]) {
            element.textContent = translation[key];
        }
    });
}

// Voice Assistant
let recognition = null;
let isListening = false;

function initVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'hi-IN'; // Default to Hindi-India
        
        recognition.onstart = function() {
            isListening = true;
            document.getElementById('micButton').classList.add('listening');
            document.getElementById('statusText').textContent = 'Listening...';
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('queryText').textContent = transcript;
            processVoiceQuery(transcript);
        };
        
        recognition.onend = function() {
            isListening = false;
            document.getElementById('micButton').classList.remove('listening');
            document.getElementById('statusText').textContent = 'Tap mic to speak';
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            showToast('Voice recognition error. Please try again.', 'error');
            isListening = false;
            document.getElementById('micButton').classList.remove('listening');
        };
    } else {
        showToast('Voice recognition not supported in this browser', 'warning');
    }
}

function startVoice() {
    if (!recognition) {
        initVoiceRecognition();
    }
    
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function processVoiceQuery(query) {
    // Show loading
    document.getElementById('responseArea').innerHTML = `
        <div class="response-card">
            <div class="loading"></div>
            <p>Processing your question...</p>
        </div>
    `;
    
    // Send to backend
    fetch('/ask-ai', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        displayResponse(data);
        
        // Speak the response
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(data.voice);
            utterance.lang = document.getElementById('languageSelect').value + '-IN';
            speechSynthesis.speak(utterance);
        }
    })
    .catch(error => {
        console.error('Error processing query:', error);
        showToast('Error processing your question', 'error');
    });
}

function displayResponse(data) {
    const responseArea = document.getElementById('responseArea');
    responseArea.innerHTML = `
        <div class="response-card">
            <div class="response-text">${data.response}</div>
            <div class="response-source">
                <i class="fas fa-robot"></i> Source: ${data.source}
            </div>
        </div>
    `;
}

// Toast notifications
function showToast(message, type = 'success') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 9999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add CSS animations for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Set current language in select
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        // In production, get from session/localStorage
        languageSelect.value = 'hindi';
    }
    
    // Initialize tooltips
    initTooltips();
    
    // Add click effect to buttons
    document.querySelectorAll('.btn, .action-card, .nav-item').forEach(button => {
        button.addEventListener('click', function(e) {
            // Add ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size/2;
            const y = e.clientY - rect.top - size/2;
            
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.7);
                transform: scale(0);
                animation: ripple 0.6s linear;
                width: ${size}px;
                height: ${size}px;
                top: ${y}px;
                left: ${x}px;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
});

function initTooltips() {
    // Add tooltips to icons
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.cssText = `
                position: fixed;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 0.85rem;
                z-index: 9999;
                top: ${rect.bottom + 5}px;
                left: ${rect.left + rect.width/2}px;
                transform: translateX(-50%);
                white-space: nowrap;
            `;
            
            this.tooltipElement = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this.tooltipElement) {
                this.tooltipElement.remove();
            }
        });
    });
}

// Weather data fetching
function fetchWeather() {
    // In production, integrate with weather API
    return {
        current: {
            temp: '32°C',
            condition: 'Partly Cloudy',
            humidity: '65%',
            wind: '12 km/h',
            rain: '20%'
        }
    };
}

// Image processing
function compressImage(file, maxWidth = 800, maxHeight = 800, quality = 0.8) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        
        reader.onload = function(event) {
            const img = new Image();
            img.src = event.target.result;
            
            img.onload = function() {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                
                if (width > height) {
                    if (width > maxWidth) {
                        height *= maxWidth / width;
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width *= maxHeight / height;
                        height = maxHeight;
                    }
                }
                
                canvas.width = width;
                canvas.height = height;
                
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob(blob => {
                    resolve(new File([blob], file.name, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    }));
                }, 'image/jpeg', quality);
            };
            
            img.onerror = reject;
        };
        
        reader.onerror = reject;
    });
}

// Offline detection
function checkConnection() {
    if (!navigator.onLine) {
        showToast('You are offline. Some features may not work.', 'warning');
    }
}

window.addEventListener('online', () => showToast('Back online!', 'success'));
window.addEventListener('offline', () => showToast('Connection lost', 'warning'));

// Initialize connection check
checkConnection();
