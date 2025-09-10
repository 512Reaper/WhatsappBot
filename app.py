import re
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__)

# -------------------- Twilio Config --------------------
account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')
twilio_number = os.getenv('twilio_number')
lawyer_whatsapp = os.getenv('lawyer_whatsapp')

# -------------------- Mail Config --------------------
app.config['MAIL_SERVER'] = os.getenv('EMAIL_HOST')
app.config['MAIL_PORT'] = int(os.getenv('EMAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_ADDRESS')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_ADDRESS')

mail = Mail(app)

LAWYER_EMAIL = os.getenv('LAWYER_EMAIL')

client = Client(account_sid, auth_token)

# Store user sessions (basic dict for demo; use DB in production)
user_sessions = {}

def send_email(subject, body, to_email):
    """Send email using Flask-Mail"""
    msg = Message(subject=subject, recipients=[to_email], body=body)
    mail.send(msg)

@app.route('/', methods=['POST'])
def whatsapp_bot():
    sender = request.form.get('From')
    incoming_msg = request.form.get('Body').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    session = user_sessions.get(sender, {'stage': 'start'})

    if session['stage'] == 'start':
        msg.body("Hello! 👋 Welcome to our Legal Services. May I have your *name*, please?")
        session['stage'] = 'get_name'

    elif session['stage'] == 'get_name':
        session['name'] = incoming_msg.title()
        msg.body("Thanks! 📞 Can you provide your *phone number*?")
        session['stage'] = 'get_phone'

    elif session['stage'] == 'get_phone':
        phone = incoming_msg
        if re.fullmatch(r'\d{10}', phone):
            session['phone'] = phone
            msg.body("Great! 📍 What *location* are you contacting us from?")
            session['stage'] = 'get_location'
        else:
            msg.body("❌ Please enter a valid 10-digit phone number (e.g., 9876543210).")
            session['stage'] = 'get_phone'

    elif session['stage'] == 'get_location':
        session['location'] = incoming_msg.title()
        client.messages.create(
            content_sid=os.getenv('lawyer1'),
            from_=twilio_number,
            to=sender
        )
        session['stage'] = 'get_case_type'

    elif session['stage'] == 'get_case_type':
        session['case_type'] = incoming_msg
        if incoming_msg.lower() == 'others':
            client.messages.create(
                content_sid=os.getenv('lawyer2'),
                from_=twilio_number,
                to=sender,
            )
        else:
            msg.body("When would you be available for a callback? \n1. Morning\n2. Afternoon\n3. Evening")
            session['stage'] = 'get_time'

    elif session['stage'] == 'get_time':
        session['time'] = incoming_msg
        msg.body("✅ Thank you for providing the details. Our team will get back to you shortly.")

        # Send collected info to lawyer via email
        summary = f""" 
        📨 *New Client Inquiry* 
        👤 Name: {session['name']} 
        📞 Phone: {session['phone']} 
        📍 Location: {session['location']} 
        📂 Case Type: {session['case_type']} 
        🕒 Preferred Time: {session['time']} """

        send_email(
            subject="New Client Inquiry",
            body=summary,
            to_email=LAWYER_EMAIL
        )

        user_sessions.pop(sender, None)

    user_sessions[sender] = session
    return str(resp)


if __name__ == '__main__':
    app.run()
