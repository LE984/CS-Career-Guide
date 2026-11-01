import api from './clients.js'

export const authAPI = {
  login: data => api.post('/users/auth/login/', data, { publicAuth: true }),
  register: data => api.post('/users/auth/register/', data, { publicAuth: true }),
  logout: () => api.post('/users/auth/logout/')
}
