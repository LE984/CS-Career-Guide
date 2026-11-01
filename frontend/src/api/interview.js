import api, { apiFetch } from './clients.js'

export const interviewAPI = {
  listReviews: () => api.get('/ai/records/interview-reviews/'),
  getReview: sessionId => api.get(`/ai/records/interview-reviews/${encodeURIComponent(sessionId)}/`),
  saveReview: data => api.post('/ai/interview/save_review/', data),
  transcribe: formData => api.post('/asr/speech-to-text/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const aiAPI = {
  chat: (message, mode, interview_style, session_id) => api.post('/ai/llm/chat/', { message, mode, interview_style, session_id }),
  chatStream: (message, mode, interview_style, session_id) => apiFetch('/ai/llm/chat/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, mode, interview_style, session_id })
  }),
  getHistory: sessionId => api.get(`/ai/llm/chat/history/?session_id=${sessionId}`),
  careerRecommendation: self_introduction => api.post('/ai/llm/career/recommendation/', { self_introduction }),
  careerPlanGeneration: (self_introduction, selected_careers) => api.post('/ai/llm/career/plan/', { self_introduction, selected_careers }),
  careerReport: (user_profile, target_job) => api.post('/career-report/', { user_profile, target_job }),
  saveChatRecord: (session_id, user_message, assistant_message, mode) => api.post('/ai/llm/save-chat/', { session_id, user_message, assistant_message, mode }),
  saveCareerEvaluation: (session_id, selected_careers, evaluation_result) => api.post('/ai/records/save-evaluation/', { session_id, selected_careers, evaluation_result }),
  saveCareerPlan: (session_id, report_content, radar_data) => api.post('/ai/records/save-plan/', { session_id, report_content, radar_data }),
  saveCareerRecommendation: (session_id, self_introduction, recommendations) => api.post('/ai/records/save-recommendation/', { session_id, self_introduction, recommendations })
}
