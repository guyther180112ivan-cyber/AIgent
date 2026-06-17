import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import LoginPage from './login/page';

export default async function Home() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;

  if (token) {
    const payload = await verifyToken(token);
    if (payload) {
      redirect('/agents');
    }
  }

  return <LoginPage />;
}
