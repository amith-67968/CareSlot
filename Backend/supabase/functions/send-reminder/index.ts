// CareSlot — Supabase Edge Function: Send Reminder
// Processes pending reminders and creates notifications.
// Deploy: supabase functions deploy send-reminder
// Schedule via pg_cron or Supabase Dashboard cron job (every 5 minutes).

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get pending reminders that are due
    const now = new Date().toISOString();
    const { data: reminders, error: fetchError } = await supabase
      .from("reminders")
      .select("*")
      .eq("status", "pending")
      .lte("scheduled_at", now)
      .limit(50);

    if (fetchError) {
      throw new Error(`Failed to fetch reminders: ${fetchError.message}`);
    }

    if (!reminders || reminders.length === 0) {
      return new Response(
        JSON.stringify({ message: "No pending reminders", processed: 0 }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    let processed = 0;

    for (const reminder of reminders) {
      // Create notification for this reminder
      const { error: notifError } = await supabase
        .from("notifications")
        .insert({
          user_id: reminder.user_id,
          title: reminder.title,
          body: reminder.description || `Reminder: ${reminder.title}`,
          type: reminder.reminder_type,
          is_read: false,
          reference_id: reminder.reference_id,
        });

      if (notifError) {
        console.error(`Notification insert error for reminder ${reminder.id}:`, notifError);
        continue;
      }

      // Update reminder status to 'sent'
      const { error: updateError } = await supabase
        .from("reminders")
        .update({ status: "sent" })
        .eq("id", reminder.id);

      if (updateError) {
        console.error(`Reminder update error for ${reminder.id}:`, updateError);
        continue;
      }

      // Handle recurring reminders
      if (reminder.recurrence && reminder.recurrence !== "none") {
        const nextDate = calculateNextDate(reminder.scheduled_at, reminder.recurrence);
        if (nextDate) {
          await supabase.from("reminders").insert({
            user_id: reminder.user_id,
            title: reminder.title,
            description: reminder.description,
            reminder_type: reminder.reminder_type,
            scheduled_at: nextDate,
            status: "pending",
            reference_id: reminder.reference_id,
            recurrence: reminder.recurrence,
          });
        }
      }

      processed++;
    }

    return new Response(
      JSON.stringify({ message: "Reminders processed", processed }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Edge function error:", error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});

function calculateNextDate(currentDate: string, recurrence: string): string | null {
  const date = new Date(currentDate);
  switch (recurrence) {
    case "daily":
      date.setDate(date.getDate() + 1);
      break;
    case "weekly":
      date.setDate(date.getDate() + 7);
      break;
    case "monthly":
      date.setMonth(date.getMonth() + 1);
      break;
    default:
      return null;
  }
  return date.toISOString();
}
