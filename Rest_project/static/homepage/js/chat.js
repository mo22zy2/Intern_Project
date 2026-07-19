(function () {
    'use strict';

    var API_URL = window.CHAT_API_URL || '/api/v1/nlp/index/answer/1';

    var toggle = document.getElementById('chat-toggle');
    var panel = document.getElementById('chat-panel');
    var minimize = document.getElementById('chat-minimize');
    var messages = document.getElementById('chat-messages');
    var input = document.getElementById('chat-input');
    var sendBtn = document.getElementById('chat-send');
    var typing = document.getElementById('chat-typing');

    var isOpen = false;

    function scrollBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function addMessage(text, role) {
        var div = document.createElement('div');
        div.className = 'chat-msg ' + role;
        div.textContent = text;
        messages.insertBefore(div, typing);
        scrollBottom();
    }

    function showTyping() {
        typing.style.display = 'flex';
        scrollBottom();
    }

    function hideTyping() {
        typing.style.display = 'none';
    }

    function toggleChat() {
        isOpen = !isOpen;
        toggle.classList.toggle('open', isOpen);
        panel.classList.toggle('hidden', !isOpen);
        if (isOpen) {
            input.focus();
            scrollBottom();
        }
    }

    function openChat() {
        if (!isOpen) toggleChat();
    }

    function sendMessage() {
        var text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';
        sendBtn.disabled = true;
        showTyping();

        fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, limit: 5 })
        })
        .then(function (r) {
            if (!r.ok) throw new Error('Server error');
            return r.json();
        })
        .then(function (data) {
            hideTyping();
            var reply = data.reply || data.response || data.answer || JSON.stringify(data);
            addMessage(reply, 'bot');
        })
        .catch(function (err) {
            hideTyping();
            addMessage('Sorry, something went wrong. Please try again.', 'error');
            console.error('Chat API error:', err);
        })
        .finally(function () {
            sendBtn.disabled = false;
        });
    }

    /* ---- Event listeners ---- */

    if (toggle) toggle.addEventListener('click', toggleChat);
    if (minimize) minimize.addEventListener('click', toggleChat);
    if (sendBtn) sendBtn.addEventListener('click', sendMessage);

    if (input) {
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    /* ---- Open on incoming event (optional) ---- */
    window.openChat = openChat;

    /* ---- Initial bot greeting ---- */
    setTimeout(function () {
        addMessage('Hi there! How can I help you today?', 'bot');
    }, 600);

})();
