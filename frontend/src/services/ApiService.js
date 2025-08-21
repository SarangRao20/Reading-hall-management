import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => {
        return response.data;
      },
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error.response?.data || error;
      }
    );
  }

  // Analytics and Overview
  async getOverview() {
    return await this.api.get('/api/analytics/overview');
  }

  async getUsageAnalytics(days = 7) {
    return await this.api.get(`/api/analytics/usage?days=${days}`);
  }

  // User Management
  async getUsers() {
    return await this.api.get('/api/users');
  }

  async createUser(userData) {
    return await this.api.post('/api/users', userData);
  }

  async getUserByBarcode(barcode) {
    return await this.api.get(`/api/users/${barcode}`);
  }

  // Reading Halls and Seats
  async getHalls() {
    return await this.api.get('/api/halls');
  }

  async getHallSeats(hallId) {
    return await this.api.get(`/api/halls/${hallId}/seats`);
  }

  // Session Management
  async getActiveSessions() {
    return await this.api.get('/api/sessions/active');
  }

  async checkInUser(barcode, seatId) {
    return await this.api.post('/api/checkin', {
      barcode,
      seat_id: seatId
    });
  }

  async checkOutUser(barcode) {
    return await this.api.post('/api/checkout', {
      barcode
    });
  }

  // Computer Vision Integration
  async sendVisionDetection(detectionData) {
    return await this.api.post('/api/vision/detection', detectionData);
  }

  // Configuration
  async getConfigurations() {
    return await this.api.get('/api/config');
  }

  async updateConfiguration(key, value, description = '') {
    return await this.api.put('/api/config', {
      key,
      value,
      description
    });
  }

  // Utility methods for real-time updates
  startPolling(endpoint, callback, interval = 30000) {
    const poll = async () => {
      try {
        const data = await this.api.get(endpoint);
        callback(data);
      } catch (error) {
        console.error('Polling error:', error);
      }
    };

    // Initial call
    poll();

    // Set up interval
    const intervalId = setInterval(poll, interval);

    // Return cleanup function
    return () => clearInterval(intervalId);
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.api.get('/');
      return { status: 'ok', response };
    } catch (error) {
      return { status: 'error', error };
    }
  }
}

export default new ApiService();
