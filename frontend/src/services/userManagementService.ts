import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  roles: string[];
  isActive: boolean;
  emailVerified: boolean;
  phoneVerified: boolean;
  lastLogin?: string;
  createdAt: string;
}

interface CreateUserData {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  roles: string[];
  password?: string;
}

interface UpdateUserData {
  firstName?: string;
  lastName?: string;
  phone?: string;
  roles?: string[];
  isActive?: boolean;
  email?: string;
}

interface PasswordResetRequest {
  email: string;
}

interface PasswordReset {
  code: string;
  newPassword: string;
}

export const userManagementService = {
  /**
   * Get all users (Admin only)
   */
  getAllUsers: async (): Promise<User[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch users');
    }
  },

  /**
   * Get user by ID (Admin or self)
   */
  getUserById: async (userId: string): Promise<User> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/${userId}/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch user');
    }
  },

  /**
   * Create new user (Admin only)
   */
  createUser: async (userData: CreateUserData): Promise<User> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/users/`, userData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to create user');
    }
  },

  /**
   * Update user data (Admin or self)
   */
  updateUser: async (userId: string, userData: UpdateUserData): Promise<User> => {
    try {
      const response = await axios.patch(`${API_BASE_URL}/users/${userId}/`, userData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update user');
    }
  },

  /**
   * Update user roles (Admin only)
   */
  updateUserRoles: async (userId: string, roles: string[]): Promise<User> => {
    try {
      const response = await axios.patch(
        `${API_BASE_URL}/users/${userId}/`,
        { roles },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update user roles');
    }
  },

  /**
   * Update user email (Admin or self)
   */
  updateUserEmail: async (userId: string, newEmail: string): Promise<User> => {
    try {
      const response = await axios.patch(
        `${API_BASE_URL}/users/${userId}/`,
        { email: newEmail },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update email');
    }
  },

  /**
   * Update user phone (Admin or self)
   */
  updateUserPhone: async (userId: string, newPhone: string): Promise<User> => {
    try {
      const response = await axios.patch(
        `${API_BASE_URL}/users/${userId}/`,
        { phone: newPhone },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update phone');
    }
  },

  /**
   * Delete user (Admin only)
   */
  deleteUser: async (userId: string): Promise<void> => {
    try {
      await axios.delete(`${API_BASE_URL}/users/${userId}/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete user');
    }
  },

  /**
   * Deactivate user (Admin only)
   */
  deactivateUser: async (userId: string): Promise<User> => {
    try {
      const response = await axios.patch(
        `${API_BASE_URL}/users/${userId}/`,
        { isActive: false },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to deactivate user');
    }
  },

  /**
   * Activate user (Admin only)
   */
  activateUser: async (userId: string): Promise<User> => {
    try {
      const response = await axios.patch(
        `${API_BASE_URL}/users/${userId}/`,
        { isActive: true },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to activate user');
    }
  },

  /**
   * Send password reset email
   */
  sendPasswordResetEmail: async (email: string): Promise<{ message: string }> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/users/password-reset-request/`, {
        email,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to send reset email');
    }
  },

  /**
   * Reset password with code
   */
  resetPassword: async (data: PasswordReset): Promise<{ message: string }> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/users/password-reset/`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to reset password');
    }
  },

  /**
   * Admin sends password reset for another user
   */
  adminResetUserPassword: async (userId: string): Promise<{ tempPassword: string }> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/reset-password/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to reset user password');
    }
  },

  /**
   * Get user sessions
   */
  getUserSessions: async (userId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/${userId}/sessions/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch sessions');
    }
  },

  /**
   * Terminate user session
   */
  terminateSession: async (userId: string, sessionId: string): Promise<void> => {
    try {
      await axios.delete(`${API_BASE_URL}/users/${userId}/sessions/${sessionId}/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
    } catch (error) {
      throw new Error('Failed to terminate session');
    }
  },

  /**
   * Search users
   */
  searchUsers: async (query: string): Promise<User[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/search/`, {
        params: { q: query },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to search users');
    }
  },

  /**
   * Get user statistics (Admin only)
   */
  getUserStats: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/stats/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch user statistics');
    }
  },

  /**
   * Verify user email
   */
  verifyEmail: async (userId: string, code: string): Promise<{ message: string }> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/verify-email/`,
        { code },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to verify email');
    }
  },

  /**
   * Request email verification code
   */
  requestEmailVerification: async (userId: string): Promise<{ message: string }> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/request-email-verification/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to request verification');
    }
  },

  /**
   * Verify phone number
   */
  verifyPhone: async (userId: string, code: string): Promise<{ message: string }> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/verify-phone/`,
        { code },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to verify phone');
    }
  },

  /**
   * Request phone verification code
   */
  requestPhoneVerification: async (userId: string): Promise<{ message: string }> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/users/${userId}/request-phone-verification/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to request phone verification');
    }
  },

  /**
   * Export users to CSV
   */
  exportUsers: async (format: 'csv' | 'excel' = 'csv'): Promise<Blob> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/export/`, {
        params: { format },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to export users');
    }
  },

  /**
   * Bulk update user roles
   */
  bulkUpdateRoles: async (updates: Array<{ userId: string; roles: string[] }>): Promise<void> => {
    try {
      await axios.post(`${API_BASE_URL}/users/bulk-update/`, { updates }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to bulk update users');
    }
  },
};

export default userManagementService;
