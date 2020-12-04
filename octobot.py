import logging
import random
import uuid
import typing
import configparser
import requests
import json
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.utils.callback_data import CallbackData

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('broadcast')

#config
config = configparser.ConfigParser()
config.read('config.ini')
token = config.get("main", "token")
key = config.get("main", "key")
admin = config.get("main", "admin")
octoprint = config.get("main", "octoprint")

bot = Bot(token=token)
dp = Dispatcher(bot)

command_cb = CallbackData('id','action')  # post:<id>:<action>

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@dataclass
class Printer_Connection:
    errorCode: str = '-1'
    success: bool = False
    state: str = 'Closed'

@dataclass
class Printer_State:
    errorCode: str = '-1'
    success: bool = False
    data: str = ''

#get printer status
def get_printer_connection_status():
    status = Printer_Connection()
    try:
        r = requests.get(url = octoprint+'/api/connection', headers = {'X-Api-Key':key})
        if r.status_code == 200:
            json_data = json.loads(r.text)
            status.state = json_data['current']['state']
            status.success = True
        else:
            status.errorCode = str(r.status_code)
            status.success = False
    except Exception:
        status.success = False
    finally:
        return status

#get printer state when connected
def get_printer_state():
    status = Printer_State()
    try:
        r = requests.get(url = octoprint+'/api/connection', headers = {'X-Api-Key':key})
        if r.status_code == 200:
            status.data = json.loads(r.text)
            status.success = True
        else:
            status.errorCode = str(r.status_code)
            status.success = False
    except Exception:
        status.success = False
    finally:
        return status




#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def check_user(user_id):
    if str(user_id) == admin:
        return True
    else:
        return False

def get_main_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('❔ Status', callback_data=command_cb.new(action='kb_status'),parse_mode=ParseMode.MARKDOWN),
        types.InlineKeyboardButton('Photo', callback_data=command_cb.new(action='photo')),
    )


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#command /start. show all menus
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if check_user(message.from_user.id):
        await bot.send_message(message.from_user.id,'Выберите действие', reply_markup=get_main_keyboard())

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#button "status"
@dp.callback_query_handler(command_cb.filter(action='kb_status'))
async def callback_status_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение статуса...")  # don't forget to answer callback query as soon as possible\
        status = get_printer_connection_status()
        if status.success:
            await bot.send_message(query.message.chat.id, status.state)
        elif status.errorCode != '-1':
            await bot.send_message(query.message.chat.id, 'Ошибка получения статуса!\n Код ответа: '+status.errorCode)
        else:
            await bot.send_message(query.message.chat.id, 'Подключение к OCTOPRINT не удалось')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
