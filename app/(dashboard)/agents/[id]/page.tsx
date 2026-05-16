import { getAgentById } from '@/lib/agents';
import { notFound } from 'next/navigation';
import ChatWindow from '@/components/chat/ChatWindow';

type Params = { params: Promise<{ id: string }> };

export default async function AgentPage({ params }: Params) {
  const { id } = await params;
  const agent = getAgentById(id);

  if (!agent) notFound();

  return <ChatWindow agentId={id} agentName={agent.name} />;
}
