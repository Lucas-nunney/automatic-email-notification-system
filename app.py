import json
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import threading
import time
from email_utils import send_reminder_email

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

app = Flask(__name__)
REMINDERS_FILE = 'reminders.json'

def load_reminders():
    try:
        with open(REMINDERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_reminders(reminders):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    date = request.form.get('date')
    email = request.form.get('email')

    reminders = load_reminders()
    reminders.append({
        'name': name,
        'date': date,
        'email': email,
        'sent_today': False,
        'sent_week_before': False
    })
    save_reminders(reminders)
    return redirect(url_for('view'))

@app.route('/view')
def view():
    reminders = load_reminders()
    return render_template('view.html', reminders=reminders)

@app.route('/delete/<int:index>', methods=['POST'])
def delete_reminder(index):
    reminders = load_reminders()
    if 0 <= index < len(reminders):
        reminders.pop(index)
        save_reminders(reminders)
    return redirect(url_for('view'))

def check_reminders():
    while True:
        reminders = load_reminders()
        now = datetime.now().date()
        changed = False

        for reminder in reminders:
            reminder_date = datetime.strptime(reminder['date'], '%Y-%m-%d').date()

            # Send on due date
            if reminder_date == now and not reminder.get('sent_today', False):
                send_reminder_email(
                    to_email=reminder['email'],
                    subject=f"Reminder: {reminder['name']} is due today!",
                    body=f"Hey! Your reminder '{reminder['name']}' is due today."
                )
                reminder['sent_today'] = True
                changed = True

            # Send one week before
            if reminder_date - timedelta(days=7) == now and not reminder.get('sent_week_before', False):
                send_reminder_email(
                    to_email=reminder['email'],
                    subject=f"Upcoming Reminder: {reminder['name']} in 1 week",
                    body=f"Just a heads-up: Your reminder '{reminder['name']}' is due on {reminder['date']}!"
                )
                reminder['sent_week_before'] = True
                changed = True

        if changed:
            save_reminders(reminders)

        time.sleep(60)

if __name__ == '__main__':
    print("📧 Loaded email:", os.getenv("EMAIL_ADDRESS")) 
    threading.Thread(target=check_reminders, daemon=True).start()
    app.run(debug=True)


