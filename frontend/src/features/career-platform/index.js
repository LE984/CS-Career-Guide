import client from '@/api'
import { createPlatformAPI } from './api.js'
export const platformAPI = createPlatformAPI(client)
