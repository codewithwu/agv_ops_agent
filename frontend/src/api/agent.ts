/**
 * 智能体问答 API 调用
 */

import axiosInstance from './axios';

/** 对话请求 */
export interface ChatRequest {
  message: string;
  session_id?: string;
  llm_provider?: 'openai' | 'ollama';
}

/** 对话响应 */
export interface ChatResponse {
  message: string;
  session_id: string;
  messages: { role: string; content: string }[];
}

/**
 * 发送对话消息
 */
export const chat = async (data: ChatRequest): Promise<ChatResponse> => {
  const response = await axiosInstance.post<ChatResponse>('/agent/chat', data);
  return response.data;
};

/**
 * 流式对话（返回 ReadableStream）
 */
export const chatStream = (
  data: ChatRequest,
  onMessage: (content: string) => void,
  onError?: (error: Error) => void,
  onDone?: (fullContent: string) => void,
): () => void => {
  const token = localStorage.getItem('access_token');
  let cancelled = false;
  let fullContent = '';

  console.log('[chatStream] 开始请求, data:', data);

  fetch('http://localhost:8000/api/v1/agent/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify(data),
  })
    .then(response => {
      console.log('[chatStream] 收到响应, status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      function read() {
        if (cancelled || !reader) return;
        reader.read().then(({ done, value }) => {
          if (done || cancelled) {
            console.log('[chatStream] 流结束, fullContent length:', fullContent.length);
            if (!cancelled && onDone) onDone(fullContent);
            return;
          }
          const chunk = decoder.decode(value, { stream: true });
          console.log('[chatStream] 收到 chunk:', chunk.length, 'chars');
          fullContent += chunk;
          onMessage(chunk);
          read();
        });
      }

      read();
    })
    .catch(error => {
      console.error('[chatStream] 请求失败:', error);
      if (!cancelled && onError) {
        onError(error);
      }
    });

  // 返回取消函数
  return () => {
    cancelled = true;
  };
};