import logging
import random
import uuid
import typing
import configparser
import requests
import json
import math
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
    state = Printer_State()
    try:
        r = requests.get(url = octoprint+'/api/printer', headers = {'X-Api-Key':key})
        if r.status_code == 200:
            state.data = json.loads(r.text)
            state.success = True
        else:
            state.errorCode = str(r.status_code)
            state.success = False
    except Exception:
        state.success = False
    finally:
        return state

#get job state when printing
def get_printer_job_state():
    job_state = Printer_State()
    try:
        r = requests.get(url = octoprint+'/api/job', headers = {'X-Api-Key':key})
        if r.status_code == 200:
            job_state.data = json.loads(r.text)
            job_state.success = True
        else:
            job_state.errorCode = str(r.status_code)
            job_state.success = False
    except Exception:
        job_state.success = False
    finally:
        return job_state




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
        connection_status = get_printer_connection_status()
        msg = ''
        if connection_status.success:
            if connection_status.state == 'Closed':
                msg += 'Принтер выключен'
            else:
                msg += 'Принтер включен\n'
                printer_state = get_printer_state()
                if printer_state.success:
                    if ( (printer_state.data['state']['flags']['printing'] == True) or
                    (printer_state.data['state']['flags']['pausing'] == True) or
                    (printer_state.data['state']['flags']['paused'] == True) or
                    (printer_state.data['state']['flags']['resuming'] == True) ):
                        #get job state if printing
                        job_state = get_printer_job_state()
                        msg += 'Принтер печатает\n'
                        if job_state.success:
                            msg += 'Файл: '+job_state.data['job']['file']['name']
                            msg += '\nПримерное время печати: '+str(round(job_state.data['job']['estimatedPrintTime'],2))
                            msg += '\nИзрасходуется: '+str(round(job_state.data['job']['filament']['tool0']['length'],2))+' мм / '+str(round(job_state.data['job']['filament']['tool0']['volume'],2))+' см³'
                            msg += '\nПрогресс: '+str(round(job_state.data['progress']['completion'],2))+' %'
                            msg += '\nВремя печати: '+str(job_state.data['progress']['printTime'])+' с'
                            msg += '\nОсталось: '+str(job_state.data['progress']['printTimeLeft'])+' с'
                        else:
                            msg += 'Ошибка получения данных о печати'

                    #msg += json.dumps(printer_state.data, indent=2)
                else:
                    msg += 'Ошибка получения данных о статусе'
            await bot.send_message(query.message.chat.id, msg)
        elif connection_status.errorCode != '-1':
            await bot.send_message(query.message.chat.id, 'Ошибка получения статуса!\n Код ответа: '+connection_status.errorCode)
        else:
            await bot.send_message(query.message.chat.id, 'Подключение к OCTOPRINT не удалось')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
