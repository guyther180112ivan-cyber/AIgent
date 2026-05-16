import { readFileSync, existsSync, writeFileSync } from 'fs';
import path from 'path';

const AGENTS_FILE = path.join(process.cwd(), 'data', 'agents.json');

export interface Agent {
  id: string;
  name: string;
  model: string;
  description?: string;
  system_prompt?: string;
  is_active: boolean;
  created_at: string;
  user_id: string;
}

function readAgents(): Agent[] {
  if (!existsSync(AGENTS_FILE)) {
    return [];
  }
  try {
    return JSON.parse(readFileSync(AGENTS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeAgents(agents: Agent[]) {
  const dir = path.dirname(AGENTS_FILE);
  writeFileSync(AGENTS_FILE, JSON.stringify(agents, null, 2));
}

export function getAgentsByUserId(userId: string): Agent[] {
  const agents = readAgents();
  return agents.filter(a => a.user_id === userId);
}

export function getAgentById(agentId: string): Agent | undefined {
  const agents = readAgents();
  return agents.find(a => a.id === agentId);
}

export function createAgent(data: Omit<Agent, 'id' | 'created_at'>): Agent {
  const agents = readAgents();
  const agent: Agent = {
    ...data,
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
  };
  agents.push(agent);
  writeAgents(agents);
  return agent;
}

export function updateAgent(agentId: string, updates: Partial<Agent>): Agent | undefined {
  const agents = readAgents();
  const index = agents.findIndex(a => a.id === agentId);
  if (index === -1) return undefined;
  agents[index] = { ...agents[index], ...updates };
  writeAgents(agents);
  return agents[index];
}

export function deleteAgent(agentId: string): boolean {
  const agents = readAgents();
  const filtered = agents.filter(a => a.id !== agentId);
  if (filtered.length === agents.length) return false;
  writeAgents(filtered);
  return true;
}
