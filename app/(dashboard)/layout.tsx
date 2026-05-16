import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { verifyToken, findUserById } from '@/lib/auth';
import Sidebar from '@/components/layout/Sidebar';

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
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar user={sidebarUser} />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
