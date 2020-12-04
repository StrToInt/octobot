import logging
import random
import uuid
import typing
import configparser
import requests
import json
import math
from dataclasses import dataclass
import subprocess
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.utils.callback_data import CallbackData

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

#config++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@dataclass
class octobot_config:
    token: str
    key: str
    admin: str
    octoprint: str
config_file = configparser.ConfigParser()
config_file.read('config.ini')

config = octobot_config(token = config_file.get("main", "token"),
                        key = config_file.get("main", "key"),
                        admin = config_file.get("main", "admin"),
                        octoprint = config_file.get("main", "octoprint"))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

bot = Bot(token=config.token)
dp = Dispatcher(bot)

last_printer_state = 'Closed'

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
        r = requests.get(url = config.octoprint+'/api/connection', headers = {'X-Api-Key':config.key})
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
        r = requests.get(url = config.octoprint+'/api/printer', headers = {'X-Api-Key':config.key})
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
        r = requests.get(url = config.octoprint+'/api/job', headers = {'X-Api-Key':config.key})
        if r.status_code == 200:
            job_state.data = json.loads(r.text)
            if job_state.data['progress']['printTime'] == None:
                job_state.data['progress']['printTime'] = -1
            if job_state.data['progress']['printTimeLeft'] == None:
                job_state.data['progress']['printTimeLeft'] = -1
            job_state.success = True
        else:
            job_state.errorCode = str(r.status_code)
            job_state.success = False
    except Exception:
        job_state.success = False
    finally:
        return job_state




#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def make_photo():
    subprocess.call("bash photo.sh", shell=True)

def check_user(user_id):
    if str(user_id) == config.admin:
        return True
    else:
        return False

def get_main_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('❔ Status', callback_data=command_cb.new(action='kb_status'),parse_mode=ParseMode.MARKDOWN),
        types.InlineKeyboardButton('Photo', callback_data=command_cb.new(action='photo')),
    )

def user_friendly_seconds(n):
    return str(timedelta(seconds = n))

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
                            if job_state.data['job']['filament'] != None:
                                msg += '\nИзрасходуется: '+str(round(job_state.data['job']['filament']['tool0']['length'],2))+' мм / '+str(round(job_state.data['job']['filament']['tool0']['volume'],2))+' см³'
                            msg += '\nПрогресс: '+str(round(job_state.data['progress']['completion'],2))+' %'
                            msg += '\nВремя печати: '+user_friendly_seconds(job_state.data['progress']['printTime'])
                            msg += '\nОсталось: '+user_friendly_seconds(job_state.data['progress']['printTimeLeft'])
                            time_end = datetime.now() + timedelta(seconds = job_state.data['progress']['printTimeLeft'])
                            msg += '\nЗакончится: '+time_end.strftime('%d-%m-%Y %H:%M')
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
        try:
            make_photo()
            with open('photoaf.jpg', 'rb') as photo:
                await query.message.answer_photo(photo)
        except Exception:
            await bot.send_message(query.message.chat.id, 'Не удалось получить фото')



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

