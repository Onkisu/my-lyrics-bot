from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def bot():
    print(f"[DEBUG - ENV] All environment vars: {os.environ}")
    API_KEY = os.getenv("GOOGLE_DEV_API")  # pakai API key Gemini
    print(f"[DEBUG] Loaded Gemini API Key: {API_KEY}")
    
    incoming_msg = request.values.get("Body", "").strip()
    print(f"[WHATSAPP INCOMING] Message: {incoming_msg}")

    lang_prompt = detect_language(incoming_msg)
    prompt = f"{lang_prompt} {incoming_msg}"
    print(f"[AI PROMPT] {prompt}")

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [{"text":{prompt}"}]
                    }
                ]
            },
            timeout=30
        )

        data = response.json()
        print(f"[AI RESPONSE RAW] {data}")

        # Ambil hasil teks dari struktur Gemini API
        lyrics = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not lyrics:
            lyrics = "Maaf, AI tidak bisa membuat lirik saat ini."

        print(f"[AI LYRICS GENERATED]\n{lyrics}")

        twilio_resp = MessagingResponse()
        for part in split_message(lyrics):
            twilio_resp.message(part)

        return Response(str(twilio_resp), mimetype="application/xml")

    except Exception as e:
        print(f"[ERROR] Failed to get response from Gemini: {e}")
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
    port = int(os.environ.get("PORT", 5001))
    print(f"[SERVER] AI Lyrics bot is running on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)
