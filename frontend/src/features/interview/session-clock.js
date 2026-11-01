export const INTERVIEW_DURATIONS = [15, 30, 45, 60]
export const DEFAULT_DURATION = 45
export function interviewDuration(value = DEFAULT_DURATION) {
  return INTERVIEW_DURATIONS.includes(Number(value)) ? Number(value) : DEFAULT_DURATION
}

// Wall-clock deltas survive throttled background tabs; pauses do not count.
export function createSessionClock(seconds, now = () => Date.now()) {
  let remaining = seconds * 1000, started = now(), paused = false
  const milliseconds = () => Math.max(0, remaining - (paused ? 0 : now() - started))
  return {
    remaining: () => Math.ceil(milliseconds() / 1000),
    pause() { if (!paused) { remaining = milliseconds(); paused = true } },
    resume() { if (paused) { started = now(); paused = false } },
  }
}
