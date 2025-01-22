document.addEventListener("DOMContentLoaded", () => {
    const chatbotIcon = document.getElementById("chatbot-icon");
    const chatbotWindow = document.getElementById("chatbot-window");
    const closeChatbot = document.getElementById("close-chatbot");
    const userInput = document.getElementById("user-input");
    const chatContent = document.getElementById("chat-content");
  
    // Open chatbot window
    chatbotIcon.addEventListener("click", () => {
      chatbotWindow.classList.toggle("hidden");
    });
  
    // Close chatbot window
    closeChatbot.addEventListener("click", () => {
      chatbotWindow.classList.add("hidden");
    });
  
    // Handle user input
    userInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && userInput.value.trim() !== "") {
        const userMessage = userInput.value;
        addMessage(userMessage, "user");
        userInput.value = "";
        setTimeout(() => addMessage("I'm still learning! 😊", "bot"), 1000);
      }
    });
  
    function addMessage(message, sender) {
      const messageDiv = document.createElement("div");
      messageDiv.classList.add(
        "p-2",
        "rounded-lg",
        "my-1",
        sender === "user" ? "bg-teal-100 text-right" : "bg-gray-200 text-left"
      );
      messageDiv.textContent = message;
      chatContent.appendChild(messageDiv);
      chatContent.scrollTop = chatContent.scrollHeight;
    }
  });
  