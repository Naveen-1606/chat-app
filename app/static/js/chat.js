window.socket = window.socket || null;
window.currentRoomId = window.currentRoomId || null;
window.messageQueue = window.messageQueue || [];
window.typingTimer = window.typingTimer || null;
window.isTyping = window.isTyping || false;
window.TYPING_IDLE_MS = window.TYPING_IDLE_MS || 2000; // stop after 2s idle


// Generate simple unique ID
function generateTempId() {
  return "temp-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
}

function sendTyping(status) {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;
  socket.send(JSON.stringify({ type: "typing", status }));
}

// -----------------------------
// Load room via HTMX + WebSocket
// -----------------------------
function loadRoom(roomId) {
    // 1. Fetch chat area via HTMX
    htmx.ajax('GET', `/chat/rooms/${roomId}`, { target: '#chat-container', swap: 'innerHTML' });
    
    // 2. Connect WebSocket after a slight delay to ensure HTML is swapped
    setTimeout(() => connectWebSocket(roomId), 100);
}

// --------------------------
// Render a single message
// --------------------------
function renderMessage({ sender, content = "", timestamp = null, type = "chat_message", message = "", tempId = null, id = null, status = null }) {
  const chatMessages = document.getElementById("chat-messages");
  if (!chatMessages) return;

  let div = null;
  if (tempId) {
    // Look for existing pending message
    div = chatMessages.querySelector(`[data-temp-id="${tempId}"]`);
  }

  if (!div) {
    div = document.createElement("div");
    div.classList.add("mb-2");
    if (tempId) div.dataset.tempId = tempId;
    if (id) div.dataset.messageId = id;
    chatMessages.appendChild(div);
  }

  if (type === "system") {
    div.innerHTML = `<em class="text-gray-500">${message} ${timestamp ? '(' + new Date(timestamp).toLocaleTimeString() + ')' : ''}</em>`;
  } else if (type === "chat_message") {
    let label = sender === window.currentUsername ? "You" : sender;

    let statusText = "";
    if (label === "You" && status) {
      statusText = ` <small class="text-gray-400">(${status})</small>`;
    }

    div.innerHTML = `
      <strong>${label}:</strong> ${content}
      <small class="text-gray-500 text-xs">${timestamp ? new Date(timestamp).toLocaleString() : ""}</small>
      ${statusText}
    `;
  }

  // chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// --------------------------
// Attach send message handler, queue the message if web socket is not connected
// --------------------------
function attachMessageFormHandler() {
  const form = document.getElementById("message-form");
  const input = document.getElementById("message-input");

  if (!form || !input) return;

  form.onsubmit = (e) => {
    e.preventDefault();
    const content = input.value.trim();
    if (content === "") return;

    const tempId = generateTempId();

    // Render immediately as pending
    renderMessage({
      sender: "You",
      content,
      timestamp: new Date().toISOString(),
      tempId,
      status: "pending"
    });

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.warn("⚠️ Socket not ready, queueing message:", content);
      messageQueue.push({ content, tempId });   // 🆕 queue it
    } else {
      socket.send(JSON.stringify({ content, tempId }));
    }

    input.value = "";
    // after sending, consider typing stopped
    if (isTyping) {
      isTyping = false;
      sendTyping("stop");
      clearTimeout(typingTimer);
    }
  };
  // TYPING indicator: start on input, stop after idle
  input.oninput = () => {
    if (!isTyping) {
      isTyping = true;
      sendTyping("start");
    }
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
      if (isTyping) {
        isTyping = false;
        sendTyping("stop");
      }
    }, TYPING_IDLE_MS);
  };
}


// --------------------------
// Connect to WebSocket
// --------------------------
function connectWebSocket(roomId) {
  // Close old connection
  if (socket) {
    socket.onclose = null; // detach old onclose
    socket.close();
    socket = null;
  }

  currentRoomId = roomId;


  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomId}`;
  socket = new WebSocket(wsUrl);

  const chatMessages = document.getElementById("chat-messages");

  socket.onopen = () => {
    console.log(`✅ Connected to room ${roomId}`);
    if (chatMessages) chatMessages.innerHTML = "";
    attachMessageFormHandler();

    // 🆕 Flush queued messages
    while (messageQueue.length > 0) {
        const {msg, tempId} = messageQueue.shift();
        console.log("📤 Sending queued:", msg);
        socket.send(JSON.stringify({ content: msg, tempId }));
    }
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "history") {
        // Clear messages before rendering history
        if (chatMessages) chatMessages.innerHTML = "";
        data.messages.forEach(m => renderMessage({
            type: "chat_message",
            sender: m.sender,
            content: m.content,
            timestamp: m.timestamp,
            status: "sent",
            id: m.id,
        }));
    } else if (data.type === "error") {
        alert(data.message);

    } else if (data.type === "chat_message") {
        if (data.tempId) {
            // 🆕 Update pending bubble instead of creating new
            const pending = chatMessages.querySelector(`[data-temp-id="${data.tempId}"]`);
            if (pending) {
                pending.innerHTML = `
                  <strong>You:</strong> ${data.content}
                  <small class="text-gray-500 text-xs">${new Date(data.timestamp).toLocaleString()}</small>
                  <small class="text-gray-400">(sent)</small>
                  <div class="message-status text-xs text-gray-500 mt-1"></div>
                `;
                pending.dataset.messageId = data.id; // store real id now
                delete pending.dataset.tempId;
            } else {
                // fallback (in case div not found)
                renderMessage({ ...data, sender: "You", status: "sent" });
            }
        } else {
            // 🆕 Only render others’ messages
            if (data.sender === window.currentUsername) {
                // skip (already updated local bubble)
                return;
            }
            // Normal message from others
            renderMessage({ ...data, status: "sent" });

            // 🆕 If this message is from another user, send "seen" event
            if (data.sender !== window.currentUsername) {
                socket.send(JSON.stringify({
                    type: "seen",
                    message_id: data.id
                }));
            }
        }

    } else if (data.type === "seen_update") {
        // 🆕 Update sender’s UI with "seen" info
        const msgElement = chatMessages.querySelector(`[data-message-id="${data.message_id}"]`);
        if (msgElement) {
            let statusEl = msgElement.querySelector(".message-status");
            if (!statusEl) {
                statusEl = document.createElement("div");
                statusEl.classList.add("message-status", "text-xs", "text-gray-500", "mt-1");
                msgElement.appendChild(statusEl);
            }
            statusEl.textContent = `Seen by ${data.seen_by} at ${new Date(data.seen_at).toLocaleTimeString()}`;
        }

    } else if (data.type === "typing_update") {
        const you = window.currentUsername;
        const others = (data.users || []).filter(u => u !== you);

        const el = document.getElementById("typing-indicator");
        if (!el) return;

        if (others.length === 0) {
          el.textContent = "";
          el.classList.add("hidden");
        } else if (others.length === 1) {
          el.textContent = `${others[0]} is typing…`;
          el.classList.remove("hidden");
        } else if (others.length === 2) {
          el.textContent = `${others[0]} and ${others[1]} are typing…`;
          el.classList.remove("hidden");
        } else {
          el.textContent = `Several people are typing…`;
          el.classList.remove("hidden");
        }
    } else {
        renderMessage(data);
    }
};



  socket.onclose = () => {
    console.log(`❌ Disconnected from room ${roomId}`); socket = null; };

  socket.onerror = (err) => console.error("WebSocket error:", err);
}

// --------------------------
// Re-bind form after HTMX swaps
// --------------------------
document.body.addEventListener("htmx:afterSwap", () => {
  attachMessageFormHandler();
});

// --------------------------
// Expose globally for HTMX partials
// --------------------------
window.connectWebSocket = connectWebSocket;

// --------------------------
// Bind initially in case form already exists
// --------------------------
attachMessageFormHandler();