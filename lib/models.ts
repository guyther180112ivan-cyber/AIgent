export const MODELS = [
  { value: 'qwen/qwen3-coder:free', label: 'Qwen3 Coder (рекомендуется, бесплатно)', free: true },
  { value: 'meta-llama/llama-3.3-70b-instruct:free', label: 'Llama 3.3 70B (бесплатно)', free: true },
  { value: 'google/gemma-4-26b-a4b-it:free', label: 'Gemma 4 26B (бесплатно)', free: true },
  { value: 'qwen/qwen3-next-80b-a3b-instruct:free', label: 'Qwen3 Next 80B (бесплатно)', free: true },
  { value: 'openai/gpt-4o-mini', label: 'GPT-4o Mini', free: false },
  { value: 'openai/gpt-4o', label: 'GPT-4o', free: false },
  { value: 'anthropic/claude-3-5-sonnet', label: 'Claude 3.5 Sonnet', free: false },
  { value: 'anthropic/claude-3-haiku', label: 'Claude 3 Haiku (быстрый)', free: false },
  { value: 'google/gemini-pro', label: 'Gemini Pro', free: false },
];

export const DEFAULT_MODEL = 'qwen/qwen3-coder:free';

export function getModelLabel(model: string): string {
  return MODELS.find((m) => m.value === model)?.label || model;
}
