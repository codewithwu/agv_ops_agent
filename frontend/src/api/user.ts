/**
 * 用户管理 API 调用
 */

import axiosInstance from './axios';
import type { UserInfo } from '../types/auth';

/** 用户列表响应 */
export interface UserListResponse {
  total: number;
  users: UserInfo[];
}

/** 更新用户请求 */
export interface UpdateUserRequest {
  role?: string;
  is_active?: boolean;
}

/**
 * 获取用户列表
 */
export const listUsers = async (): Promise<UserListResponse> => {
  const response = await axiosInstance.get<UserListResponse>('/users');
  return response.data;
};

/**
 * 更新用户信息（仅 admin）
 */
export const updateUser = async (userId: number, data: UpdateUserRequest): Promise<UserInfo> => {
  const response = await axiosInstance.patch<UserInfo>(`/users/${userId}`, data);
  return response.data;
};
