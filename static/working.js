document.getElementById('send-button').addEventListener('click', sendMessage); // Simplified

document.getElementById('user-input').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent the default form submission (if inside a form)
        sendMessage();  // Call the sendMessage function
    }
});

function sendMessage() {
    let userInput = document.getElementById('user-input').value;
    if (userInput.trim() !== "") { // Check for non-empty input after trimming whitespace
        displayMessage('user', userInput);
        sendMessageToServer(userInput);
        document.getElementById('user-input').value = ''; // Clear the input
        document.getElementById('user-input').focus();  // Put the cursor focus back into the box

    }
}

function displayMessage(sender, message) {
    let messages = document.getElementById('messages');
    let div = document.createElement('div');
    div.className = sender;
    div.textContent = message;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight; // Scroll to the bottom
}

function sendMessageToServer(message) {
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            displayMessage('bot', data.response);
        } else if (data.error) {
            displayMessage('bot', 'Oops, something went wrong!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage('bot', 'Sorry, there was an error.');
    });
}