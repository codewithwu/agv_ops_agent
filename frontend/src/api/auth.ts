/**
 * 认证 API 调用
 */

import axiosInstance from './axios';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  ChangePasswordRequest,
  ChangePasswordResponse,
  UserInfo,
} from '../types/auth';

/**
 * 用户登录
 */
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await axiosInstance.post<LoginResponse>('/auth/login', data);
  return response.data;
};

/**
 * 用户注册
 */
export const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  const response = await axiosInstance.post<RegisterResponse>('/auth/register', data);
  return response.data;
};

/**
 * 刷新访问令牌
 */
export const refreshToken = async (data: RefreshTokenRequest): Promise<RefreshTokenResponse> => {
  const response = await axiosInstance.post<RefreshTokenResponse>('/auth/refresh', data);
  return response.data;
};

/**
 * 用户退出登录
 */
export const logout = async (): Promise<void> => {
  await axiosInstance.post('/auth/logout');
};

/**
 * 修改密码
 */
export const changePassword = async (data: ChangePasswordRequest): Promise<ChangePasswordResponse> => {
  const response = await axiosInstance.post<ChangePasswordResponse>('/auth/change-password', data);
  return response.data;
};

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<UserInfo> => {
  const response = await axiosInstance.get<UserInfo>('/auth/me');
  return response.data;
};
