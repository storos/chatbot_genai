import { useState } from 'react';
import { ChatHistory } from './components/ChatHistory';
import { ChatInput } from './components/ChatInput';
import { useChat } from './hooks/useChat';
import { getSessionId, resetSessionId } from './utils/sessionUtils';
import { RotateCcw, AlertCircle } from 'lucide-react';
import './index.css';

function App() {
  // Generate session ID that persists across page refreshes but resets on browser restart
  const [sessionId, setSessionId] = useState(() => getSessionId());
  
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat(sessionId);
  const [apiConnected, setApiConnected] = useState(true);

  const handleSendMessage = async (message: string) => {
    try {
      await sendMessage(message);
      setApiConnected(true);
    } catch (err) {
      setApiConnected(false);
    }
  };

  const handleClearChat = () => {
    clearMessages();
    const newSessionId = resetSessionId();
    setSessionId(newSessionId);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Customer Support Chat</h1>
              <p className="text-sm text-gray-500">
                Session: {sessionId}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Connection Status */}
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              apiConnected 
                ? 'bg-green-100 text-green-700' 
                : 'bg-red-100 text-red-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                apiConnected ? 'bg-green-500' : 'bg-red-500'
              }`} />
              {apiConnected ? 'Connected' : 'Disconnected'}
            </div>
            
            {/* Clear Chat Button */}
            <button
              onClick={handleClearChat}
              disabled={messages.length === 0}
              className="flex items-center gap-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear conversation history"
            >
              <RotateCcw className="w-4 h-4" />
              Clear
            </button>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-400 mr-3" />
            <div>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-h-0">
        <ChatHistory messages={messages} isLoading={isLoading} />
        <ChatInput 
          onSendMessage={handleSendMessage} 
          isLoading={isLoading}
          disabled={!apiConnected}
        />
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-6 py-2">
        <p className="text-xs text-gray-500 text-center">
          AI-Powered Customer Support • Built with React + FastAPI
        </p>
      </footer>
    </div>
  );
}

export default App;