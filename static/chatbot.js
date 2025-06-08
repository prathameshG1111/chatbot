// Store sender_id in localStorage for consistent Rasa session
if (!localStorage.getItem('sender_id')) {
    localStorage.setItem('sender_id', crypto.randomUUID());
}


// Toggle chat window visibility
function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    chatWindow.style.display = chatWindow.style.display === 'none' || chatWindow.style.display === '' ? 'block' : 'none';
}

// Get the image paths from the hidden input fields
const userIconPath = document.getElementById('userIconPath').value;
const botIconPath = document.getElementById('botIconPath').value;

// Function to handle sending messages
document.getElementById('send-btn').addEventListener('click', function() {
    sendMessage();
});

function sendMessage() {
    const inputField = document.getElementById('user-input');
    const userMessage = inputField.value.trim();
    const sender_id = localStorage.getItem('sender_id'); // Retrieve sender_id

    if (userMessage !== '') {
        appendMessage('user', userMessage);
        inputField.value = ''; // Clear the input field

        // Display typing indicator in bot's chat bubble
        appendTypingIndicator();

        // Make an AJAX request to the Flask backend to get the bot's response
        fetch('/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({message: userMessage, sender_id: sender_id})
        })
        .then(response => response.json())
        .then(data => {
            const botResponse = data.response;

            // Delay the removal of the typing indicator by 1 second
            setTimeout(() => {
                removeTypingIndicator(); // Remove typing indicator after 1 second
                appendMessage('bot', botResponse); // Append bot response after the delay
            }, 1000); // 1 second delay (1000 milliseconds)
        })
        .catch(error => {
            console.error('Error:', error);

            // Remove the typing indicator and show error message after the delay
            setTimeout(() => {
                removeTypingIndicator(); // Remove typing indicator in case of error
                appendMessage('bot', "Sorry, I'm having trouble understanding. Please try again.");
            }, 1000);
        });
    }
}


// Append user or bot messages to chat window
function appendMessage(sender, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    const profileImg = document.createElement('img');

    // Get the current time
    const currentTime = new Date();
    const hours = currentTime.getHours();
    const minutes = currentTime.getMinutes().toString().padStart(2, '0'); // Add leading zero if needed
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayTime = (hours % 12 || 12) + ':' + minutes + ' ' + ampm;

    // Configure the message based on sender
    if (sender === 'user') {
        messageDiv.className = 'user-message';
        profileImg.src = userIconPath; // Use the user icon path
    } else if (sender === 'bot') {
        messageDiv.className = 'bot-message';
        profileImg.src = botIconPath; // Use the bot icon path
    }

    profileImg.alt = sender + ' profile';
    messageDiv.appendChild(profileImg);

    // Add message text
    const messageText = document.createElement('span');
    messageText.innerHTML = message;
    messageDiv.appendChild(messageText);

    // Add time stamp
    const timeStamp = document.createElement('span');
    timeStamp.className = 'timestamp';
    timeStamp.textContent = displayTime; // Add the formatted time to the time stamp
    messageDiv.appendChild(timeStamp);

    // Append the new message to the chat
    chatMessages.appendChild(messageDiv);

    // Scroll to the latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Append typing indicator for the bot's message
function appendTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'bot-message typing-indicator';
    
    const profileImg = document.createElement('img');
    profileImg.src = botIconPath; // Bot's profile image
    profileImg.alt = 'Bot profile';
    typingDiv.appendChild(profileImg);

    // Create typing dots animation
    const typingDots = document.createElement('div');
    typingDots.className = 'thinking-indicator';
    typingDots.innerHTML = `
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
    `;
    typingDiv.appendChild(typingDots);

    chatMessages.appendChild(typingDiv);

    // Scroll to the latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator when bot's response is ready
function removeTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove(); // Remove the typing indicator div
    }
}

window.addEventListener('load', function() {
    const welcomeMessage = document.getElementById('welcome-message');

    // Function to determine the greeting based on time of day
    function getDynamicGreeting() {
        const currentHour = new Date().getHours();
        if (currentHour < 12) {
            return "Good Morning! How can I help you today?";
        } else if (currentHour < 18) {
            return "Good Afternoon! How can I assist you?";
        } else {
            return "Good Evening! How may I help you?";
        }
    }

    if (welcomeMessage) {
        // Show the first part of the welcome message after a brief delay
        setTimeout(function() {
            welcomeMessage.innerHTML = "Hi!! I am your assistant!";
            welcomeMessage.classList.add('show'); // Show the message

            // Wait for 3.5 seconds before displaying the second part
            setTimeout(function() {
                welcomeMessage.innerHTML = "How can I help you?"; // Update to the second message
            }, 3500); // Delay for the second part

        // Append the dynamic greeting immediately
        const dynamicGreeting = getDynamicGreeting();
        appendMessage('bot', dynamicGreeting); // Append dynamic greeting
        }, 1000); // Initial delay to show the first message

        // Optional: Remove the message after 8 seconds total
        setTimeout(function() {
            welcomeMessage.classList.remove('show'); // Hide after showing for 8 seconds
        }, 8000); // Adjust timing as needed
    }
});