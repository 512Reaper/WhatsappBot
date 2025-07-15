from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)


account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
twilio_number = 'whatsapp:+14155238886'
lawyer_whatsapp = 'whatsapp:+91XXXXXXXXXX'  # Replace with lawyer's number

client = Client(account_sid, auth_token)

# Store user sessions (basic dict for demo; use DB in production)
user_sessions = {}

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
        session['phone'] = incoming_msg
        msg.body("Great! 📍 What *location* are you contacting us from?")
        session['stage'] = 'get_location'

    elif session['stage'] == 'get_location':
        session['location'] = incoming_msg.title()
        msg.body("Please choose your *case type*:\n1. Property\n2. Family\n3. Criminal\n4. Business")
        session['stage'] = 'get_case_type'

    elif session['stage'] == 'get_case_type':
        session['case_type'] = incoming_msg
        msg.body("When would you be available for a callback? \n1. Morning\n2. Afternoon\n3. Evening")
        session['stage'] = 'get_time'

    elif session['stage'] == 'get_time':
        session['time'] = incoming_msg
        msg.body("✅ Thank you for providing the details. Our team will get back to you shortly.")

        # Send collected info to lawyer
        summary = f"""
📨 *New Client Inquiry*

👤 Name: {session['name']}
📞 Phone: {session['phone']}
📍 Location: {session['location']}
📂 Case Type: {session['case_type']}
🕒 Preferred Time: {session['time']}
        """
        client.messages.create(
            from_=twilio_number,
            to=lawyer_whatsapp,
            body=summary
        )

        session['stage'] = 'done'

    user_sessions[sender] = session
    return str(resp)


if __name__ == '__main__':
    app.run()
