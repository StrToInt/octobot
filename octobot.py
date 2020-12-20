import logging
import random
import uuid
import typing
import configparser
import requests
import json
import math
import pprint
import traceback
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

config = configparser.ConfigParser()
config.read('config.ini')

#writeconfig
def config_write():
    with open('config.ini', "w") as config_file:
        config.write(config_file)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@dataclass
class Print_File_Data:
    start_time = None
    last_z_pos = -1.0
    max_z_pos = -1.0
    last_z_time = None
    common_layer_time = None
    file_name = ''
    offsets = {}


bot = Bot(token=config.get("main", "token"))
dp = Dispatcher(bot)

last_printer_state = 'Closed'
print_file: Print_File_Data = None
last_msg = None

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
def parse_file_for_offsets(name):
    global print_file
    file_pos = 0
    print_file = None
    max_z = -1.0
    max_z_finish = float(config.get('printer','max_z_finish'))
    new_file_data = Print_File_Data()
    new_file_data.offsets = {}
    new_file_data.file_name = name
    new_file_data.start_time = datetime.now()
    new_file_data.common_layer_time = None
    new_file_data.last_z_time = None
    print('Parsing file for offsets: '+ name)
    with open(config.get("main", "filesdir")+name, 'r') as fp:
        for line in fp:
            last_offset = file_pos

            m = re.search(r"(?<=Z)\d+\.\d+", line)
            file_pos += len(line)
            if m:
                res_text = m.group(0)
                res = float(res_text) #resulted Z pos
                try:
                    if res > max_z:
                        if max_z_finish != -1.0:
                            if res < max_z_finish:
                                max_z = res
                        else:
                            max_z = res
                except Exception:
                    pass

                new_file_data.offsets.update({file_pos+len(res_text):res})
    new_file_data.max_z_pos = max_z
    print_file = new_file_data
    print(new_file_data.offsets)
    print('max_Z = '+str(max_z))

#get current Z pos from file with layers range
def get_current_z_pos_with_range(offset):
    global print_file
    if print_file != None:
        #temp pos
        lastkey = None
        keynum = 0
        for key in print_file.offsets.keys():
            if offset <= key and lastkey != None:
                return [print_file.offsets.get(lastkey,-1),keynum,len(print_file.offsets.keys())]
            keynum+=1
            lastkey = key
    return [-1,0,0]

#get current Z pos from file
def get_current_z_pos(offset):
    return get_current_z_pos_with_range(offset)[0]

#get z position as string with max and percentage
def get_z_pos_str():
    return

#get printer status
def get_printer_connection_status():
    status = Printer_Connection()
    try:
        r = requests.get(url = config.get("main", "octoprint")+'/api/connection', headers = {'X-Api-Key':config.get("main", "key")}, timeout=3)
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
        r = requests.get(url = config.get("main", "octoprint")+'/api/printer', headers = {'X-Api-Key':config.get("main", "key")},timeout=3)
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
        r = requests.get(url = config.get("main", "octoprint")+'/api/job', headers = {'X-Api-Key':config.get("main", "key")},timeout=3)
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


#execute command
async def execute_command(path):
    print('Execute command '+ '/api/system/commands/'+path)
    result = Printer_State()
    try:
        r = requests.post(url = config.get("main", "octoprint")+'/api/system/commands/'+path, headers = {'X-Api-Key':config.get("main", "key")},timeout=3)
        if r.status_code == 204:
            result.success = True
        else:
            result.errorCode = str(r.status_code)
            result.success = False
    except Exception:
        traceback.print_exc()
        result.success = False
    finally:
        return result

#get printer registered commands
def get_printer_commands(source = 'core'):
    printer_commands = Printer_State()
    try:
        r = requests.get(url = config.get("main", "octoprint")+'/api/system/commands/'+source, headers = {'X-Api-Key':config.get("main", "key")},timeout=2)
        if r.status_code == 200:
            printer_commands.data = json.loads(r.text)
            printer_commands.success = True
        else:
            printer_commands.errorCode = str(r.status_code)
            printer_commands.success = False
    except Exception:
        printer_commands.success = False
    finally:
        return printer_commands

#boolean smile
def get_smile_for_boolean(inp):
    return '✅' if inp == True else '❌'

#boolean on/off
def get_smile_for_boolean_str(inp):
    return 'вкл' if inp == True else 'выкл'

def get_additional_file_strings():
    info = ''

    try:
        with open('information.txt','r',encoding="utf-8") as fp:
            line = fp.readline()
            while line:
                info += line
                line = fp.readline()
    except:
        return None

    return info

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def make_photo():
    subprocess.call("bash photo.sh", shell=True)

def check_user(user_id):
    if str(user_id) == config.get("main", "admin"):
        return True
    else:
        return False

def get_main_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('❔ Статус', callback_data=command_cb.new(action='kb_status')),
        types.InlineKeyboardButton('📸Фото', callback_data=command_cb.new(action='kb_photo')),
        types.InlineKeyboardButton('🖨Печать...', callback_data=command_cb.new(action='kb_print')),
    ).add(types.InlineKeyboardButton('📛STOP', callback_data=command_cb.new(action='kb_stop_request'))).row(
        types.InlineKeyboardButton('� Настройки', callback_data=command_cb.new(action='kb_show_settings')),
        types.InlineKeyboardButton(get_smile_for_boolean(config.getboolean('misc','silent'))+' Silent', callback_data=command_cb.new(action='kb_silent_toggle')),
        types.InlineKeyboardButton('📲Действия', callback_data=command_cb.new(action='kb_show_actions')),
    )


def get_settings_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton(get_smile_for_boolean(config.getboolean('misc','silent'))+' Беззвук', callback_data=command_cb.new(action='kb_silent_toggle'))
    ).row(
        types.InlineKeyboardButton(get_smile_for_boolean(config.getboolean('misc','silent_photos'))+' Беззвук на фото', callback_data=command_cb.new(action='kb_photo_silent_toggle')),
    ).row(
        types.InlineKeyboardButton(get_smile_for_boolean(config.getboolean('misc','silent_z_change'))+' Беззвук на изменение Z', callback_data=command_cb.new(action='kb_z_silent_toggle')),
    ).row(
        types.InlineKeyboardButton('Назад', callback_data=command_cb.new(action='kb_show_keyboard')),
    )

def get_show_keyboard_button():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('⌨️Показать клавиатуру', callback_data=command_cb.new(action='kb_show_keyboard')),
    )

def user_friendly_seconds(n):
    return str(timedelta(seconds = n,microseconds=0, milliseconds=0))

def str_round(number):
    return str(round(number,2))

async def update_printer_status():
    current_state = ''
    global last_printer_state,print_file
    job_state = None
    connection_status = get_printer_connection_status()
    if connection_status.success:
        print('Printer status:' + connection_status.state)
        if connection_status.state == 'Closed':
            current_state = connection_status.state
        else:
            printer_state = get_printer_state()
            if printer_state.success:
                current_state = printer_state.data['state']['text']

            job_state = get_printer_job_state()

    #Operational
    if current_state == 'Operational':
        if last_printer_state in ('Closed','Connecting'):
            #printer connected
            await send_information_about_job_action('⏩ Принтер подключен.')
            await send_printer_status()
            print('Printer connected')
        elif last_printer_state in ('Printing','Pausing','Paused','Resuming','Cancelling','Finishing'):
            #print finished
            await send_information_about_job_action('⏩ Печать завершена.')
            await send_printer_status()
            print_file = None
            print('Print '+job_state.data['job']['file']['name']+' finished')
    #Closed
    if current_state == 'Closed':
        if last_printer_state != 'Closed':
            #printer disconnected
            print_file = None
            await send_information_about_job_action('⏩ Принтер отключен')
            print('Printer disconnected')
    #Connecting
    elif current_state == 'Connecting':
        if last_printer_state == 'Closed':
            #printer connecting
            await send_information_about_job_action('⏩ Подключение к принтеру')
            print('Printer connecting')
    #Printing
    elif current_state == 'Printing':
        if last_printer_state == 'Printing':
            #get current z progress
            _z = get_current_z_pos(job_state.data['progress']['filepos'])
            if _z != print_file.last_z_pos:
                if print_file.last_z_time != None:
                    print_file.common_layer_time = datetime.now() - print_file.last_z_time
                print_file.last_z_time = datetime.now()
                await send_printer_status(silent = config.getboolean('misc','silent_z_change') )
            print_file.last_z_pos = _z
            if (_z != -1):
                print('Printing '+job_state.data['job']['file']['name'] + " at "+str(_z))
        elif last_printer_state in ('Paused','Resuming','Pausing'):
            #resumed printing file
            await send_information_about_job_action('⏩ Печать продолжена.')
            await send_printer_status()
            if print_file == None:
                parse_file_for_offsets(job_state.data['job']['file']['name'])
            print('Print '+job_state.data['job']['file']['name']+' resumed')
        else: #if last_printer_state in ['Operational', 'Closed','Connecting']:
            #start printing file
            await send_information_about_job_action('⏩ Печать запущена. ')
            await send_printer_status()
            print('Start printing '+job_state.data['job']['file']['name'])
            parse_file_for_offsets(job_state.data['job']['file']['name'])
    #Paused
    elif current_state == 'Paused':
        if last_printer_state in ('Pausing','Operational'):
            #print paused
            await send_information_about_job_action('⏩ Печать приостановлена.')
            await send_printer_status()
            if print_file == None:
                parse_file_for_offsets(job_state.data['job']['file']['name'])
            print('Print '+job_state.data['job']['file']['name']+' paused')
    #Pausing
    elif current_state == 'Pausing':
        if last_printer_state != 'Pausing':
            #print pausing
            await send_information_about_job_action('⏩ Печать ставится на паузу.')
            await send_printer_status()
            if print_file == None:
                parse_file_for_offsets(job_state.data['job']['file']['name'])
            print('Print '+job_state.data['job']['file']['name']+' pausing')
    #Cancelling
    elif current_state == 'Cancelling':
        if last_printer_state != 'Cancelling':
            #print cancelling
            await send_information_about_job_action('⏩ Печать отменяется.')
            await send_printer_status()
            print('Print '+job_state.data['job']['file']['name']+' cancelling')
    last_printer_state = current_state

async def send_information_about_job_action(information, silent = True):
    await bot.send_message(config.get('main','admin'),information)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#command /start. show all menus
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    if check_user(message.from_user.id):
        await bot.send_message(message.from_user.id,'Выберите действие', reply_markup=get_main_keyboard())

#command /photo. get photo
@dp.message_handler(commands=['photo'])
async def photo_command(message: types.Message):
    if check_user(message.from_user.id):
        await send_photos(message.from_user.id, silent = False, cap = None)

#command /status. get status
@dp.message_handler(commands=['status'])
async def status_command(message: types.Message):
    if check_user(message.from_user.id):
        await send_printer_status(silent = False)

#command /actions. get actions
@dp.message_handler(commands=['actions'])
async def actions_command(message: types.Message):
    if check_user(message.from_user.id):
        await send_actions_keyboard(message.from_user.id)

#echo all
@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text + "\nYou ID: "+ str(message.from_user.id))

#get printer status text
async def get_printer_status_string():
    photo_cation = 'Фото '
    global print_file
    connection_status = get_printer_connection_status()
    msg = datetime.now().strftime('%d.%m.%Y %H:%M')+'\n'
    if connection_status.success:
        if connection_status.state in ['Closed','Offline']:
            msg += '❌ Принтер выключен'
            print('11111')
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
                        if print_file != None:
                            if print_file.start_time != None:
                                msg += '\n⏱ Печать начата: '+print_file.start_time.strftime('%d.%m.%Y %H:%M')
                        if job_state.data['job']['estimatedPrintTime'] != None:
                            msg += '\n⏱ Расчетное время печати: '+user_friendly_seconds(job_state.data['job']['estimatedPrintTime'])
                        _z = get_current_z_pos_with_range(job_state.data['progress']['filepos'])

                        if print_file != None:
                            if _z[0] != -1:
                                photo_cation ='Высота: '+str(round(_z[0],2)) + " / " +str(round(print_file.max_z_pos,2)) + "мм " +\
                                    str(round(100*_z[0]/print_file.max_z_pos,1))+"% Осталось: "+str(round(print_file.max_z_pos-_z[0],2))+"мм"+\
                                    "\n📚Слой "+str(_z[1]) + " / "+str(_z[2])+" "+str(round(100*_z[1]/_z[2],1))+"% Осталось: "+str(_z[2]-_z[1])
                                if print_file.common_layer_time != None:
                                    photo_cation += "\n⏱/📚Время на слой "+str(print_file.common_layer_time)
                                msg += '\n🏔'+photo_cation
                            else:
                                msg += '\n🏔Высота Z ?'
                        if job_state.data['job']['filament'] != None:
                            msg += '\n⛓Израсходуется: '+str(round(job_state.data['job']['filament']['tool0']['length'],2))+' мм / '+str(round(job_state.data['job']['filament']['tool0']['volume'],2))+' см³'
                        tempp = '\n🔄Прогресс: ' + str(job_state.data['progress']['filepos'])+' / ' +\
                            str(job_state.data['job']['file']['size'])+' байт '+\
                            str(round(job_state.data['progress']['completion'],2))+' %'
                        photo_cation += tempp
                        msg += tempp
                        msg += '\n⏰ Время печати: '+user_friendly_seconds(job_state.data['progress']['printTime'])
                        msg += '\n⏰ Осталось: '+user_friendly_seconds(job_state.data['progress']['printTimeLeft'])
                        time_end = datetime.now() + timedelta(seconds = job_state.data['progress']['printTimeLeft'])
                        msg += '\n⏰ Закончится: '+time_end.strftime('%d.%m.%Y %H:%M')
                    else:
                        msg += '🆘Ошибка получения данных о печати'
            else:
                msg += '🆘Ошибка получения данных о статусе'

            add_info = get_additional_file_strings()
            if add_info != None:
                msg += '\n'+add_info

            return [1,msg]

        add_info = get_additional_file_strings()
        if add_info != None:
            msg += '\n'+add_info
        return [1,msg]
    else:
        return [0,connection_status.errorCode]

    return [-1,'']


#send printer status
async def send_printer_status(silent = False):
    chat_id = config.get('main','admin')
    status = await get_printer_status_string()
    if status[0] == -1:
        pass
        await bot.send_message(chat_id, 'Подключение к OCTOPRINT не удалось', reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent') )
    elif status[0] == 0:
        pass
        await bot.send_message(chat_id, 'Ошибка получения статуса!\n Код ответа: '+status[1], reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent') )
    else:
        #send message if all success
        if  config.getint('printer','cam_count') > 0:
            await send_photos(chat_id,silent,None)

        await bot.send_message(chat_id, status[1], reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent') )

async def send_photos(chat_id, silent = False, cap = None):
    make_photo()
    cam_count = config.getint('printer','cam_count')
    print(f'Make photo from {cam_count} cameras')
    if cam_count == 1:
        with open('photo.jpg', 'rb') as photo:
            await bot.send_chat_action(chat_id, action = 'upload_photo')
            await bot.send_photos(chat_id,photo, caption = cap, reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent_photos') )
    else:
        media = types.MediaGroup()
        for c in range(1,cam_count+1):
            print(f'Attach photo from #{c} camera')
            media.attach_photo(types.InputFile('photo'+str(c)+'.jpg'), caption = cap if c == 1 else None)

        await bot.send_chat_action(chat_id, action = 'upload_photo')
        try:
            await bot.send_media_group(chat_id,media, disable_notification = silent or config.getboolean('misc','silent') )
        except Exception as e:
            traceback.print_exc()
            await bot.send_message(chat_id, "\nНе удалось отправить фото", reply_markup=get_show_keyboard_button(),\
                disable_notification = silent or config.getboolean('misc','silent') )


async def delete_last_msg():
    global last_msg
    if last_msg != None:
        try:
            await bot.delete_message(last_msg.chat.id,last_msg.message_id)
        except:
            pass
        finally:
            last_msg = None


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#button "status"
@dp.callback_query_handler(command_cb.filter(action='kb_status'))
async def callback_status_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение статуса...")
        await send_printer_status()

#button "photo"
@dp.callback_query_handler(command_cb.filter(action='kb_photo'))
async def callback_photo_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение фото...")
        await send_photos(query.message.chat.id)

#button "show keyboard"
@dp.callback_query_handler(command_cb.filter(action='kb_show_keyboard'))
async def callback_show_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("выберите действие...")
        await start_command(query)

async def send_actions_keyboard(chat_id):
    kbd = types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('🌋Прогнать файл по высотам Z', callback_data=command_cb.new(action='kb_reparse_file'))
        )
    commands_data = get_printer_commands('core')
    if commands_data.success:
        add_kbd=[]
        print(commands_data.data)
        for command in commands_data.data:
            add_kbd.append(types.InlineKeyboardButton(command['name'], callback_data=command_cb.new(action='action_core_'+command['action'])))
        kbd.add(*add_kbd)

    commands_data = get_printer_commands('custom')
    if commands_data.success:
        add_kbd=[]
        print(commands_data.data)
        for command in commands_data.data:
            add_kbd.append(types.InlineKeyboardButton(command['name'], callback_data=command_cb.new(action='action_custom_'+command['action'])))
        kbd.add(*add_kbd)

    kbd.row(
            types.InlineKeyboardButton('Назад', callback_data=command_cb.new(action='kb_show_keyboard')),
        )
    global last_msg
    last_msg = await bot.send_message(chat_id,'Действия', reply_markup=kbd)


#button "show actions"
@dp.callback_query_handler(command_cb.filter(action='kb_show_actions'))
async def callback_show_actions_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("выберите действие...")
        send_actions_keyboard(query.message.chat.id)

#button "show settings"
@dp.callback_query_handler(command_cb.filter(action='kb_show_settings'))
async def callback_show_settings(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("Настройки")
        await bot.send_message(query.message.chat.id,'Настройки', reply_markup=get_settings_keyboard())

#button "silent mode toggle"
@dp.callback_query_handler(command_cb.filter(action='kb_silent_toggle'))
async def callback_silent_mode_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        val = not config.getboolean('misc','silent')
        config.set('misc','silent', str(val))
        config_write()
        await query.answer("Режим беззвука: " + get_smile_for_boolean_str(val))

#button "silent photo mode toggle"
@dp.callback_query_handler(command_cb.filter(action='kb_photo_silent_toggle'))
async def callback_silent_photo_mode_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        val = not config.getboolean('misc','silent_photos')
        config.set('misc','silent_photos', str(val))
        config_write()
        await query.answer("Режим беззвука для фотографий: " + get_smile_for_boolean_str(val))

#button "silent z change toggle"
@dp.callback_query_handler(command_cb.filter(action='kb_z_silent_toggle'))
async def callback_silent_z_change_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        val = not config.getboolean('misc','silent_z_change')
        config.set('misc','silent_z_change', str(val))
        config_write()
        await query.answer("Режим беззвука на изменение Z: " + get_smile_for_boolean_str(val))

#button "reparse file"
@dp.callback_query_handler(command_cb.filter(action='kb_reparse_file'))
async def callback_reparse_file(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        job_state = get_printer_job_state()
        if job_state.success:
            await query.answer("Высчитывание высот для файла..")
            parse_file_for_offsets(job_state.data['job']['file']['name'])
            await bot.send_message(query.message.chat.id,'Высоты по файлу '+job_state.data['job']['file']['name']+' обновлены')
        else:
            await query.answer("Файл для печати не выбран!")

#action callback
@dp.callback_query_handler(text_contains='action_')
async def callback_action_query(query: types.CallbackQuery):
    if check_user(query.message.chat.id):
        await query.answer()
        source = None
        command = None

        global last_msg

        if query.data.startswith('id:action_core_'):
            source = 'core'
            command = query.data[len('id:action_core_'):]

        if query.data.startswith('id:action_custom_'):
            source = 'custom'
            command = query.data[len('id:action_custom_'):]

        if source != None:
            commands_data = get_printer_commands(source)
            for c in commands_data.data:
                if c['action'] == command:
                    if 'confirm' in c:
                        kbd = types.InlineKeyboardMarkup().row(
                            types.InlineKeyboardButton('Выполнить', callback_data=command_cb.new(action='actionexecute|'+source+"|"+command)),
                            types.InlineKeyboardButton('Отменить', callback_data=command_cb.new(action='actionexecute|'+'cancel'))
                            )

                        await delete_last_msg()
                        last_msg = await bot.send_message(query.message.chat.id,'Запрос на выполнение команды:\n"'+c['confirm']+'"', reply_markup=kbd)
                        print('confirmation for '+c['name']+" "+source+" "+command)
                        return
                    else:
                        await delete_last_msg()
                        result = await execute_command(source+"/"+command)

                        if result.success == True:
                            await bot.send_message(query.message.chat.id,"Команда "+c['name'] + " выполнена")
                        else:
                            await bot.send_message(query.message.chat.id,"Команда "+c['name']+' (' +source+"/"+command+ ") не выполнена\nКод ошибки:"+result.errorCode)

                        print('execute command '+c['name']+" "+source+" "+command)
                        return

#action callback
@dp.callback_query_handler(text_contains='actionexecute|')
async def callback_action_query(query: types.CallbackQuery):
    if check_user(query.message.chat.id):
        await query.answer()
        global last_msg

        if query.data.startswith('id:actionexecute|'):
            data = query.data.split('|')
            print(data)
            if len(data) == 3:
                await delete_last_msg()

                result = await execute_command(data[1]+'/'+data[2])

                if result.success == True:
                    await bot.send_message(query.message.chat.id,"Команда "+data[1]+'/'+data[2] + " выполнена")
                else:
                    await bot.send_message(query.message.chat.id,"Команда "+data[1]+'/'+data[2] + " не выполнена\nКод ошибки:"+result.errorCode)
                print('execute command '+data[1]+' '+data[2])
            elif len(data) == 2 and data[1] == 'cancel':
                await delete_last_msg()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(10, repeat, coro, loop)

if __name__ == '__main__':
    parse_file_for_offsets('nullprint.gcode')
    print(get_current_z_pos_with_range(297))
    loop = asyncio.get_event_loop()
    loop.call_later(10, repeat, update_printer_status, loop)
    executor.start_polling(dp, skip_updates=True)
    print('Goodbye')

