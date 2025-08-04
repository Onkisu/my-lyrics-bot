from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get("Body", "").strip()
    print(f"[WHATSAPP INCOMING] Message: {incoming_msg}")

    lang_prompt = detect_language(incoming_msg)
    prompt = f"{lang_prompt} Write a song lyrics about: {incoming_msg}"
    print(f"[AI PROMPT] {prompt}")

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/horizon-beta",
                "messages": [
                    {"role": "system", "content": "You are a creative lyrics composer."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500
            },
            timeout=30
        )

        data = response.json()
        print(f"[AI RESPONSE RAW] {data}")

        lyrics = data["choices"][0]["message"]["content"]
        print(f"[AI LYRICS GENERATED]\n{lyrics}")

        twilio_resp = MessagingResponse()

        for part in split_message(lyrics):
            twilio_resp.message(part)

        return Response(str(twilio_resp), mimetype="application/xml")

    except Exception as e:
        print(f"[ERROR] Failed to get response from OpenRouter: {e}")
        twilio_resp = MessagingResponse()
        twilio_resp.message("Sorry, the AI couldn't generate lyrics at the moment. Please try again later.")
        return Response(str(twilio_resp), mimetype="application/xml")


def detect_language(msg):
    if any(char in msg for char in "あいうえお"):
        return "Write in Japanese."
    elif any(char.lower() in "abcdefghijklmnopqrstuvwxyz" for char in msg):
        return "Write in English."
    else:
        return "Write in Indonesian."

def split_message(msg, limit=1200):
    return [msg[i:i+limit] for i in range(0, len(msg), limit)]

if __name__ == "__main__":
    print("[SERVER] AI Lyrics bot is running on http://localhost:5001")
    app.run(debug=True, host="0.0.0.0", port=port)
