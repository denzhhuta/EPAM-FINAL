from flask import Flask, render_template, request, jsonify
from datetime import datetime
from aiosmtplib import SMTP
import asyncio
from email.message import EmailMessage
from reminder import send_telegram_announcement
import aiomysql
 
app = Flask(__name__, template_folder="templates", static_folder="static")

# @app.errorhandler(404)
# def page_not_found(error):
#     return render_template('404.html'), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/book-table', methods=['GET'])
def table():
    return render_template('table.html')

@app.route('/book-table', methods=['POST'])
def book_table():
    booking_data = request.get_json()
    
    # Get current time for the booking
    booking_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    asyncio.run(send_telegram_announcement(booking_data, booking_time))

    # Send confirmation email
    asyncio.run(send_confirmation_email(booking_data, booking_time))
    
    asyncio.run(database_book_table(booking_data, booking_time))
    
    asyncio.run(logs_handler(booking_data["email"], counter=[0]))

    # Return success response to the client
    return jsonify({'success': True})

async def send_confirmation_email(booking_data, booking_time):
    # Email configuration
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'stonehaven.reset@gmail.com'
    smtp_password = 'lfemarbsgejrcfmq'
    
    sender_email = smtp_username
    receiver_email = booking_data['email']
    subject = 'Table Booking Confirmation'
    message = f'''
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
            }}
            h1 {{
                color: #426B1F;
                text-align: center;
                padding: 20px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px;
                background-color: #ffffff;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }}
            th {{
                background-color: #F6DE60;
                color: #426B1F;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>Thank you for booking a table at our restaurant!</h1>
        <table>
            <tr>
                <th>Booking details</th>
                <th>NewYork Cafe</th>
            </tr>
            <tr>
                <td>Table Number:</td>
                <td>{booking_data['tableNumber']}</td>
            </tr>
            <tr>
                <td>Name and Surname:</td>
                <td>{booking_data['name']} {booking_data['surname']}</td>
            </tr>
            <tr>
                <td>Email:</td>
                <td>{booking_data['email']}</td>
            </tr>
            <tr>
                <td>Phone:</td>
                <td>{booking_data['phone']}</td>
            </tr>
            <tr>
                <td>Booking Time:</td>
                <td>{booking_time}</td>
            </tr>
        </table>
    </body>
    </html>
    '''
    
    # Create the email message
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.set_content(message, subtype='html')
    
    # Connect to the SMTP server and send the email
    async with SMTP(hostname='smtp.gmail.com', port=587, start_tls=True,
                    username=sender_email, password=smtp_password) as smtp:
        
        await smtp.send_message(msg)

@app.route('/check-table-availability', methods=['POST'])
async def check_table_availability():
    booking_data = request.get_json()

    # Retrieve the booking information from the database
    conn = await connect_to_db()
    async with conn.cursor() as cursor:
        table_number = booking_data['tableNumber']
        booking_start = booking_data['startTime']
        booking_end = booking_data['endTime']

        query = """
        SELECT booking_start, booking_end
        FROM bookings
        WHERE table_number = %s
        AND booking_start < %s
        AND booking_end > %s
        """
        await cursor.execute(query, (table_number, booking_end, booking_start))
        overlapping_bookings_result = await cursor.fetchall()

        if len(overlapping_bookings_result) > 0:
            # The table is already booked, retrieve the overlapping booking times
            overlapping_bookings = []
            for booking in overlapping_bookings_result:
                booking_range = f"{booking['booking_start']} - {booking['booking_end']}"
                overlapping_bookings.append(booking_range)

            # Return the response with the overlapping booking times
            return jsonify({'available': False, 'overlappingBookings': overlapping_bookings})
        else:
            # The table is available
            return jsonify({'available': True})


async def logs_handler(email, counter=[0]):
    counter[0] += 1
    f = None  # Initialize f with None
    
    try:
        with open('/Users/zgutadenis/Desktop/My Projects/EPAM-3/Epam_project/logs.txt', 'a') as f:
            f.write("\n{email},{time}".format(email=email, time=datetime.now().strftime("%Y-%m-%d %H:%M")))
    except Exception as e:
        print(f"An error occurred while adding the email {email}: {e}")
        if f is not None:
            f.write("\n{counter}An error occurred while adding the email {email}: {exception} at {time}".format(counter=counter, email=email, exception=e, time=datetime.now().strftime("%Y-%m-%d %H:%M")))


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

async def database_book_table(booking_data, booking_time):
    conn = await connect_to_db()
    async with conn.cursor() as cursor:
        table_number = booking_data['tableNumber']
        booked_by = booking_data['name']
        booking_start = booking_data['startTime']
        booking_end = booking_data['endTime']
        booking_email = booking_data['email']

        query = """
        SELECT COUNT(*) AS count
        FROM bookings
        WHERE table_number = %s
        AND booking_start < %s
        AND booking_end > %s
        """
        await cursor.execute(query, (table_number, booking_end, booking_start))
        result = await cursor.fetchone()
        count = result['count']

        if count > 0:
            # The table is already booked
            return jsonify({'success': False, 'message': 'Table already booked for the given time range.'})
        else:
            # Insert the new booking into the database
            insert_query = """
            INSERT INTO bookings (table_number, booking_start, booking_end, booked_by, email)
            VALUES (%s, %s, %s, %s, %s)
            """
            await cursor.execute(insert_query, (table_number, booking_start, booking_end, booked_by, booking_email))
            await conn.commit()

            # Return success response to the client
            return jsonify({'success': True})

@app.route('/get-table-bookings', methods=['POST'])
async def get_table_bookings():
    booking_data = request.get_json()
    table_number = booking_data['tableNumber']

    conn = await connect_to_db()
    
    async with conn.cursor() as cursor:        
        query = """
        SELECT booking_start, booking_end
        FROM bookings
        WHERE table_number = %s AND booking_end > NOW()
        """
        await cursor.execute(query, (table_number,))
        bookings = await cursor.fetchall()
        #print(bookings)
    return jsonify({'bookings': bookings})

 
if __name__ == '__main__':
    app.run(debug=True)