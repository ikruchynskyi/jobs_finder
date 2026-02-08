# AutoApply Frontend

Modern, responsive frontend for the Job Application Automation Platform built with Next.js 14, React, and Tailwind CSS.

## Features

✅ **Google OAuth Authentication** - Sign in with Google account  
✅ **Email/Password Authentication** - Traditional authentication support  
✅ **Profile Management** - Complete user profile with resume upload  
✅ **Resume Upload** - Drag-and-drop resume upload with file validation  
✅ **Job Browsing** - Search and browse jobs from multiple platforms  
✅ **Job Crawling** - Trigger automated job crawling  
✅ **Auto-Apply** - One-click application to multiple jobs  
✅ **Application Tracking** - Monitor all your job applications  
✅ **Dark Mode** - Full dark mode support  
✅ **Responsive Design** - Works on desktop, tablet, and mobile  
✅ **Real-time Updates** - Live status updates for applications  

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with Framer Motion animations
- **Authentication**: NextAuth.js with Google OAuth
- **State Management**: Zustand
- **Form Handling**: React Hook Form + Zod validation
- **HTTP Client**: Axios
- **File Upload**: React Dropzone
- **Notifications**: React Hot Toast

## Design Features

### Distinctive Aesthetic
- Modern teal & amber color scheme
- Custom Outfit font family for clean, professional look
- Glass morphism effects
- Smooth animations with Framer Motion
- Gradient accents and hover effects
- Custom scrollbar styling
- Responsive grid layouts

### User Experience
- Intuitive navigation with sidebar
- Real-time feedback for all actions
- Loading states and error handling
- Keyboard shortcuts support
- Accessibility compliant

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (see backend README)
- Google OAuth credentials (optional, for Google sign-in)

### Installation

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Set up environment variables:**
```bash
cp .env.local.example .env.local
```

Edit `.env.local` and add:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

3. **Start development server:**
```bash
npm run dev
```

4. **Open your browser:**
```
http://localhost:3000
```

## Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
5. Application type: **Web application**
6. Authorized redirect URIs:
   - `http://localhost:3000/api/auth/callback/google`
   - `https://yourdomain.com/api/auth/callback/google` (for production)
7. Copy **Client ID** and **Client Secret** to `.env.local`

## Project Structure

```
frontend/
├── app/
│   ├── api/auth/[...nextauth]/   # NextAuth configuration
│   ├── auth/                      # Authentication pages
│   │   ├── signin/                # Sign in page
│   │   └── signup/                # Sign up page
│   ├── dashboard/                 # Dashboard pages
│   │   ├── layout.tsx             # Dashboard layout with sidebar
│   │   ├── page.tsx               # Dashboard home
│   │   ├── profile/               # Profile management
│   │   ├── jobs/                  # Job browsing
│   │   └── applications/          # Applications tracking
│   ├── globals.css                # Global styles
│   ├── layout.tsx                 # Root layout
│   └── page.tsx                   # Landing page
├── components/
│   └── providers.tsx              # Context providers
├── types/
│   └── next-auth.d.ts             # TypeScript definitions
├── public/                        # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Available Scripts

```bash
# Development
npm run dev              # Start dev server at http://localhost:3000

# Production
npm run build            # Build for production
npm start               # Start production server

# Code Quality
npm run lint            # Run ESLint
```

## Key Pages

### Landing Page (`/`)
- Hero section with animated background
- Feature showcase
- Google OAuth and email sign-in options
- Responsive design

### Dashboard (`/dashboard`)
- Overview statistics
- Recent applications
- Success rate visualization
- Quick access to all features

### Profile (`/dashboard/profile`)
- Personal information management
- Resume upload with drag-and-drop
- Skills management (add/remove tags)
- Cover letter template
- Social links (LinkedIn, GitHub, Portfolio)

### Jobs (`/dashboard/jobs`)
- Search and filter jobs
- Browse jobs from multiple platforms
- One-click apply functionality
- Job crawling trigger
- Remote job filtering

### Applications (`/dashboard/applications`)
- Track all job applications
- Filter by status (Pending, Applied, Interview, etc.)
- View application details
- Delete pending applications
- Direct links to original job postings

## Authentication Flow

1. **Google OAuth**:
   - User clicks "Continue with Google"
   - Redirects to Google consent screen
   - Google returns to `/api/auth/callback/google`
   - User is registered/logged in automatically
   - Redirects to dashboard

2. **Email/Password**:
   - User enters credentials
   - Frontend validates input
   - Sends to backend `/api/v1/auth/login`
   - Receives JWT tokens
   - Stores in session
   - Redirects to dashboard

## API Integration

The frontend communicates with the backend API using Axios:

```typescript
// Example: Fetching user profile
const response = await axios.get(
  `${API_URL}/api/v1/users/profile`,
  {
    headers: {
      Authorization: `Bearer ${session.accessToken}`
    }
  }
);
```

All authenticated requests include the JWT token in the Authorization header.

## Styling Guide

### Color Scheme

```css
Primary (Teal):   hsl(174, 72%, 44%)
Secondary (Amber): hsl(42, 87%, 55%)
```

### Common Patterns

**Glass Effect:**
```tsx
<div className="glass rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
  {/* Content */}
</div>
```

**Gradient Text:**
```tsx
<h1 className="text-gradient">Your Text</h1>
```

**Primary Button:**
```tsx
<button className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white">
  Click Me
</button>
```

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy

### Docker

```bash
# Build image
docker build -t autoapply-frontend .

# Run container
docker run -p 3000:3000 autoapply-frontend
```

### Environment Variables for Production

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=production-secret-key
GOOGLE_CLIENT_ID=production-google-client-id
GOOGLE_CLIENT_SECRET=production-google-client-secret
```

## Troubleshooting

### Google OAuth not working
- Check redirect URIs match exactly
- Verify Client ID and Secret are correct
- Ensure Google+ API is enabled

### API connection errors
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend is running
- Inspect network requests in DevTools

### Build errors
- Clear `.next` folder: `rm -rf .next`
- Delete `node_modules` and reinstall
- Check TypeScript errors: `npm run type-check`

## Performance Optimization

- **Image Optimization**: Next.js Image component
- **Code Splitting**: Automatic with Next.js App Router
- **Font Optimization**: Google Fonts with `next/font`
- **Bundle Analysis**: `npm run analyze`

## Accessibility

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - see backend LICENSE for details
