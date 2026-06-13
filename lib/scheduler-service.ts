import cron, { ScheduledTask as CronJob } from 'node-cron';
import { getActiveTasks, incrementRunCount, resetDailyCounts } from '@/lib/scheduler';
import { getAgentById } from '@/lib/agents';
import {
  getConversationById,
  getLastConversationForAgent,
  createConversation,
  updateConversation,
} from '@/lib/conversations';
import { createMessage, getMessagesByConversationId } from '@/lib/messages';
import { AgentRuntime } from '@/modules/core/agent-runtime';
import { ChatCompletionMessage, ScheduledTask } from '@/types';

class SchedulerService {
  private jobs: Map<string, CronJob> = new Map();
  private started = false;
  private dailyResetJob: CronJob | null = null;

  start() {
    if (this.started) return;
    this.started = true;
    console.log('[Scheduler] Starting scheduler service...');

    const tasks = getActiveTasks();
    for (const task of tasks) {
      this.registerJob(task);
    }

    this.dailyResetJob = cron.schedule('0 0 * * *', () => {
      console.log('[Scheduler] Resetting daily run counts');
      resetDailyCounts();
    });

    console.log(`[Scheduler] Registered ${tasks.length} cron jobs`);
  }

  stop() {
    for (const [id, job] of this.jobs) {
      job.stop();
    }
    this.jobs.clear();
    this.dailyResetJob?.stop();
    this.dailyResetJob = null;
    this.started = false;
    console.log('[Scheduler] Stopped all jobs');
  }

  registerJob(task: ScheduledTask) {
    this.removeJob(task.id);

    if (!task.is_active) return;

    if (!cron.validate(task.cron_expr)) {
      console.error(`[Scheduler] Invalid cron expression for task ${task.id}: ${task.cron_expr}`);
      return;
    }

    const job = cron.schedule(task.cron_expr, () => {
      this.executeTask(task.id);
    });

    this.jobs.set(task.id, job);
    console.log(`[Scheduler] Registered job: ${task.id} (${task.cron_expr})`);
  }

  removeJob(taskId: string) {
    const job = this.jobs.get(taskId);
    if (job) {
      job.stop();
      this.jobs.delete(taskId);
    }
  }

  private async executeTask(taskId: string) {
    const tasks = getActiveTasks();
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    if (task.run_count_today >= task.daily_limit) {
      console.log(`[Scheduler] Task ${taskId} reached daily limit (${task.daily_limit})`);
      return;
    }

    const agent = getAgentById(task.agent_id);
    if (!agent) {
      console.error(`[Scheduler] Agent not found for task ${taskId}`);
      return;
    }

    console.log(`[Scheduler] Executing task: ${task.name} (agent: ${agent.name})`);

    try {
      let conversation = getLastConversationForAgent(task.agent_id, task.user_id);

      if (!conversation) {
        conversation = createConversation({
          agent_id: task.agent_id,
          user_id: task.user_id,
          title: task.name,
          source: 'scheduled',
        });
      } else {
        conversation = updateConversation(conversation.id, {}) || conversation;
      }

      createMessage({
        conversation_id: conversation.id,
        role: 'user',
        content: task.prompt,
      });

      const history = getMessagesByConversationId(conversation.id);
      const messages: ChatCompletionMessage[] = history.map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }));

      const runtime = new AgentRuntime();
      const ctx = {
        agentId: task.agent_id,
        userId: task.user_id,
        conversationId: conversation.id,
        messages,
        systemPrompt: agent.system_prompt || '',
        metadata: { model: agent.model },
      };

      const response = await runtime.processMessage(ctx);

      createMessage({
        conversation_id: conversation.id,
        role: 'assistant',
        content: response.content,
      });

      incrementRunCount(taskId);

      console.log(`[Scheduler] Task ${taskId} completed. Response length: ${response.content.length}`);

      this.sendPushNotification(task, agent.name, response.content);
    } catch (err) {
      console.error(`[Scheduler] Error executing task ${taskId}:`, err);
    }
  }

  private async sendPushNotification(task: ScheduledTask, agentName: string, content: string) {
    try {
      const { existsSync, readFileSync } = await import('fs');
      const pathMod = await import('path');
      const subsFile = pathMod.join(process.cwd(), 'data', 'push-subscriptions.json');

      if (!existsSync(subsFile)) return;

      const subs = JSON.parse(readFileSync(subsFile, 'utf-8'));
      const userSubs = subs.filter((s: any) => s.user_id === task.user_id);

      if (userSubs.length === 0) return;

      const webpush = await import('web-push');
      const vapidPublicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || '';
      const vapidPrivateKey = process.env.VAPID_PRIVATE_KEY || '';

      if (!vapidPublicKey || !vapidPrivateKey) return;

      webpush.default.setVapidDetails(
        `mailto:${process.env.VAPID_EMAIL || 'admin@example.com'}`,
        vapidPublicKey,
        vapidPrivateKey
      );

      const payload = JSON.stringify({
        title: agentName,
        body: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-192.png',
      });

      for (const sub of userSubs) {
        try {
          await webpush.default.sendNotification(
            { endpoint: sub.endpoint, keys: sub.keys, expirationTime: sub.expirationTime },
            payload
          );
        } catch (err: any) {
          if (err.statusCode === 410) {
            const filtered = subs.filter((s: any) => s.endpoint !== sub.endpoint);
            const { writeFileSync } = await import('fs');
            writeFileSync(subsFile, JSON.stringify(filtered, null, 2));
          }
        }
      }
    } catch (err) {
      console.error('[Scheduler] Push notification error:', err);
    }
  }
}

let instance: SchedulerService | null = null;

export function getSchedulerService(): SchedulerService {
  if (!instance) {
    instance = new SchedulerService();
  }
  return instance;
}
