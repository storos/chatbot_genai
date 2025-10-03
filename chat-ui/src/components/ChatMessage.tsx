import React, { useState } from 'react';
import { ChatMessage } from '../types/chat';
import { User, Bot, ExternalLink, Settings, ChevronDown, ChevronRight } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessage;
}

export const ChatMessageComponent: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [showToolCalls, setShowToolCalls] = useState(false);
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={`flex gap-3 p-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-500' : 'bg-gray-500'
        }`}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`rounded-lg px-4 py-2 max-w-full ${
            isUser 
              ? 'bg-blue-500 text-white rounded-br-sm' 
              : 'bg-gray-100 text-gray-900 rounded-bl-sm'
          }`}>
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>

          {/* Tool Calls */}
          {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
            <div className="w-full mt-2">
              <button
                onClick={() => setShowToolCalls(!showToolCalls)}
                className="flex items-center gap-2 text-xs bg-blue-50 text-blue-700 px-3 py-2 rounded-lg hover:bg-blue-100 transition-colors"
              >
                <Settings className="w-3 h-3" />
                <span>Tool Calls ({message.tool_calls.length})</span>
                {showToolCalls ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
              </button>
              
              {showToolCalls && (
                <div className="mt-2 space-y-2">
                  {message.tool_calls.map((toolCall, index) => (
                    <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs">
                      <div className="font-semibold text-gray-800 mb-2">{toolCall.tool_name}</div>
                      
                      {/* Request Info */}
                      <div className="mb-2">
                        <div className="text-gray-600 font-medium">Request:</div>
                        <div className="text-blue-600">{toolCall.method} {toolCall.endpoint}</div>
                        <div className="bg-gray-100 rounded p-2 mt-1">
                          <pre className="text-gray-700 overflow-x-auto">
                            {JSON.stringify(toolCall.request_data, null, 2)}
                          </pre>
                        </div>
                      </div>
                      
                      {/* Response Info */}
                      <div className="mb-2">
                        <div className="text-gray-600 font-medium">Response:</div>
                        <div className={`font-medium ${
                          toolCall.response_status === 204 || toolCall.response_status === 200 
                            ? 'text-green-600' 
                            : 'text-red-600'
                        }`}>
                          Status: {toolCall.response_status}
                        </div>
                        {toolCall.response_data && (
                          <div className="bg-gray-100 rounded p-2 mt-1">
                            <pre className="text-gray-700 overflow-x-auto">
                              {typeof toolCall.response_data === 'string' 
                                ? toolCall.response_data 
                                : JSON.stringify(toolCall.response_data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                      
                      {/* Error Info */}
                      {toolCall.error && (
                        <div>
                          <div className="text-red-600 font-medium">Error:</div>
                          <div className="bg-red-50 text-red-700 rounded p-2 mt-1">
                            {toolCall.error}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Sources */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="w-full mt-2">
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-2 text-xs bg-green-50 text-green-700 px-3 py-2 rounded-lg hover:bg-green-100 transition-colors"
              >
                <ExternalLink className="w-3 h-3" />
                <span>Sources ({message.sources.length})</span>
                {showSources ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
              </button>
              
              {showSources && (
                <div className="mt-2 space-y-2">
                  {message.sources.map((source, index) => (
                    <div 
                      key={index} 
                      className="bg-green-50 border border-green-200 rounded-lg p-3 text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-3 h-3 text-green-600" />
                        <span className="font-medium text-green-800">{source}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Timestamp */}
          <span className="text-xs text-gray-500">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
};