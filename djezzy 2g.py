from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json

# ضع هنا توكن البوت الذي حصلت عليه من BotFather
TOKEN = "token"

# الوظيفة الرئيسية لطلب رقم الهاتف
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل رقمك الذي يبدأ بـ07 لتفعيل عرض 2G جيزي.")

# وظيفة للتحقق من الرقم المرسل وبدء عملية OTP
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = update.message.text.strip()
    if len(num) == 10 and num.startswith("07") and num.isdigit():
        await update.message.reply_text("جاري إرسال كود التفعيل، انتظر...")
        
        # إعداد البيانات لطلب الكود OTP
        data = f'msisdn=213{num}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data)),
            "Host": "apim.djezzy.dz",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "Djezzy/2.6.6",
            "Accept": "*/*"
        }
        
        # إرسال الطلب للحصول على OTP
        res = requests.post('https://apim.djezzy.dz/oauth2/registration', data=data, headers=headers).text
        if 'the confirmation code has been sent successfully' in res:
            await update.message.reply_text("تم إرسال الكود بنجاح. أرسل الكود الآن.")
            
            # حفظ الرقم في السياق لاستخدامه لاحقاً
            context.user_data["num"] = num
        else:
            await update.message.reply_text("فشل في إرسال كود OTP، حاول مرة أخرى.")
    else:
        await update.message.reply_text("يرجى إرسال رقم صحيح يبدأ بـ07 ويتكون من 10 أرقام.")

# وظيفة لمعالجة كود OTP والتحقق منه
async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    num = context.user_data.get("num")
    
    if num and otp.isdigit():
        await update.message.reply_text("جاري التحقق من الكود وتفعيل العرض...")
        
        # إعداد البيانات لطلب الحصول على التوكن
        data2 = f'otp={otp}&mobileNumber=213{num}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data2)),
            "Host": "apim.djezzy.dz",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "Djezzy/2.6.6",
            "Accept": "*/*"
        }
        
        # إرسال الطلب للحصول على التوكن
        res2 = requests.post('https://apim.djezzy.dz/oauth2/token', data=data2, headers=headers).json()
        
        # التحقق من الحصول على التوكن
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
            
            # إعدادات الطلب لتفعيل العرض
            subscription_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
                "Host": "apim.djezzy.dz",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "User-Agent": "Djezzy/2.6.6",
                "Accept": "*/*"
            }
            
            # إرسال الطلب لتفعيل العرض
            res = requests.post(f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/213{num}/subscription-product?include=', json=json_data, headers=subscription_headers).text
            if 'successfully done' in res:
                await update.message.reply_text("تم تفعيل عرض 2G بنجاح!")
            else:
                await update.message.reply_text("فشل في تفعيل العرض. حاول مرة أخرى.")
                
        except KeyError:
            await update.message.reply_text("الكود المدخل غير صحيح. حاول مرة أخرى.")
    else:
        await update.message.reply_text("يرجى إرسال الكود الصحيح.")

# إعداد البوت وتحديد الأوامر
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة أوامر البداية
    app.add_handler(CommandHandler("start", start))
    
    # إضافة معالجات الرسائل
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^07\d{8}$'), handle_number))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d{4,6}$'), handle_otp))
    
    # تشغيل البوت
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()