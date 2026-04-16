/**
 * 认证相关 TypeScript 类型定义
 */

/** 登录请求 */
export interface LoginRequest {
  username: string;
  password: string;
}

/** 登录响应 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/** 注册请求 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

/** 注册响应 */
export interface RegisterResponse {
  id: number;
  username: string;
  email: string;
}

/** 刷新令牌请求 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/** 刷新令牌响应 */
export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

/** 修改密码响应 */
export interface ChangePasswordResponse {
  message: string;
}

/** 用户信息 */
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string | null;
}

/** 认证状态 */
export interface AuthState {
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  user: UserInfo | null;
}
