import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { verifyToken, findUserById } from '@/lib/auth';
import DashboardShell from '@/components/layout/DashboardShell';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;

  if (!token) {
    redirect('/login');
  }

  const payload = await verifyToken(token);

  if (!payload) {
    redirect('/login');
  }

  const user = findUserById(payload.userId);

  if (!user) {
    redirect('/login');
  }

  const sidebarUser = {
    id: user.id,
    email: user.username,
    user_metadata: { username: user.username },
  };

  return (
    <DashboardShell user={sidebarUser}>
      {children}
    </DashboardShell>
  );
}
