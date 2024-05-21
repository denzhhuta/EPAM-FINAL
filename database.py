import aiomysql
import aiogram
import asyncio
from datetime import datetime
from aiosmtplib import SMTP
from email.message import EmailMessage


async def connect_to_db():
    try:
        conn = await aiomysql.connect(
            host='localhost',
            port=3306,
            user="root",
            password="root1234",
            db="table_bookings",
            cursorclass=aiomysql.DictCursor)
    
        print("Connected successfully...")
        return conn
    
    except Exception as ex:
        print("Connection to DataBase refused...")
        print(ex)
        
 # ТО ДЛЯ ТЕЛЕГРАМУ!!!!!!!       
async def get_table_bookings(table_number):
    try:
        conn = await connect_to_db() 
        async with conn.cursor() as cursor:
            query = """
            SELECT id, booking_start, booking_end, email
            FROM bookings
            WHERE table_number = %s AND booking_end > NOW()
            """
            await cursor.execute(query, (table_number,))
            bookings = await cursor.fetchall()
    
        return bookings

    except Exception as ex:
        print("Error occurred while fetching bookings from the database:")
        print(ex)
        return []


async def cancel_booking(booking_id):
    try:
        conn = await connect_to_db()
        async with conn.cursor() as cursor:
            query = "DELETE FROM bookings WHERE id = %s"
            await cursor.execute(query, (booking_id,))
            await conn.commit()
        return True
    
    except Exception as ex:
        print("Error occurred while canceling booking:")
        print(ex)
        return False

#EТПО ВСІ бУкІнГІ
async def get_all_table_bookings():
    try:
        conn = await connect_to_db()
        async with conn.cursor() as cursor:
            query = """
            SELECT id, table_number, booking_start, booking_end
            FROM bookings
            WHERE booking_end > NOW()
            """
            await cursor.execute(query)
            bookings = await cursor.fetchall()

        return bookings

    except Exception as ex:
        print("Error occurred while fetching bookings from the database:")
        print(ex)
        return []

async def send_confirmation_email(booking_email: str, booking_id: str, booking_start: str, booking_end: str, cancellation_reason: str):
    # Email configuration
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'stonehaven.reset@gmail.com'
    smtp_password = 'lfemarbsgejrcfmq'
    
    sender_email = smtp_username
    receiver_email = booking_email
    subject = 'NewYork Cafe | Cancellation of Reservation'
    message = f'''
    <html>
        <head>
            <style>
                /* CSS styles */
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f2f2f2;
                }}
                .container {{
                    margin: 20px;
                    background-color: #ffffff;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    padding: 20px;
                    background-color: #008080;
                    color: #ffffff;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                }}
                .booking-details {{
                    margin: 20px;
                }}
                .booking-id {{
                    font-weight: bold;
                }}
                .message {{
                    margin-top: 20px;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }}
                .footer {{
                    font-style: italic;
                    text-align: center;
                    padding: 10px;
                    background-color: #e0e0e0;
                    border-bottom-left-radius: 5px;
                    border-bottom-right-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">Booking Cancellation</div>
                <div class="booking-details">
                    <p>Your booking with ID: <span class="booking-id">{booking_id}</span> from {booking_start} to {booking_end} has been cancelled.</p>
                    <p>Cancellation Reason: {cancellation_reason}</p>
                </div>
                <div class="message">
                    <p>We apologize for any inconvenience caused.</p>
                </div>
                <div class="footer">NewYork Cafe</div>
            </div>
        </body>
    </html>
    '''
    
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.set_content(message, subtype='html')
    
    # Connect to the SMTP server and send the email
    async with SMTP(hostname='smtp.gmail.com', port=587, start_tls=True,
                    username=sender_email, password=smtp_password) as smtp:
        
        await smtp.send_message(msg)