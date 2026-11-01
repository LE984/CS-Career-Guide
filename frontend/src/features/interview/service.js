/**
 * Interview application port. Implementations own prompts and wire protocols;
 * callers own UI state, timers and media playback.
 *
 * start/answer/generateReview accept a context object and an async onEvent
 * callback. Events retain {type, content?, session_id?, audio?, message?}.
 * generateReview returns {content, skipped}; saveReview/transcribe return the
 * existing API payload. Dependencies are supplied at the composition root.
 */
export function createInterviewService(implementation) {
  const operations = ['start', 'answer', 'generateReview', 'saveReview', 'transcribe']
  for (const operation of operations) {
    if (typeof implementation?.[operation] !== 'function') {
      throw new TypeError(`Interview implementation must provide ${operation}`)
    }
  }
  return Object.freeze(Object.fromEntries(operations.map(operation => [
    operation, (...args) => implementation[operation](...args)
  ])))
}
