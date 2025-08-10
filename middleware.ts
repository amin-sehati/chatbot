import { NextResponse, NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  // Allow login and static assets
  if (
    pathname.startsWith("/login") ||
    pathname.startsWith("/api/login") ||
    pathname.startsWith("/api/python-chat") ||
    pathname.startsWith("/pychat") ||
    pathname.startsWith("/_next/") ||
    pathname === "/favicon.ico" ||
    pathname.startsWith("/public/")
  ) {
    return NextResponse.next();
  }

  const authed = req.cookies.get("chat_auth")?.value === "1";
  if (!authed) {
    const url = req.nextUrl.clone();
    const returnTo = req.nextUrl.pathname + (req.nextUrl.search || "");
    url.pathname = "/login";
    url.searchParams.set("from", returnTo);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}


