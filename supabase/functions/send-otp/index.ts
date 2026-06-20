import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "@supabase/supabase-js";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
);

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")!;

function generateOTP(): string {
  return Math.floor(1000 + Math.random() * 9000).toString();
}

serve(async (req) => {
  try {
    const { email } = await req.json();

    if (!email) {
      return new Response(JSON.stringify({ error: "Email required" }), {
        status: 400,
      });
    }

    const otp = generateOTP();

    await supabase.from("otp_codes").insert({
      email,
      otp,
      expires_at: new Date(Date.now() + 2 * 60 * 1000).toISOString()
    });

    const emailRes = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: "Vanity Creation <noreply@yourdomain.com>",
        to: [email],
        subject: "Your OTP Code",
        html: `<h1>${otp}</h1>`,
      }),
    });

    if (!emailRes.ok) {
      const err = await emailRes.json();
      return new Response(JSON.stringify({ error: err }), { status: 500 });
    }

    return new Response(
      JSON.stringify({ success: true }),
      { ...corsHeaders, status: 200 }
    );
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      ...corsHeaders,
      status: 500,
    });
  }
});