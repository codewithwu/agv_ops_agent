/**
 * Zustand 认证状态 Store
 * 使用 localStorage 持久化存储 Token
 */

import { create } from 'zustand';
import type { UserInfo } from '../types/auth';

interface AuthTokens {
  accessToken: string | null;
  refreshToken: string | null;
}

interface AuthState {
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  user: UserInfo | null;
}

interface AuthActions {
  setAuth: (tokens: AuthTokens, user?: UserInfo) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: UserInfo) => void;
  clearAuth: () => void;
}

// 从 localStorage 获取 Token
const getStoredTokens = (): AuthTokens => {
  try {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    return {
      accessToken,
      refreshToken,
    };
  } catch {
    return { accessToken: null, refreshToken: null };
  }
};

// 导出获取 Token 的函数供 axios.ts 使用
export const getAuthTokens = (): AuthTokens => getStoredTokens();

export const useAuthStore = create<AuthState & AuthActions>((set) => ({
  // 初始状态：从 localStorage 恢复
  ...getStoredTokens(),
  isAuthenticated: !!getStoredTokens().accessToken,
  user: null,

  setAuth: (tokens: AuthTokens, user?: UserInfo) => {
    // 存储到 localStorage
    if (tokens.accessToken) {
      localStorage.setItem('access_token', tokens.accessToken);
    }
    if (tokens.refreshToken) {
      localStorage.setItem('refresh_token', tokens.refreshToken);
    }

    set({
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      isAuthenticated: !!tokens.accessToken,
      user: user || null,
    });
  },

  setAccessToken: (token: string) => {
    localStorage.setItem('access_token', token);
    set({ accessToken: token, isAuthenticated: true });
  },

  setUser: (user: UserInfo) => {
    set({ user });
  },

  clearAuth: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      user: null,
    });
  },
}));

// 导出清除 Token 的函数供 axios.ts 使用
export const clearAuthTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};
