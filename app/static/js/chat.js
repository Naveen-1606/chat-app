window.socket = window.socket || null;
window.currentRoomId = window.currentRoomId || null;


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
function renderMessage({ sender = "System", content = "", timestamp = null, type = "chat_message", message = "" }) {
  const chatMessages = document.getElementById("chat-messages");
  if (!chatMessages) return;

  const div = document.createElement("div");
  div.classList.add("mb-2");

  if (type === "system") {
    div.innerHTML = `<em class="text-gray-500">${message} ${timestamp ? '(' + new Date(timestamp).toLocaleTimeString() + ')' : ''}</em>`;
  } else if (type === "chat_message") {
    div.innerHTML = `
      <strong>${sender}:</strong> ${content}
      <small class="text-gray-500 text-xs">${timestamp ? new Date(timestamp).toLocaleString() : ""}</small>
    `;
  }

  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// --------------------------
// Attach send message handler
// --------------------------
function attachMessageFormHandler() {
  const form = document.getElementById("message-form");
  const input = document.getElementById("message-input");

  if (!form || !input) return;

  // Clear previous handler to avoid duplicates
  form.onsubmit = (e) => {
    e.preventDefault();
    if (!socket) {
      console.warn("WebSocket not connected yet");
      return;
    }
    const content = input.value.trim();
    if (content !== "") {
      socket.send(JSON.stringify({ content }));
      input.value = "";
    }
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
    // const chatMessages = document.getElementById("chat-messages");
    if (chatMessages) chatMessages.innerHTML = "";
    attachMessageFormHandler(); // Bind send handler
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
      }));
    } else if (data.type === "error") {
      alert(data.message);
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
