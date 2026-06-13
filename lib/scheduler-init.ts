import { getSchedulerService } from '@/lib/scheduler-service';

let initialized = false;

export function ensureSchedulerStarted() {
  if (initialized) return;
  initialized = true;

  try {
    const service = getSchedulerService();
    service.start();
  } catch (err) {
    console.error('[SchedulerInit] Failed to start:', err);
  }
}
