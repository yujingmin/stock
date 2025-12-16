/**
 * 认证相关 API 服务
 */
import { apiClient } from '../client';

// 类型定义
export interface RegisterRequest {
  username: string;
  phone: string;
  password: string;
  verification_code?: string;
}

export interface LoginRequest {
  phone: string;
  password?: string;
  verification_code?: string;
}

export interface SendCodeRequest {
  phone: string;
  purpose: 'register' | 'login' | 'reset_password';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: number;
  username: string;
}

export interface UserResponse {
  id: number;
  username: string;
  phone: string;
  nickname?: string;
  email?: string;
  avatar_url?: string;
  status: string;
  vip_level: number;
  vip_expire_at?: string;
  created_at: string;
  last_login_at?: string;
}

export interface UpdateProfileRequest {
  nickname?: string;
  email?: string;
  avatar_url?: string;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

// API 方法
export const authApi = {
  /**
   * 用户注册
   */
  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/register', data);
    return response.data;
  },

  /**
   * 用户登录
   */
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', data);
    return response.data;
  },

  /**
   * 发送验证码
   */
  sendCode: async (data: SendCodeRequest): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>('/auth/send-code', data);
    return response.data;
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>('/auth/me');
    return response.data;
  },

  /**
   * 更新用户信息
   */
  updateProfile: async (data: UpdateProfileRequest): Promise<UserResponse> => {
    const response = await apiClient.put<UserResponse>('/auth/me', data);
    return response.data;
  },

  /**
   * 登出
   */
  logout: async (): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>('/auth/logout');
    return response.data;
  },
};

export default authApi;
