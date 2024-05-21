import aiogram
from aiogram import types, Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import Update
from aiogram.types.chat_member import ChatMemberMember, ChatMemberOwner, ChatMemberAdministrator
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command
from keyboard import on_players_online_press
from keyboard import on_booking_press
from database import get_table_bookings
from database import cancel_booking
from database import get_all_table_bookings
from database import send_confirmation_email
import urllib.parse
import hashlib

class CheckSubscriptionUserMiddleware(BaseMiddleware):
    def __init__(self):
         self.prefix = 'key_prefix'
         super(CheckSubscriptionUserMiddleware, self).__init__()
         
    async def on_process_update(self, update: types.Update, data: dict):
        if "message" in update:
            this_user = update.message.from_user
            if update.message.text:
                if "start" in update.message.text:
                    return
    
        elif "callback_query" in update:
            this_user = update.callback_query.from_user
        
        else:
            this_user = None
        
        if this_user is not None:
            get_prefix = self.prefix
                     
            if not this_user.is_bot:                       
                user_id = this_user.id
                if this_user.username != "morkovka2005":
                    await bot.send_message(user_id, 
                               "<b>😔 You are not allowed to use this bot!</b>", 
                               parse_mode="HTML")
                    
                    raise CancelHandler()     
                        
TOKEN_API = "6064195503:AAHdQeQ6LA4T2BPoDTBozkOucEIwCTcliQo"

storage = MemoryStorage()
bot = aiogram.Bot(TOKEN_API)
dp = aiogram.Dispatcher(bot, storage=storage)

booking_mapping = {}

def generate_booking_identifier(booking_id, booking_start, booking_end, booking_email):
    identifier_string = f"{booking_id}{booking_start}{booking_end}{booking_email}"
    identifier_hash = hashlib.md5(identifier_string.encode()).hexdigest()
    return identifier_hash

async def send_telegram_announcement(booking_data, booking_time):
    announcement_message = f"<b>Table booked!</b>\n\n<b>Name</b>: {booking_data['name']} {booking_data['surname']}\n<b>Table Number</b>: {booking_data['tableNumber']}\n<b>Email</b>: {booking_data['email']}\n<b>Phone</b>: {booking_data['phone']}\n<b>Booking Time</b>: {booking_time}"
    await bot.send_message(chat_id = 1013673667,
                           text=announcement_message,
                           parse_mode="HTML")

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message) -> None:
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    if last_name is None:
        await bot.send_message(chat_id=message.from_user.id,
                           text=f"<b>Вітаю, {message.from_user.first_name}!</b>",
                           parse_mode="HTML",
                           reply_markup=on_players_online_press())
    else:
        await bot.send_message(chat_id=message.from_user.id,
                           text=f"<b>Вітаю, {message.from_user.first_name} {message.from_user.last_name}!</b>",
                           parse_mode="HTML",
                           reply_markup=on_players_online_press())

@dp.message_handler(text='Назад 🔙')
async def update_reply_keyboard_back(message: types.Message) -> None:
   await bot.send_message(chat_id=message.from_user.id,
                           text='<b>Головне меню 🧾</b>',
                           parse_mode="HTML",
                           reply_markup=on_players_online_press())
   
@dp.message_handler(text='Пореглянути бронювання 🕐')
async def update_reply_keyboard_back(message: types.Message) -> None:
   await bot.send_message(chat_id=message.from_user.id,
                           text='<b>Меню бронювання 🧾</b>',
                           parse_mode="HTML",
                           reply_markup=on_booking_press())
   
@dp.message_handler(text=['Стіл 1', 'Стіл 2', 'Стіл 3', 'Стіл 4', 'Стіл 5', 'Стіл 6', 'Стіл 7', 'Стіл 8', 'Стіл 9'])
async def handle_table_booking_selection(message: types.Message):
    table_number = int(message.text.split()[1])  # Extract the table number from the button text
    bookings = await get_table_bookings(table_number)
    
    keyboard = InlineKeyboardMarkup(row_width=1)  # Initialize the keyboard variable
    
    if bookings:
        for booking in bookings:
            booking_id = booking['id']
            booking_start = booking['booking_start']
            booking_end = booking['booking_end']
            booking_email = booking['email']
            
            booking_identifier = generate_booking_identifier(booking_id, booking_start, booking_end, booking_email)
            button_text = f"ID: {booking_id}\nStart: {booking_start}\nEnd: {booking_end}"
            button_callback_data = f"cancel_booking_{booking_identifier}"
            booking_mapping[booking_identifier] = {
                'id': booking_id,
                'start': booking_start,
                'end': booking_end,
                'email': booking_email
            }
            keyboard.add(InlineKeyboardButton(text=button_text, callback_data=button_callback_data))
        
        response_message = f"<b>Valid Bookings for Table {table_number}:</b>\n\n"
        response_message += "To undo cancellation - /cancel\nPlease select the booking interval you want to cancel:"
    else:
        response_message = f"No valid bookings found for Table {table_number}"
        
    await bot.send_message(chat_id=message.chat.id, text=response_message, parse_mode="HTML", reply_markup=keyboard)

@dp.message_handler(text=['Переглянути всі бронювання 🚫'])
async def handle_all_bookings(message: types.Message):
    try:
        all_bookings = await get_all_table_bookings()
        
        if not all_bookings:
            await message.reply("There are no bookings at the moment.")
        else:
            response = "All bookings:\n\n"
            for booking in all_bookings:
                response += f"Booking ID: {booking['id']}\n"
                response += f"Table Number: {booking['table_number']}\n"
                response += f"Booking Start: {booking['booking_start']}\n"
                response += f"Booking End: {booking['booking_end']}\n\n"
            
            await message.reply(response)
    
    except Exception as ex:
        print("Error occurred while handling all bookings command:")
        print(ex)
        await message.reply("An error occurred while fetching the bookings.")

# Callback query handler to handle cancel booking interval button press
@dp.callback_query_handler(lambda query: query.data.startswith('cancel_booking_'))
async def handle_cancel_booking(query: types.CallbackQuery, state: FSMContext):
    booking_identifier = query.data.split('_')[2]  # Extract the booking identifier from the callback data
    print(booking_identifier)
    # Retrieve the booking details using the identifier from the mapping
    booking_details = booking_mapping.get(booking_identifier)
    
    if booking_details:
        await state.update_data(booking_identifier=booking_identifier)
        await query.message.reply("Please, send the reason for cancellation:")
        await state.set_state("cancel_booking")
    
    else:
        await bot.send_message(chat_id=query.message.chat.id,
                               text="Invalid booking indentifier!")
        
@dp.message_handler(state='cancel_booking')   
async def collect_cancellation_reasion(message: types.Message, state: FSMContext):
    cancellation_reason = message.text.strip()
    
    if cancellation_reason.startswith('Стіл'):
        await bot.send_message(chat_id=message.from_user.id,
                               text="<b>Unvalid reason!</b>",
                               parse_mode="HTML")
        
        await state.reset_state("cancel_booking")
        return
    
    if cancellation_reason.startswith("Назад"):
        await bot.send_message(chat_id=message.from_user.id,
                               text="<b>Unvalid reason!</b>",
                               parse_mode="HTML")
        
        await state.reset_state()
        return
    
    if str(cancellation_reason) == '/cancel':
        await bot.send_message(chat_id=message.from_user.id,
                               text="<b>Operation has been cancelled!</b>",
                               parse_mode="HTML")
        await state.reset_state()
        return
    
    async with state.proxy() as data:
        booking_identifier = data.get('booking_identifier')
        
    booking_details = booking_mapping.get(booking_identifier)
    
    if booking_details:
        booking_id = booking_details['id']
        booking_start = booking_details['start']
        booking_end = booking_details['end']
        booking_email = booking_details['email']
    
        await cancel_booking(booking_id)
        
        if booking_email:
            await send_confirmation_email(booking_email, booking_id, booking_start, booking_end, cancellation_reason)
                   
        await bot.send_message(chat_id=message.from_user.id, 
                               text=f"Booking ID {booking_id} with interval {booking_start} - {booking_end} was canceled. Reason: {cancellation_reason}")
        await state.reset_state()

    
    else:
        await bot.send_message(chat_id=message.from_user.id,
                               text="Invalid booking identifier!")
        await state.reset_state()
    
    
    
    
    # if booking_details:
    #     # Extract the necessary details from the booking_details dictionary
    #     booking_id = booking_details['id']
    #     booking_start = booking_details['start']
    #     booking_end = booking_details['end']
    #     booking_email = booking_details['email']
     
    #     # Implement your logic to cancel the specific interval of the booking using the booking ID
    #     await cancel_booking(booking_id)
        
    #     if booking_email:
    #         await send_confirmation_email(booking_email, booking_id, booking_start, booking_end)
        
    #     await bot.send_message(chat_id=query.message.chat.id, text=f"Booking ID {booking_id} with interval {booking_start} - {booking_end} was canceled.")
    # else:
    #     await bot.send_message(chat_id=query.message.chat.id, text="Invalid booking identifier.")


if __name__ == '__main__':
    dp.middleware.setup(CheckSubscriptionUserMiddleware())
    executor.start_polling(dp, 
                           skip_updates=True)    