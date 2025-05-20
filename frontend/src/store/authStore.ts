import { create } from 'zustand';
import authService, { RegisterData, UserProfile } from '../services/authService';

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: false,
  error: null,

  login: async (email: string, password: string) => {
    try {
      set({ loading: true, error: null });
      const { access_token } = await authService.login(email, password);
      set({ token: access_token });
      const profile = await authService.getProfile(access_token);
      set({ user: profile, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Login failed', loading: false });
    }
  },

  register: async (data: RegisterData) => {
    try {
      set({ loading: true, error: null });
      await authService.register(data);
      set({ loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Registration failed', loading: false });
    }
  },

  logout: () => set({ user: null, token: null }),

  fetchProfile: async () => {
    const token = get().token;
    if (!token) return;
    try {
      const profile = await authService.getProfile(token);
      set({ user: profile });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch profile' });
    }
  }
}));

export default useAuthStore;
