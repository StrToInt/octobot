import requests
import subprocess
import asyncio
from datetime import datetime, timedelta
from threading import Thread

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
    @staticmethod
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
    @staticmethod
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
    @staticmethod
    async def execute_command(path):
        print('Execute command '+ '/api/system/commands/'+path)
        result = Printer_State()
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
    async def execute_job_command(command):
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
    async def execute_gcode(commands):
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



    #get printer status text
    @staticmethod
    async def get_printer_status_string(self):
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