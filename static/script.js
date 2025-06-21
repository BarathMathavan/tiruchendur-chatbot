document.addEventListener('DOMContentLoaded', () => {

    const contentDisplay = document.getElementById('content-display');
    const chatOpener = document.getElementById('chat-opener');
    const chatWindow = document.getElementById('chat-window');
    const chatCloser = document.getElementById('chat-closer');
    const chatBox = document.getElementById('chat-box');
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');

    // Default coordinates for Tiruchendur as a fallback
    const TIRUCHENDUR_COORDS = "8.4967,78.1245";

    // --- INITIALIZATION ---
    if (INITIAL_BOT_RESPONSE && INITIAL_BOT_RESPONSE.text) {
        addMessage(INITIAL_BOT_RESPONSE.text, 'bot', INITIAL_BOT_RESPONSE.buttons);
    }

    // --- EVENT LISTENERS ---
    chatOpener.addEventListener('click', () => toggleChatWindow(true));
    chatCloser.addEventListener('click', () => toggleChatWindow(false));
    messageForm.addEventListener('submit', handleFormSubmit);
    chatBox.addEventListener('click', handleChatBoxClick);

    /**
     * Tries to get the user's current GPS location.
     * Returns a Promise that resolves with a coordinate string or rejects.
     */
    function getUserLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject('Geolocation is not supported by your browser.');
                return;
            }

            const options = {
                enableHighAccuracy: true,
                timeout: 10000, // 10 seconds
                maximumAge: 0
            };

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    resolve(`${lat},${lon}`);
                },
                () => {
                    reject('Permission denied or unable to get location.');
                },
                options
            );
        });
    }

    async function handleChatBoxClick(event) {
        const target = event.target;
        const embedLink = target.closest('a[data-embed="true"]');

        if (embedLink) {
            event.preventDefault(); 
            let finalUrl = embedLink.href;

            // Check if this link needs the user's current location
            if (finalUrl.includes('origin=CURRENT_LOCATION')) {
                addMessage('Getting your location to calculate the route...', 'bot');
                try {
                    const userLocation = await getUserLocation();
                    console.log("User location success:", userLocation);
                    finalUrl = finalUrl.replace('CURRENT_LOCATION', userLocation);
                } catch (error) {
                    console.warn("Could not get user location:", error);
                    addMessage('Could not get your location. Using the temple as the starting point.', 'bot');
                    // Fallback to default coordinates
                    finalUrl = finalUrl.replace('CURRENT_LOCATION', TIRUCHENDUR_COORDS);
                }
            }
            loadMapInIframe(finalUrl);
            return;
        }

        const chatButton = target.closest('.chat-button');
        if (chatButton) {
            event.preventDefault();
            const payload = chatButton.dataset.payload;
            const buttonText = chatButton.textContent.trim();
            addMessage(buttonText, 'user');
            const buttonContainer = chatButton.closest('.button-container');
            if (buttonContainer) {
                buttonContainer.querySelectorAll('.chat-button').forEach(btn => btn.disabled = true);
            }
            sendMessageToServer(payload);
        }
    }

    function toggleChatWindow(show) {
        chatWindow.classList.toggle('visible', show);
        if (show) userInput.focus();
    }

    function handleFormSubmit(event) {
        event.preventDefault();
        const question = userInput.value.trim();
        if (!question) return;
        addMessage(question, 'user');
        userInput.value = '';
        sendMessageToServer(question);
    }

    function loadMapInIframe(mapUrl) {
        console.log("Loading map in iframe:", mapUrl);
        contentDisplay.innerHTML = '';
        const iframe = document.createElement('iframe');
        iframe.src = mapUrl;
        iframe.setAttribute('allowfullscreen', '');
        iframe.setAttribute('loading', 'lazy');
        iframe.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
        contentDisplay.appendChild(iframe);
        toggleChatWindow(false);
    }

    async function sendMessageToServer(message) {
        toggleInput(false);
        showTypingIndicator(true);
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: message, user_id: USER_ID })
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const data = await response.json();
            addMessage(data.text, 'bot', data.buttons);
        } catch (error) {
            console.error('Error fetching bot response:', error);
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        } finally {
            showTypingIndicator(false);
            toggleInput(true);
        }
    }
    
    function addMessage(text, sender, buttons = []) {
        if (!text) return;

        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        const bubbleElement = document.createElement('div');
        bubbleElement.classList.add('bubble');
        const textElement = document.createElement('div');
        textElement.innerHTML = text;
        bubbleElement.appendChild(textElement);
        if (buttons.length > 0) {
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'button-container';
            buttons.forEach(btnData => {
                const button = document.createElement('button');
                button.className = 'chat-button';
                button.textContent = btnData.text;
                button.dataset.payload = btnData.payload;
                buttonContainer.appendChild(button);
            });
            bubbleElement.appendChild(buttonContainer);
        }
        messageElement.appendChild(bubbleElement);
        chatBox.insertBefore(messageElement, typingIndicator);
    }

    function showTypingIndicator(show) {
        typingIndicator.classList.toggle('visible', show);
    }

    function toggleInput(enabled) {
        userInput.disabled = !enabled;
        sendButton.disabled = !enabled;
        if (enabled) userInput.focus();
    }
});