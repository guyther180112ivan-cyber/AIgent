/**
 * МОДУЛЬ: Skills (Навыки)
 *
 * Реализует систему навыков по спецификации Anthropic.
 * Каждый навык — это шаблон промпта с параметрами.
 */

import { AgentContext, AgentModuleInterface, Skill } from '@/types';
import { createServiceClient } from '@/modules/core/supabase/server';

export class SkillsModule implements AgentModuleInterface {
  name = 'skills';

  async onBeforeMessage(ctx: AgentContext): Promise<AgentContext> {
    try {
      const supabase = await createServiceClient();

      // Получаем навыки агента
      const { data: agentSkills } = await supabase
        .from('agent_skills')
        .select('config, skills(*)')
        .eq('agent_id', ctx.agentId);

      if (!agentSkills || agentSkills.length === 0) return ctx;

      const skillsBlock = agentSkills
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((item: any) => {
          const skills: Skill | null = item.skills;
          if (!skills) return '';
          return `### Навык: ${skills.name}\n${skills.description}\n${skills.prompt_template}`;
        })
        .filter(Boolean)
        .join('\n\n');

      if (skillsBlock) {
        return {
          ...ctx,
          systemPrompt: ctx.systemPrompt + `\n\n## Доступные навыки:\n${skillsBlock}`,
        };
      }
    } catch (err) {
      console.error('[SkillsModule] Ошибка:', err);
    }

    return ctx;
  }
}

/** Реестр встроенных навыков */
export const BUILT_IN_SKILLS: Omit<Skill, 'id' | 'created_at'>[] = [
  {
    name: 'Web Search',
    description: 'Поиск информации в интернете',
    prompt_template:
      'Когда нужно найти актуальную информацию, выполни поиск через инструмент web_search.',
    parameters: [
      { name: 'query', type: 'string', description: 'Поисковый запрос', required: true },
    ],
    type: 'anthropic',
  },
  {
    name: 'Code Assistant',
    description: 'Помощь с написанием и отладкой кода',
    prompt_template:
      'Ты опытный разработчик. Пиши чистый, документированный код. Объясняй решения.',
    parameters: [],
    type: 'prompt',
  },
];
