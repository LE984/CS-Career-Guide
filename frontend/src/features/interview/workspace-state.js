// Same-tab navigation recovery only. No private conversation is written to disk.
let saved = null
export function saveInterviewWorkspace(owner, state) {
  if (!owner) return
  saved = { owner, state: structuredClone(state) }
}
export function restoreInterviewWorkspace(owner) {
  if (!owner || saved?.owner !== owner) { saved = null; return null }
  return structuredClone(saved.state)
}
export function clearInterviewWorkspace() { saved = null }

export function createConversationFollow() {
  let following = true
  return {
    interrupt: () => { following = false },
    resume: () => { following = true },
    track: element => { following = element.scrollHeight - element.clientHeight - element.scrollTop < 16 },
    get following() { return following },
  }
}
