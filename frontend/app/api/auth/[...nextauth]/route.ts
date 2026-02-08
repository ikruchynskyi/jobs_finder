import NextAuth, { NextAuthOptions } from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import CredentialsProvider from 'next-auth/providers/credentials';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        try {
          // Login to backend API
          const formData = new URLSearchParams();
          formData.append('username', credentials?.email || '');
          formData.append('password', credentials?.password || '');

          const response = await axios.post(
            `${API_URL}/api/v1/auth/login`,
            formData,
            {
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            }
          );

          if (response.data.access_token) {
            // Fetch user data
            const userResponse = await axios.get(
              `${API_URL}/api/v1/users/me`,
              {
                headers: { Authorization: `Bearer ${response.data.access_token}` }
              }
            );

            return {
              id: userResponse.data.id.toString(),
              email: userResponse.data.email,
              name: userResponse.data.full_name,
              accessToken: response.data.access_token,
              refreshToken: response.data.refresh_token,
            };
          }
          
          return null;
        } catch (error) {
          console.error('Login error:', error);
          return null;
        }
      }
    })
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      if (account?.provider === 'google') {
        try {
          // Register/login user in backend with Google info
          const response = await axios.post(`${API_URL}/api/v1/auth/register`, {
            email: user.email,
            username: user.email?.split('@')[0],
            password: Math.random().toString(36).slice(-8), // Random password for OAuth users
            full_name: user.name,
          });

          // If user already exists, login
          if (response.status === 201 || response.status === 400) {
            const formData = new URLSearchParams();
            formData.append('username', user.email || '');
            formData.append('password', Math.random().toString(36).slice(-8));

            const loginResponse = await axios.post(
              `${API_URL}/api/v1/auth/login`,
              formData,
              {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
              }
            );

            if (loginResponse.data.access_token) {
              user.accessToken = loginResponse.data.access_token;
              user.refreshToken = loginResponse.data.refresh_token;
            }
          }
        } catch (error) {
          console.error('Google sign-in error:', error);
        }
      }
      return true;
    },
    async jwt({ token, user, account }) {
      if (user) {
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.id = token.id as string;
      session.accessToken = token.accessToken as string;
      session.refreshToken = token.refreshToken as string;
      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: 'jwt',
  },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
