window.socket = window.socket || null;
window.currentRoomId = window.currentRoomId || null;
window.messageQueue = window.messageQueue || [];


// Generate simple unique ID
function generateTempId() {
  return "temp-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
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


  // const div = document.createElement("div");
  // div.classList.add("mb-2");

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
      messageQueue.push(content, tempId);   // 🆕 queue it
    } else {
      socket.send(JSON.stringify({ content, tempId }));
    }

    input.value = "";
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
        status: "sent"
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