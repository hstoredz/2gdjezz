from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "your_verify_token")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "your_page_token")

# لتخزين أرقام المستخدمين مؤقتاً (في الذاكرة فقط)
sessions = {}

@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]
                if messaging_event.get("message"):
                    msg = messaging_event["message"].get("text", "")
                    handle_message(sender_id, msg)

    return "ok", 200

def handle_message(sender_id, msg):
    msg = msg.strip()
    
    # حالة رقم الهاتف
    if len(msg) == 10 and msg.startswith("07") and msg.isdigit():
        send_message(sender_id, "جاري إرسال كود التفعيل، انتظر...")
        full_number = f"213{msg}"
        data = f'msisdn={full_number}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data)),
            "Host": "apim.djezzy.dz",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "Djezzy/2.6.6",
            "Accept": "*/*"
        }
        res = requests.post('https://apim.djezzy.dz/oauth2/registration', data=data, headers=headers).text
        if 'confirmation code has been sent successfully' in res:
            send_message(sender_id, "✅ تم إرسال الكود. أرسل الكود الآن.")
            sessions[sender_id] = full_number
        else:
            send_message(sender_id, "❌ فشل في إرسال كود OTP، حاول مرة أخرى.")
    
    # حالة الكود
    elif msg.isdigit() and 4 <= len(msg) <= 6 and sender_id in sessions:
        send_message(sender_id, "جاري التحقق من الكود وتفعيل العرض...")
        number = sessions[sender_id]
        otp = msg
        data2 = f'otp={otp}&mobileNumber={number}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data2)),
            "Host": "apim.djezzy.dz",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "Djezzy/2.6.6",
            "Accept": "*/*"
        }
        res2 = requests.post('https://apim.djezzy.dz/oauth2/token', data=data2, headers=headers).json()
        try:
            token = res2['access_token']
            json_data = {
                "data": {
                    "id": "GIFTWALKWIN",
                    "type": "products",
                    "meta": {
                        "services": {
                            "steps": 10666,
                            "code": "GIFTWALKWIN2GO",
                            "id": "WALKWIN"
                        }
                    }
                }
            }
            sub_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
                "Host": "apim.djezzy.dz",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "User-Agent": "Djezzy/2.6.6",
                "Accept": "*/*"
            }
            res = requests.post(f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{number}/subscription-product?include=', json=json_data, headers=sub_headers).text
            if 'successfully done' in res:
                send_message(sender_id, "✅ تم تفعيل عرض 2G بنجاح!")
            else:
                send_message(sender_id, "❌ فشل في تفعيل العرض.")
        except KeyError:
            send_message(sender_id, "❌ الكود غير صحيح أو منتهي.")
    
    else:
        send_message(sender_id, "👋 أهلاً! أرسل رقمك الذي يبدأ بـ07 لتفعيل عرض 2G.")

def send_message(recipient_id, text):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}
    requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
