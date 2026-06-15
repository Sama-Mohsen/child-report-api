import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
import requests
import json
from datetime import datetime, timezone, timedelta
load_dotenv()

client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
    )

def format_previous_messages(conv, start_of_week, end_of_week):
    messages = sorted(conv["messages"], key=lambda m: m["createdAt"])
    context_msgs = []
    weekly_msgs = []

    for msg in messages:
        msg_time = datetime.fromisoformat(
            msg["createdAt"].replace("Z", "+00:00")
        )

        if msg_time < start_of_week:
            context_msgs.append(msg)
        elif start_of_week <= msg_time < end_of_week:
            weekly_msgs.append(msg)

    context_msgs = context_msgs[-4:]
    conv["messages"] = context_msgs + weekly_msgs
    return conv

def filter_this_week(data):
    now = datetime.now(timezone.utc)

    conversations_data = data["conversations"]

    days_since_saturday = (now.weekday() + 2) % 7
    start_of_week = now - timedelta(days=days_since_saturday)
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7)
    # print(start_of_week, end_of_week)

    filtered = []
    for conv in conversations_data:
        created_at = datetime.fromisoformat(
            conv["conversation"]["createdAt"].replace("Z", "+00:00")
        )
        last_message_at = datetime.fromisoformat(
            conv["conversation"]["lastMessageAt"].replace("Z", "+00:00")
        )

        if (start_of_week <= created_at < end_of_week or
            start_of_week <= last_message_at < end_of_week):
            if created_at < start_of_week:
                format_previous_messages(conv, start_of_week, end_of_week)
            filtered.append(conv)

    data["conversations"] = filtered
    return data

def format_conversations(history):
    conversations = sorted(history["conversations"], key=lambda c: c["conversation"]["createdAt"])
    formatted_conversations = ""
    for i, conversation in enumerate(conversations):

        messages = sorted(conversation["messages"], key=lambda m: m["createdAt"])

        formatted_conversations+=f"Conversation {i+1}:\n"
        for msg in messages:
            if msg["sender"] == "user":
                formatted_conversations += f"User: {msg['message']}\n"
        formatted_conversations += "\n"
    # print(formatted_conversations)
    return formatted_conversations

def generate_report(conversations):
    # model = "models/gemini-2.5-flash"
    model = "models/gemini-3.1-flash-lite-preview"

    prompt = f"""
    Analyze the following weekly conversations:

    {conversations}
    """

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=[
            types.Part.from_text(text="""You are an AI assistant generating a high-level weekly well-being report for parents about their child.

Your goal is to help parents understand their child's emotional state over time while fully respecting the child's privacy.

Follow these rules strictly:

- This is a weekly report, not a real-time assessment:
  - Do NOT describe the child’s current or immediate feelings (e.g., avoid "the child feels now").
  - Do NOT refer to specific days, moments, or exact situations.
  - Focus on overall emotional trends across the conversations.
  - Describe patterns over time using varied and natural expressions (do not repeat the same phrase).

- Use varied and natural phrasing when describing weekly patterns.
- Do NOT rely on a single repeated phrase (e.g., avoid always saying "over the past week").
- You may use different expressions such as:
  - "Throughout the week"
  - "Across recent conversations"
  - "There appears to be a pattern of"
  - "Overall"
  - "It seems that"
  - "In general"
- Avoid repetitive sentence structures across sections.

- Do NOT include or quote any exact messages from the conversations.
- Do NOT reveal sensitive or private details.
- Do NOT expose secrets, names, or specific personal events.
- Focus only on general emotional patterns and overall well-being.

- Be neutral, calm, and respectful.
- Do NOT sound judgmental, critical, or accusatory.
- Do NOT exaggerate or create unnecessary alarm.

- Analyze emotional patterns across time (e.g., improvement, decline, or fluctuations).
- Focus on repeated signals and the overall emotional trend.
- Consider both recurring patterns and the general emotional trajectory.

If there are signs of emotional distress:
- Mention them carefully and gently.
- Do NOT use alarming or extreme language unless clearly necessary.

If there are signs of significant concern:
- Highlight them in a calm and responsible way.
- Encourage supportive actions rather than panic.

Always generate the response in the following format:

1. General Emotional State
- Describe overall mood trends (e.g., stable, fluctuating, mildly stressed).

2. Notable Concerns
- Mention general areas of concern (e.g., stress, self-doubt, withdrawal).
- Focus on repeated or noticeable patterns, not isolated moments.

3. Risk Indicators (if any)
- Include only if there are meaningful warning signs.
- Keep it high-level and careful (no sensitive details).
- Reflect overall patterns, not single statements.

4. Guidance for Parents
- Provide practical, supportive advice on how to help their child.

- Suggestions may include:
  - Encouraging open and non-judgmental communication
  - Creating a safe and supportive environment
  - Avoiding pressure or criticism
  - Gently checking in emotionally

- Optionally suggest helpful resources for parents (e.g., books or podcasts about supporting teens' mental health).

- When recommending books or podcasts:
  - Suggest real, well-known resources when possible.
  - Only provide names if confident they exist.
  - Do NOT invent names.
  - Keep recommendations general, relevant, and appropriate.

- Keep guidance practical, realistic, and respectful.

Return the response strictly in valid JSON format like:

{
  "emotional_summary": "",
  "patterns": [],
  "feedback": "",
  "suggestions": []
}
"""),
        ],
    )

    max_retries = 3
    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config,
            )
            return response.text
        except Exception:
            print(f"Retry {i+1}...")
            time.sleep(2)
    return "Error: Unable to generate the report right now."


def Report(history):
    history = filter_this_week(history)
    conversations = format_conversations(history)
    try:
        report = generate_report(conversations)
        json.loads(report)
        return report

    except Exception:
        return {"error": "unable_to_generate_report_rightnow"}