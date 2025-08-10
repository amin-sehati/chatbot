Repository layout for Vercel deployment:

- `app/` Next.js App Router UI and routes.
- `app/api/chat/route.ts` Frontend API route that converts AI SDK UI messages and forwards to the Python function.
- `api/python-chat.py` Python serverless function (FastAPI + LangChain).
- `requirements.txt` Python dependencies.
- `vercel.json` Configures Python runtime and build commands.

## Getting Started

First, run the development server:

```bash
npm run dev
```
And in a separate terminal, run the Python server:
```bash
uv run uvicorn api.python-chat:app --host 127.0.0.1 --port 8000
```


Open [http://localhost:3001](http://localhost:3001) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

1. Push to a Git repo, import into Vercel.
2. Set `OPENAI_API_KEY` in Vercel Project Settings → Environment Variables.
3. Deploy. The UI calls `/api/chat`, which proxies to the Python function `/pychat` on Vercel.
