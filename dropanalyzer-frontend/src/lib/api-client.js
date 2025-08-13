
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const login = async (username, password) => {
  try {
    const response = await apiClient.post('/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("isAuthenticated", "true");
      apiClient.defaults.headers.common["Authorization"] = `Bearer ${response.data.access_token}`;
    }
    return response.data;
  } catch (error) {
    console.error('Login error:', error.response?.data || error.message);
    throw error;
  }
};

export const getDashboardStats = async () => {
  try {
    const response = await apiClient.get('/dashboard');
    return response.data;
  } catch (error) {
    console.error('Dashboard stats error:', error.response?.data || error.message);
    throw error;
  }
};

export const getReports = async () => {
  try {
    const response = await apiClient.get('/reports');
    return response.data;
  } catch (error) {
    console.error('Reports error:', error.response?.data || error.message);
    throw error;
  }
};

export const analyzeDomain = async (domain) => {
  try {
    const response = await apiClient.post('/analyze_domain', { domain });
    return response.data;
  } catch (error) {
    console.error('Analyze domain error:', error.response?.data || error.message);
    throw error;
  }
};

export default apiClient;
