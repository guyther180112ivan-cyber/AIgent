import { SignJWT, jwtVerify } from 'jose';
import bcrypt from 'bcryptjs';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import path from 'path';

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'aigent-local-secret-key-change-in-production-2024'
);
const USERS_FILE = path.join(process.cwd(), 'data', 'users.json');

export interface User {
  id: string;
  username: string;
  password: string;
  createdAt: string;
}

export interface TokenPayload {
  userId: string;
  username: string;
  [key: string]: string;
}

function readUsers(): User[] {
  if (!existsSync(USERS_FILE)) {
    return [];
  }
  try {
    return JSON.parse(readFileSync(USERS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeUsers(users: User[]) {
  const dir = path.dirname(USERS_FILE);
  writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export async function createToken(payload: TokenPayload): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(JWT_SECRET);
}

export async function verifyToken(token: string): Promise<TokenPayload | null> {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    return payload as unknown as TokenPayload;
  } catch {
    return null;
  }
}

export function findUserByUsername(username: string): User | undefined {
  const users = readUsers();
  return users.find(u => u.username === username);
}

export function findUserById(id: string): User | undefined {
  const users = readUsers();
  return users.find(u => u.id === id);
}

export async function createUser(username: string, password: string): Promise<User | { error: string }> {
  const users = readUsers();

  if (users.find(u => u.username === username)) {
    return { error: 'Username already exists' };
  }

  const hashedPassword = await hashPassword(password);
  const user: User = {
    id: crypto.randomUUID(),
    username,
    password: hashedPassword,
    createdAt: new Date().toISOString(),
  };

  users.push(user);
  writeUsers(users);
  return user;
}
