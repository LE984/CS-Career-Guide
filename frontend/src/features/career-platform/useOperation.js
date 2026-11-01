import { ref,onUnmounted } from 'vue'
import { platformFailure } from './api.js'
export function useOperation() {
  const busy=ref(false),status=ref('功能待实现。当前仅提供开发骨架。')
  const controller=new AbortController()
  async function run(operation) {
    if(busy.value) return
    busy.value=true
    try { await operation(controller.signal); if(!controller.signal.aborted)status.value='接口已有响应，业务结果展示尚待本模块完成验收。' }
    catch(error) { if(!controller.signal.aborted)status.value=platformFailure(error) }
    finally { if(!controller.signal.aborted)busy.value=false }
  }
  onUnmounted(()=>controller.abort())
  return {busy,status,run}
}
