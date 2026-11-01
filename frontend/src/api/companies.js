import { dbApi } from './clients.js'
import api from './clients.js'

export const companyAPI = {
  search: keyword => dbApi.get('/search', { params: { q: keyword } }),
  getByCity: city => dbApi.get(`/city/${city}`),
  getByJob: job => dbApi.get(`/job/${job}`),
  aiSearch: params => dbApi.post('/ai-search', params),
  getStats: () => dbApi.get('/companies/stats')
}

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
