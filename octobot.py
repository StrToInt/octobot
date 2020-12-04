import logging
import random
import uuid
import typing
import configparser
import requests
import json
import math
import re
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
    filesdir: str

config_file = configparser.ConfigParser()
config_file.read('config.ini')

config = octobot_config(token = config_file.get("main", "token"),
                        key = config_file.get("main", "key"),
                        admin = config_file.get("main", "admin"),
                        octoprint = config_file.get("main", "octoprint"),
                        filesdir = config_file.get("main", "filesdir"))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

bot = Bot(token=config.token)
dp = Dispatcher(bot)

last_printer_state = 'Closed'
file_offsets = None
file_name = ''

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

#parse file for Z offsets
def parse_file_for_offset(name, offset):
    file_pos = 0
    last_z = ''
    with open(config.filesdir+name, 'r') as fp:
        for line in fp:
            last_offset = file_pos

            if offset <= file_pos:
                return last_z
            m = re.search(r"Z\d+.\d+", line)
            if m:
                try:
                    res = m.group(0)
                    last_z = res
                except IndexError:
                    pass
            file_pos += len(line)
    return '-1'

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
        types.InlineKeyboardButton('❔ Status', callback_data=command_cb.new(action='kb_status')),
        types.InlineKeyboardButton('📸Photo', callback_data=command_cb.new(action='kb_photo')),
        types.InlineKeyboardButton('🖨Print...', callback_data=command_cb.new(action='kb_print')),
    ).add(types.InlineKeyboardButton('📛STOP', callback_data=command_cb.new(action='kb_stop')))

def get_show_keyboard_button():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('⌨️Показать клавиатуру', callback_data=command_cb.new(action='kb_show_keyboard')),
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
        msg = datetime.now().strftime('%d-%m-%Y %H:%M')+'\n'
        if connection_status.success:
            if connection_status.state == 'Closed':
                msg += '❌ Принтер выключен'
            else:
                msg += '✅ Принтер включен\n'
                printer_state = get_printer_state()
                if printer_state.success:
                    if ( (printer_state.data['state']['flags']['printing'] == True) or
                    (printer_state.data['state']['flags']['pausing'] == True) or
                    (printer_state.data['state']['flags']['paused'] == True) or
                    (printer_state.data['state']['flags']['resuming'] == True) ):
                        #get job state if printing
                        job_state = get_printer_job_state()
                        msg += '🖨Принтер печатает\n'
                        if job_state.success:
                            msg += '💾Файл: '+job_state.data['job']['file']['name']
                            if job_state.data['job']['estimatedPrintTime'] != None:
                                msg += '\n⏱ Примерное время печати: '+user_friendly_seconds(job_state.data['job']['estimatedPrintTime'])
                            try:
                                _z = parse_file_for_offset(job_state.data['job']['file']['name'],job_state.data['progress']['filepos'])
                                if _z != '-1':
                                    msg += '\n🏔Высота: '+_z
                            except Exception:
                                msg += '\n🏔Высота Z "неизвестна"'
                            if job_state.data['job']['filament'] != None:
                                msg += '\n⛓Израсходуется: '+str(round(job_state.data['job']['filament']['tool0']['length'],2))+' мм / '+str(round(job_state.data['job']['filament']['tool0']['volume'],2))+' см³'
                            msg += '\n🔄Прогресс: '+str(round(job_state.data['progress']['completion'],2))+' %'
                            msg += '\n⏰ Время печати: '+user_friendly_seconds(job_state.data['progress']['printTime'])
                            msg += '\n⏰ Осталось: '+user_friendly_seconds(job_state.data['progress']['printTimeLeft'])
                            time_end = datetime.now() + timedelta(seconds = job_state.data['progress']['printTimeLeft'])
                            msg += '\n⏰ Закончится: '+time_end.strftime('%d-%m-%Y %H:%M')
                        else:
                            msg += '🆘Ошибка получения данных о печати'

                    #msg += json.dumps(printer_state.data, indent=2)
                else:
                    msg += '🆘Ошибка получения данных о статусе'
            await bot.send_message(query.message.chat.id, msg, reply_markup=get_show_keyboard_button())
        elif connection_status.errorCode != '-1':
            await bot.send_message(query.message.chat.id, 'Ошибка получения статуса!\n Код ответа: '+connection_status.errorCode, reply_markup=get_show_keyboard_button())
        else:
            await bot.send_message(query.message.chat.id, 'Подключение к OCTOPRINT не удалось', reply_markup=get_show_keyboard_button())

        await query.answer("получение фото...")  # don't forget to answer callback query as soon as possible\

        #make photo
        await callback_photo_command(query,callback_data)

#button "photo"
@dp.callback_query_handler(command_cb.filter(action='kb_photo'))
async def callback_photo_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение фото...")  # don't forget to answer callback query as soon as possible\
        try:
            make_photo()
            with open('photoaf.jpg', 'rb') as photo:
                await query.message.answer_photo(photo, reply_markup=get_show_keyboard_button())
        except Exception:
            await bot.send_message(query.message.chat.id, '🆘Не удалось получить фото', reply_markup=get_show_keyboard_button())

#button "show keyboard"
@dp.callback_query_handler(command_cb.filter(action='kb_show_keyboard'))
async def callback_show_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    await query.answer("выберите действие...")  # don't forget to answer callback query as soon as possible\
    await start_command(query)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

