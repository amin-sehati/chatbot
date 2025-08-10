# ChatBot - Next.js + Python Backend

A chatbot application built with Next.js frontend and Python serverless backend, optimized for Vercel deployment.

## Repository Structure

- `app/` - Next.js App Router UI and routes
- `api/python-chat.py` - Python serverless function (FastAPI + LangChain + OpenAI)
- `requirements.txt` - Python dependencies
- `vercel.json` - Routing configuration for Vercel

## Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- OpenAI API key

## Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   Create a `.env.local` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   CHAT_PASSWORD=your_password_here
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **For Python backend testing (optional):**
   ```bash
   pip install -r requirements.txt
   python -c "from api.python_chat import handler; print('Python backend ready')"
   ```

5. **Open [http://localhost:3000](http://localhost:3000)**

## Vercel Deployment

### Method 1: Git Integration (Recommended)

1. **Push to GitHub/GitLab:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Import to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your repository
   - Vercel will auto-detect Next.js and Python

3. **Set Environment Variables:**
   - In Vercel dashboard → Project Settings → Environment Variables
   - Add: `OPENAI_API_KEY` = `your_api_key_here`
   - Add: `CHAT_PASSWORD` = `your_password_here`

4. **Deploy:**
   - Vercel will automatically build and deploy
   - The `/api/chat` endpoint will route to the Python backend

### Method 2: Vercel CLI

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login and deploy:**
   ```bash
   vercel login
   vercel --prod
   ```

3. **Set environment variables:**
   ```bash
   vercel env add OPENAI_API_KEY
   ```

## How It Works

- Frontend: Next.js React app with chat interface
- Backend: Python serverless function using FastAPI + LangChain + OpenAI GPT-4
- Routing: `/api/chat` → `api/python-chat.py` (configured in `vercel.json`)
- Vercel automatically detects Python runtime from `requirements.txt`

## Troubleshooting

- **404 on `/api/chat`**: Ensure `vercel.json` has the correct rewrite rule
- **Python errors**: Check that `OPENAI_API_KEY` is set in Vercel environment variables
- **Build failures**: Ensure `requirements.txt` includes all Python dependencies

## Environment Variables

| Variable | Description | Required |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes |
| `CHAT_PASSWORD` | Password for accessing the chat | Yes |
