import api from './clients.js'

export const userAPI = {
  getProfile: config => api.get('/users/profile/', config),
  updateProfile: data => api.put('/users/profile/', data),
  uploadAvatar: formData => api.post('/users/profile/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
