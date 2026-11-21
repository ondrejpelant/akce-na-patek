import { NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

export async function POST(request: Request) {
  const token = new URL(request.url).searchParams.get("token");
  const expected = process.env.REVALIDATE_TOKEN;

  if (!expected || token !== expected) {
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }

  revalidatePath("/");
  return NextResponse.json({ ok: true, revalidated: ["/"], now: new Date().toISOString() });
}
