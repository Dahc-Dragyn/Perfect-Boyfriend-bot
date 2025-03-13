document.getElementById('send-button').addEventListener('click', sendMessage);

document.getElementById('user-input').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    let userInput = document.getElementById('user-input').value;
    if (userInput.trim()!== "") {
        displayMessage('user', userInput);
        showTypingIndicator(); // Show indicator
        sendMessageToServer(userInput);
        document.getElementById('user-input').value = '';
        document.getElementById('user-input').focus();
    }
}

function displayMessage(sender, message) {
    let messages = document.getElementById('messages');
    let div = document.createElement('div');
    div.className = sender;
    div.textContent = message;
    messages.appendChild(div);
    div.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function showTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'block';
}

function hideTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'none';
}

function sendMessageToServer(message) {
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
  .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
  .then(data => {
        hideTypingIndicator(); // Hide indicator on success
        if (data.response) {
            displayMessage('bot', data.response);
        } else if (data.error) {
            displayMessage('bot', 'Oops, something went wrong!');
        }
    })
  .catch(error => {
        hideTypingIndicator(); // Hide indicator on error
        console.error('Error:', error);
        displayMessage('bot', 'Sorry, there was an error. Please try again.');
    });
}