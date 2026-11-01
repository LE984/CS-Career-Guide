import axios from 'axios'
import { API_BASE_URL, COMPANY_API_BASE_URL, API_TIMEOUT, COMPANY_API_TIMEOUT, apiUrl } from '../config'
import { createApiFetch, installAuthInterceptors } from './transport.js'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

const dbApi = axios.create({
  baseURL: COMPANY_API_BASE_URL,
  timeout: COMPANY_API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

installAuthInterceptors(api)
installAuthInterceptors(dbApi)

export const apiFetch = createApiFetch(apiUrl)

export const authAPI = {
  login: (data) => api.post('/users/auth/login/', data, { publicAuth: true }),
  register: (data) => api.post('/users/auth/register/', data, { publicAuth: true }),
  logout: () => api.post('/users/auth/logout/')
}

export const userAPI = {
  getProfile: (config) => api.get('/users/profile/', config),
  updateProfile: (data) => api.put('/users/profile/', data),
  uploadAvatar: (formData) => api.post('/users/profile/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// Shared by the editing workspace and personal center; paths match Django's routers.
export const resumeAPI = {
  get: (config) => api.get('/resumes/my/', config),
  save: (data) => api.post('/resumes/my/', data),
  uploadAvatar: (formData) => api.post('/resumes/upload_avatar/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteAvatar: () => api.delete('/resumes/delete_avatar/')
}

export const interviewAPI = {
  listReviews: () => api.get('/ai/records/interview-reviews/'),
  getReview: (sessionId) => api.get(`/ai/records/interview-reviews/${encodeURIComponent(sessionId)}/`),
  saveReview: (data) => api.post('/ai/interview/save_review/', data),
  transcribe: (formData) => api.post('/asr/speech-to-text/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const aiAPI = {
  chat: (message, mode, interview_style, session_id) => api.post('/ai/llm/chat/', { message, mode, interview_style, session_id }),
  chatStream: (message, mode, interview_style, session_id, options = {}) => {
    return apiFetch('/ai/llm/chat/', {
      method: 'POST',
      signal: options.signal,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message, mode, interview_style, session_id, enable_tts: options.enableTts === true })
    })
  },
  getHistory: (sessionId) => api.get(`/ai/llm/chat/history/?session_id=${sessionId}`),
  careerRecommendation: (self_introduction) => api.post('/ai/llm/career/recommendation/', { self_introduction }),
  careerPlanGeneration: (self_introduction, selected_careers) => api.post('/ai/llm/career/plan/', { self_introduction, selected_careers }),
  careerReport: (user_profile, target_job) => api.post('/career-report/', { user_profile, target_job }),
  saveChatRecord: (session_id, user_message, assistant_message, mode) => api.post('/ai/llm/save-chat/', { session_id, user_message, assistant_message, mode }),
  saveCareerEvaluation: (session_id, selected_careers, evaluation_result) => api.post('/ai/records/save-evaluation/', { session_id, selected_careers, evaluation_result }),
  saveCareerPlan: (session_id, report_content, radar_data) => api.post('/ai/records/save-plan/', { session_id, report_content, radar_data }),
  saveCareerRecommendation: (session_id, self_introduction, recommendations) => api.post('/ai/records/save-recommendation/', { session_id, self_introduction, recommendations })
}

export const companyAPI = {
  search: (keyword) => dbApi.get('/search', { params: { q: keyword } }),
  getByCity: (city) => dbApi.get(`/city/${city}`),
  getByJob: (job) => dbApi.get(`/job/${job}`),
  aiSearch: (params) => dbApi.post('/ai-search', params),
  getStats: () => dbApi.get('/companies/stats')
}

export default api

export const jobFairAPI = {
  getJobFairs: (page = 1, pageSize = 8) => api.get('/company-reviews/job-fairs/', {
    params: { page, page_size: pageSize }
  }),
  getFilterOptions: () => api.get('/company-reviews/job-fairs/filter_options/')
}

export const companyInfoAPI = {
  getCompanyInfos: (page = 1, pageSize = 10) => api.get('/company-reviews/company-info/', {
    params: { page, page_size: pageSize }
  })
}

export const computerCareerAPI = {
  getComputerCareers: (page = 1, pageSize = 10) => api.get('/career-evaluation/computer-careers/', {
    params: { page, page_size: pageSize }
  })
}
