export interface ToolCall {
  tool_name: string;
  endpoint: string;
  method: string;
  request_data: any;
  response_status: number | null;
  response_data: any;
  error: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
  tool_calls?: ToolCall[];
}

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  tool_calls: ToolCall[];
}