document.getElementById('send-button').addEventListener('click', sendMessage);

document.getElementById('user-input').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent form submission
        sendMessage();
    }
});

function sendMessage() {
    let userInput = document.getElementById('user-input').value;
    if (userInput.trim() !== "") {
        displayMessage('user', userInput);
        sendMessageToServer(userInput);
        document.getElementById('user-input').value = '';
        document.getElementById('user-input').focus();
    }
}

function displayMessage(sender, message) {
    let messages = document.getElementById('messages');
    let div = document.createElement('div');
    div.className = sender;
    div.textContent = message;  // Use textContent for security

    messages.appendChild(div);
    // --- Smooth Scrolling (using scrollIntoView) ---
    div.scrollIntoView({ behavior: 'smooth', block: 'end' });
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
            throw new Error(`HTTP error! status: ${response.status}`); // Check for HTTP errors
        }
        return response.json();
    })
    .then(data => {
        if (data.response) {
            displayMessage('bot', data.response);
        } else if (data.error) {
            displayMessage('bot', 'Oops, something went wrong!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage('bot', 'Sorry, there was an error. Please try again.'); // User-friendly error
    });
}