/**
 * 用户认证 Store
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, type UserResponse, type LoginRequest, type RegisterRequest } from '../api/services/auth';

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  updateUser: (user: Partial<UserResponse>) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      /**
       * 用户登录
       */
      login: async (data: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(data);
          const { access_token, user_id, username } = response;

          // 保存 token
          localStorage.setItem('access_token', access_token);

          // 获取完整用户信息
          const userInfo = await authApi.getCurrentUser();

          set({
            token: access_token,
            user: userInfo,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || '登录失败',
            isLoading: false,
          });
          throw error;
        }
      },

      /**
       * 用户注册
       */
      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.register(data);
          const { access_token, user_id, username } = response;

          // 保存 token
          localStorage.setItem('access_token', access_token);

          // 获取完整用户信息
          const userInfo = await authApi.getCurrentUser();

          set({
            token: access_token,
            user: userInfo,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || '注册失败',
            isLoading: false,
          });
          throw error;
        }
      },

      /**
       * 用户登出
       */
      logout: async () => {
        try {
          await authApi.logout();
        } catch (error) {
          console.error('Logout API error:', error);
        } finally {
          localStorage.removeItem('access_token');
          set({
            token: null,
            user: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      /**
       * 获取当前用户信息
       */
      fetchCurrentUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true });
        try {
          const userInfo = await authApi.getCurrentUser();
          set({
            user: userInfo,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token 无效或过期
          localStorage.removeItem('access_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      /**
       * 更新用户信息
       */
      updateUser: (userData: Partial<UserResponse>) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }));
      },

      /**
       * 清除错误信息
       */
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        // user 不持久化，每次启动时重新获取
      }),
    }
  )
);
