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