import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { query } = await req.json();
  // Call backend FastAPI search endpoint
  try {
    const backendUrl = "http://127.0.0.1:8000/research";
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    if (!response.ok) throw new Error("Backend search failed");
    const data = await response.json();
    // Expecting data.results or similar structure from backend
    return NextResponse.json({ results: data.results || [] });
  } catch (err: any) {
    return NextResponse.json({ results: [], error: err.message }, { status: 500 });
  }
}
