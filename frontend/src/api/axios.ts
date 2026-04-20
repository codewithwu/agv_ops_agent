/**
 * Axios 实例配置
 * 包含请求/响应拦截器，自动附加 Token 和处理 401 刷新
 */

import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosError } from 'axios';
import { getAuthTokens, clearAuthTokens, useAuthStore } from '../store/authStore';

// 后端 API 地址
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 创建 Axios 实例
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：附加 Token
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const tokens = getAuthTokens();
    if (tokens?.accessToken) {
      config.headers.Authorization = `Bearer ${tokens.accessToken}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理 401 自动刷新 Token
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // 如果是 401 且未重试过，尝试刷新 Token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const tokens = getAuthTokens();
      if (tokens?.refreshToken) {
        try {
          // 调用刷新接口
          const response = await axios.post<{ access_token: string; expires_in: number }>(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: tokens.refreshToken }
          );

          // 更新存储的 access token
          const newAccessToken = response.data.access_token;
          useAuthStore.getState().setAccessToken(newAccessToken);

          // 重试原请求
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return axiosInstance(originalRequest);
        } catch (refreshError) {
          // 刷新失败，清除认证信息
          clearAuthTokens();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
