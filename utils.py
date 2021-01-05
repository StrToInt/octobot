import requests
import subprocess
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from dataclasses import dataclass
import json
from aiogram import types
from aiogram.utils.callback_data import CallbackData

@dataclass
class Print_File_Data:
    start_time = None
    last_z_pos = -1.0
    max_z_pos = -1.0
    last_z_time = None
    common_layer_time = None
    file_name = ''
    offsets = {}

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

class utils:

    callback = CallbackData('id','action')  # post:<id>:<action>

    #parse file for Z offsets
    @staticmethod
    def parse_file_for_offsets(name, files_dir, max_z_finish):
        file_pos = 0
        max_z = -1.0
        max_z_finish = max_z_finish
        new_file_data = Print_File_Data()
        new_file_data.offsets = {}
        new_file_data.file_name = name
        new_file_data.start_time = datetime.now()
        new_file_data.common_layer_time = None
        new_file_data.last_z_time = None
        print('Parsing file for offsets: '+ name)
        with open(files_dir+name, 'r') as fp:
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
        return new_file_data
        print(new_file_data.offsets)
        print('max_Z = '+str(max_z))



    #get current Z pos from file with layers range
    @staticmethod
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
    @staticmethod
    def get_current_z_pos(offset):
        return get_current_z_pos_with_range(offset)[0]

    #get z position as string with max and percentage
    @staticmethod
    def get_z_pos_str():
        return

    #get printer status
    @staticmethod
    def get_printer_connection_status(testmode = True):
        status = Printer_Connection()
        if testmode:
            status.success = True
            status.errorCode = 200
            status.state = 'Operational'
            return status

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
    @staticmethod
    def get_printer_state(testmode = True):
        state = Printer_State()

        if testmode:
            state.success = True
            state.errorCode = 200
            state.data = json.loads('{   "temperature": {     "tool0": {       "actual": 214.8821,       "target": 220.0,       "offset": 0     },     "tool1": {       "actual": 25.3,       "target": null,       "offset": 0     },     "bed": {       "actual": 50.221,       "target": 70.0,       "offset": 5     },     "history": [       {         "time": 1395651928,         "tool0": {           "actual": 214.8821,           "target": 220.0         },         "tool1": {           "actual": 25.3,           "target": null         },         "bed": {           "actual": 50.221,           "target": 70.0         }       },       {         "time": 1395651926,         "tool0": {           "actual": 212.32,           "target": 220.0         },         "tool1": {           "actual": 25.1,           "target": null         },         "bed": {           "actual": 49.1123,           "target": 70.0         }       }     ]   },   "sd": {     "ready": true   },   "state": {     "text": "Operational",     "flags": {       "operational": true,       "paused": false,       "printing": false,       "cancelling": false,  "resuming": false,       "pausing": false,       "sdReady": true,       "error": false,       "ready": true,       "closedOrError": false     }   } }')
            return state

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
    @staticmethod
    def get_printer_job_state(testmode = True):
        job_state = Printer_State()

        if testmode:
            job_state.success = True
            job_state.errorCode = 200
            job_state.data = json.loads('{   "job": {     "file": {       "name": "whistle_v2.gcode",       "origin": "local",       "size": 1468987,       "date": 1378847754     },     "estimatedPrintTime": 8811,     "filament": {       "tool0": {         "length": 810,         "volume": 5.36       }     }   },   "progress": {     "completion": 0.2298468264184775,     "filepos": 337942,     "printTime": 276,     "printTimeLeft": 912   },   "state": "Printing" }')
            return job_state

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
    @staticmethod
    def execute_command(path, testmode = True):
        print('Execute command '+ '/api/system/commands/'+path)
        result = Printer_State()

        if testmode:
            result.success = True
            result.errorCode = 204
            return result

        try:
            r = requests.post(url = config.get("main", "octoprint")+'/api/system/commands/'+path, headers = {'X-Api-Key':config.get("main", "key")},timeout=8)
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


    #execute command
    @staticmethod
    def execute_job_command(command):
        print('Execute job command: '+command)
        result = Printer_State()
        try:
            r = requests.post(url = config.get("main", "octoprint")+'/job/command', json = {'command': command}, headers = {'X-Api-Key':config.get("main", "key")},timeout=8)
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

    #execute gcode
    @staticmethod
    def execute_gcode(commands):
        print('Execute gcode command: '+command)
        result = Printer_State()
        try:
            r = requests.post(url = config.get("main", "octoprint")+'/api/printer/command',json = {'commands':commands}, headers = {'X-Api-Key':config.get("main", "key")},timeout=8)
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
    @staticmethod
    def get_printer_commands(source = 'core', testmode = True):
        printer_commands = Printer_State()

        if testmode:
            printer_commands.success = True
            printer_commands.errorCode = 200
            printer_commands.data = json.loads('[     {       "action": "shutdown",       "name": "Shutdown",       "confirm": "<strong>You are about to shutdown the system.",       "source": "core",       "resource": "http://example.com/api/system/commands/core/shutdown"     },     {       "action": "reboot",       "name": "Reboot",       "confirm": "<strong>You are about to reboot the system.om your printers internal storage).",       "source": "core",       "resource": "http://example.com/api/system/commands/core/reboot"     },     {       "action": "restart",       "name": "Restart OctoPrint",       "confirm": "<strong>You are about to restart the OctoPrint).",       "source": "core",       "resource": "http://example.com/api/system/commands/core/restart"     } ]')
            return printer_commands

        try:
            r = requests.get(url = config.get("main", "octoprint")+'/api/system/commands/'+source, headers = {'X-Api-Key':config.get("main", "key")},timeout=5)

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



    #get printer status text
    @staticmethod
    def get_printer_status_string():
        photo_cation = 'Фото '
        global print_file
        connection_status = utils.get_printer_connection_status()
        msg = datetime.now().strftime('%d.%m.%Y %H:%M')+'\n'
        if connection_status.success:
            if connection_status.state in ['Closed','Offline']:
                msg += '❌ Принтер выключен'
                print('11111')
            else:
                msg += '✅ Принтер включен\n'
                printer_state = utils.get_printer_state()
                if printer_state.success:
                    msg += '🔥Стол: ' + utils.str_round(printer_state.data['temperature']['bed']['actual'])+'° / '+\
                                        utils.str_round(printer_state.data['temperature']['bed']['target'])+'° Δ'+\
                                        utils.str_round(printer_state.data['temperature']['bed']['offset'])+'°'+'\n'
                    msg += '🔥Экструдер: '+ utils.str_round(printer_state.data['temperature']['tool0']['actual'])+'° / '+\
                                            utils.str_round(printer_state.data['temperature']['tool0']['target'])+'°? Δ'+\
                                            utils.str_round(printer_state.data['temperature']['tool0']['offset'])+'°'+'\n'
                    if ( (printer_state.data['state']['flags']['printing'] == True) or
                    (printer_state.data['state']['flags']['pausing'] == True) or
                    (printer_state.data['state']['flags']['paused'] == True) or
                    (printer_state.data['state']['flags']['resuming'] == True) or
                    (printer_state.data['state']['flags']['cancelling'] == True) ):
                        #get job state if printing
                        job_state = utils.get_printer_job_state()
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
                                msg += '\n⏱ Расчетное время печати: '+utils.user_friendly_seconds(job_state.data['job']['estimatedPrintTime'])
                            _z = utils.get_current_z_pos_with_range(job_state.data['progress']['filepos'])

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
                            msg += '\n⏰ Время печати: '+utils.user_friendly_seconds(job_state.data['progress']['printTime'])
                            msg += '\n⏰ Осталось: '+utils.user_friendly_seconds(job_state.data['progress']['printTimeLeft'])
                            time_end = datetime.now() + timedelta(seconds = job_state.data['progress']['printTimeLeft'])
                            msg += '\n⏰ Закончится: '+time_end.strftime('%d.%m.%Y %H:%M')
                        else:
                            msg += '🆘Ошибка получения данных о печати'
                else:
                    msg += '🆘Ошибка получения данных о статусе'

                add_info = utils.get_additional_file_strings()
                if add_info != None:
                    msg += '\n'+add_info

                return [1,msg]

            add_info = utils.get_additional_file_strings()
            if add_info != None:
                msg += '\n'+add_info
            return [1,msg]
        else:
            return [0,connection_status.errorCode]

        return [-1,'']

    @staticmethod
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

    def get_settings_keyboard(settings):
        command_cb = CallbackData('id','action')  # post:<id>:<action>

        return types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton(utils.get_smile_for_boolean(settings.is_silent())+' Беззвук', callback_data=utils.callback.new(action='kb_silent_toggle'))
        ).row(
            types.InlineKeyboardButton(utils.get_smile_for_boolean(settings.is_silent_z())+' Беззвук на изменение Z', callback_data=utils.callback.new(action='kb_z_silent_toggle')),
        ).row(
            types.InlineKeyboardButton('Назад', callback_data=utils.callback.new(action='kb_show_keyboard')),
        )

    @staticmethod
    def get_show_keyboard_button():
        command_cb = CallbackData('id','action')  # post:<id>:<action>

        return types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('⌨️Показать клавиатуру', callback_data=utils.callback.new(action='kb_show_keyboard')),
        )

    @staticmethod
    def user_friendly_seconds(n):
        return str(timedelta(seconds = n,microseconds=0, milliseconds=0))

    @staticmethod
    def str_round(number):
        return str(round(number,2))


    #boolean smile
    @staticmethod
    def get_smile_for_boolean(inp):
        return '✅' if inp == True else '❌'

    #boolean on/off
    @staticmethod
    def get_smile_for_boolean_str(inp):
        return 'вкл' if inp == True else 'выкл'

    #get file size
    @staticmethod
    def get_file_size(path):
        try:
            return os.path.getsize(path)
        except:
            return -1

    @staticmethod
    def get_image_path(path):
        size = get_file_size(path)
        if size <= 0:
            return 'noimage.jpeg'
        else:
            return path