import api from './clients.js'

export const resumeAPI = {
  get: () => api.get('/resumes/my/'),
  save: data => api.post('/resumes/my/', data),
  uploadAvatar: formData => api.post('/resumes/upload_avatar/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteAvatar: () => api.delete('/resumes/delete_avatar/')
}
