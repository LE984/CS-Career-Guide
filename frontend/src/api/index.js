// Compatibility barrel: existing views can keep importing from '@/api' while
// the new frontend consumes one business-domain module at a time.
export { default, apiFetch } from './clients.js'
export { authAPI } from './auth.js'
export { userAPI } from './users.js'
export { resumeAPI } from './resumes.js'
export { interviewAPI, aiAPI } from './interview.js'
export { companyAPI, jobFairAPI, companyInfoAPI, computerCareerAPI } from './companies.js'
