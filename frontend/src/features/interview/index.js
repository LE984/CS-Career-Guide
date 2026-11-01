// Composition root: select the existing implementation here when replacing it.
import { aiAPI, interviewAPI } from '../../api/index.js'
import { createInterviewService } from './service.js'
import { LegacyInterviewImplementation } from './legacy/implementation.js'

export const interviewService = createInterviewService(new LegacyInterviewImplementation({
  chatStream: (...args) => aiAPI.chatStream(...args),
  saveReview: data => interviewAPI.saveReview(data),
  transcribe: data => interviewAPI.transcribe(data),
  readResume: () => localStorage.getItem('resume')
}))
