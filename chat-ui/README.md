# Chat UI - React Frontend

A modern, responsive web interface for the AI Customer Support Chatbot built with React, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Real-time Chat Interface**: Intuitive messaging UI with conversation history
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **TypeScript Support**: Type-safe development with full TypeScript integration
- **Modern UI Components**: Clean, accessible interface with Tailwind CSS
- **Error Handling**: Graceful error states and connection status indicators
- **Session Management**: Persistent chat sessions with unique identifiers

## 🛠️ Tech Stack

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API communication
- **Lucide React**: Beautiful, customizable icons

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the Docker image
docker build -t chatbot-ui ./chat-ui

# Run the container
docker run -d --name chatbot-ui -p 3000:3000 chatbot-ui
```

### Environment Variables
Create a `.env` file:
```bash
VITE_CHAT_API_URL=http://localhost:8001
```

## 🔗 API Integration

The UI connects to the Chat API service. Make sure the Chat API is running on the specified URL (default: http://localhost:8001).

## 📱 Usage

1. Open the application in your browser at http://localhost:3000
2. Start typing in the input field at the bottom
3. Press Enter or click the send button to send messages
4. View conversation history in the main chat area
5. Use the clear button to reset the conversation

## 🎨 Customization

- Modify `src/components/` for UI components
- Update `tailwind.config.js` for styling
- Configure API endpoint in `.env` file
- Customize colors and branding in the components

Built with ❤️ using modern web technologies