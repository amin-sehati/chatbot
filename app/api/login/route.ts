import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const { password } = await req.json();
    const chatPassword = process.env.CHAT_PASSWORD;
    
    if (!chatPassword) {
      console.error("CHAT_PASSWORD environment variable not set");
      return NextResponse.json({ error: "Server configuration error" }, { status: 500 });
    }

    if (password === chatPassword) {
      const response = NextResponse.json({ success: true });
      // Set authentication cookie
      response.cookies.set("chat_auth", "1", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: "/",
      });
      return response;
    } else {
      return NextResponse.json({ error: "Incorrect password" }, { status: 401 });
    }
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
