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
import asyncio
from datetime import datetime, timedelta
from threading import Thread

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
file_offsets = {}
file_name = ''
last_z_pos = '-1'

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
def parse_file_for_offset(name):
    file_pos = 0
    file_offsets.clear()
    with open(config.filesdir+name, 'r') as fp:
        for line in fp:
            last_offset = file_pos

            m = re.search(r"Z\d+.\d+", line)
            if m:
                try:
                    res = m.group(0)
                    file_offsets.update({file_pos:res})
                except IndexError:
                    pass
            file_pos += len(line)
    return '-1'

#get current Z pos from file
def get_current_z_pos(offset):
    lastkey = None
    for key in file_offsets.keys():
        if offset <= key and lastkey != None:
            return file_offsets.get(lastkey,-1)
        lastkey = key
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
    ).add(types.InlineKeyboardButton('📛STOP', callback_data=command_cb.new(action='kb_stop'))).row(
        types.InlineKeyboardButton('� Settings', callback_data=command_cb.new(action='kb_status')),
        types.InlineKeyboardButton('✔ Silent', callback_data=command_cb.new(action='kb_photo')),
        types.InlineKeyboardButton('📲Action', callback_data=command_cb.new(action='kb_print')),
    )

def get_show_keyboard_button():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('⌨️Показать клавиатуру', callback_data=command_cb.new(action='kb_show_keyboard')),
    )

def user_friendly_seconds(n):
    return str(timedelta(seconds = n))

def str_round(number):
    return str(round(number,2))

async def update_printer_status():
    current_state = ''
    global last_printer_state,last_z_pos
    job_state = None
    connection_status = get_printer_connection_status()
    if connection_status.success:
        if connection_status.state == 'Closed':
            current_state = connection_status.state
        else:
            printer_state = get_printer_state()
            if printer_state.success:
                current_state = printer_state.data['state']['text']

            job_state = get_printer_job_state()

    if current_state == 'Operational':
        if (last_printer_state == 'Closed' or
            last_printer_state == 'Connecting'):
            #printer connected
            await send_information_about_job_action('Принтер подключен.')
            await send_printer_status(config.admin)
            print('Printer connected')
        elif (last_printer_state == 'Printing' or
            last_printer_state == 'Pausing' or
            last_printer_state == 'Paused' or
            last_printer_state == 'Resuming' or
            last_printer_state == 'Cancelling'):
            #print finished
            await send_information_about_job_action('Печать завершена.')
            await send_printer_status(config.admin)
            print('Print '+job_state.data['job']['file']['name']+' finished')
    if current_state == 'Closed':
        if (last_printer_state != 'Closed'):
            #printer disconnected
            await send_information_about_job_action('Принтер отключен')
            print('Printer disconnected')
    elif current_state == 'Connecting':
        if last_printer_state == 'Closed':
            #printer connecting
            await send_information_about_job_action('Подключение к принтеру')
            print('Printer connecting')
    elif current_state == 'Printing':
        if (last_printer_state == 'Printing'):
            #get current z progress
            _z = get_current_z_pos(job_state.data['progress']['filepos'])
            if _z != last_z_pos:
                await send_printer_status(config.admin)
            last_z_pos = _z
            if (_z != '-1'):
                print('Printing '+job_state.data['job']['file']['name'] + " at "+_z)
        elif (last_printer_state == 'Operational'):
            #start printing file
            last_z = '-1'
            await send_information_about_job_action('Печать запущена. ')
            await send_printer_status(config.admin)
            print('Start printing '+job_state.data['job']['file']['name'])
            parse_file_for_offset(job_state.data['job']['file']['name'])
        elif (last_printer_state == 'Paused' or
            last_printer_state == 'Resuming'):
            #resumed printing file
            await send_information_about_job_action('Печать продолжена.')
            await send_printer_status(config.admin)
            print('Print '+job_state.data['job']['file']['name']+' resumed')
    elif current_state == 'Paused':
        if (last_printer_state == 'Pausing' or
            last_printer_state == 'Operational'):
            #print paused
            await send_information_about_job_action('Печать приостановлена.')
            await send_printer_status(config.admin)
            print('Print '+job_state.data['job']['file']['name']+' paused')
    elif current_state == 'Pausing':
        if last_printer_state != 'Pausing':
            #print pausing
            await send_information_about_job_action('Печать ставится на паузу.')
            await send_printer_status(config.admin)
            print('Print '+job_state.data['job']['file']['name']+' pausing')
    elif current_state == 'Cancelling':
        if last_printer_state != 'Cancelling':
            #print cancelling
            await send_information_about_job_action('Печать отменяется.')
            await send_printer_status(config.admin)
            print('Print '+job_state.data['job']['file']['name']+' cancelling')
    last_printer_state = current_state

async def send_information_about_job_action(information, silent = True):
    await bot.send_message(config.admin,information)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#command /start. show all menus
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if check_user(message.from_user.id):
        await bot.send_message(message.from_user.id,'Выберите действие', reply_markup=get_main_keyboard())

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)

async def send_printer_status(chat_id):
    connection_status = get_printer_connection_status()
    msg = datetime.now().strftime('%d-%m-%Y %H:%M')+'\n'
    if connection_status.success:
        if connection_status.state == 'Closed':
            msg += '❌ Принтер выключен'
        else:
            msg += '✅ Принтер включен\n'
            printer_state = get_printer_state()
            if printer_state.success:
                msg += '🔥Стол: ' + str_round(printer_state.data['temperature']['bed']['actual'])+'° / '+\
                                    str_round(printer_state.data['temperature']['bed']['target'])+'° Δ'+\
                                    str_round(printer_state.data['temperature']['bed']['offset'])+'°'+'\n'
                msg += '🔥Экструдер: '+ str_round(printer_state.data['temperature']['tool0']['actual'])+'° / '+\
                                        str_round(printer_state.data['temperature']['tool0']['target'])+'°? Δ'+\
                                        str_round(printer_state.data['temperature']['tool0']['offset'])+'°'+'\n'
                if ( (printer_state.data['state']['flags']['printing'] == True) or
                (printer_state.data['state']['flags']['pausing'] == True) or
                (printer_state.data['state']['flags']['paused'] == True) or
                (printer_state.data['state']['flags']['resuming'] == True) or
                (printer_state.data['state']['flags']['cancelling'] == True) ):
                    #get job state if printing
                    job_state = get_printer_job_state()
                    if job_state.success:
                        msg += '🖨Принтер '
                        if printer_state.data['state']['flags']['printing']:
                            msg += 'печатает'
                        elif printer_state.data['state']['flags']['pausing']:
                            msg += 'приостанавливает печать'
                        elif printer_state.data['state']['flags']['paused']:
                            msg += 'на паузе'
                        elif printer_state.data['state']['flags']['resuming']:
                            msg += 'возобновляет печать'
                        elif printer_state.data['state']['flags']['cancelling']:
                            msg += 'отменяет печать'
                        msg += '\n'
                        msg += '💾Файл: '+job_state.data['job']['file']['name']
                        if job_state.data['job']['estimatedPrintTime'] != None:
                            msg += '\n⏱ Примерное время печати: '+user_friendly_seconds(job_state.data['job']['estimatedPrintTime'])
                        _z = get_current_z_pos(job_state.data['progress']['filepos'])
                        if _z != '-1':
                            msg += '\n🏔Высота: '+_z
                        else:
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
        await bot.send_message(chat_id, msg, reply_markup=get_show_keyboard_button())
    elif connection_status.errorCode != '-1':
        await bot.send_message(chat_id, 'Ошибка получения статуса!\n Код ответа: '+connection_status.errorCode, reply_markup=get_show_keyboard_button())
    else:
        await bot.send_message(chat_id, 'Подключение к OCTOPRINT не удалось', reply_markup=get_show_keyboard_button())

    #make photo
    await send_photo(chat_id)


async def send_photo(chat_id):
    try:
        make_photo()
        with open('photo.jpg', 'rb') as photo:
            await bot.send_chat_action(chat_id, action = 'upload_photo')
            await bot.send_photo(chat_id,photo, reply_markup=get_show_keyboard_button())
    except Exception:
        await bot.send_message(chat_id, '🆘Не удалось получить фото', reply_markup=get_show_keyboard_button())

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#button "status"
@dp.callback_query_handler(command_cb.filter(action='kb_status'))
async def callback_status_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение статуса...")  # don't forget to answer callback query as soon as possible\
        await send_printer_status(query.message.chat.id)

#button "photo"
@dp.callback_query_handler(command_cb.filter(action='kb_photo'))
async def callback_photo_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение фото...")  # don't forget to answer callback query as soon as possible\
        await send_photo(query.message.chat.id)

#button "show keyboard"
@dp.callback_query_handler(command_cb.filter(action='kb_show_keyboard'))
async def callback_show_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    await query.answer("выберите действие...")  # don't forget to answer callback query as soon as possible\
    await start_command(query)

def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(10, repeat, coro, loop)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.call_later(10, repeat, update_printer_status, loop)
    executor.start_polling(dp, skip_updates=True)

