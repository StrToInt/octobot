from pprint import pprint
import ruamel.yaml
from ruamel.yaml import YAML
import sys

class YamlObject(YAML):
    def __init__(self):
        YAML.__init__(self)
        self.default_flow_style = True
        self.block_seq_indent = 0
        self.indent = 2
        self.allow_unicode = True
        self.encoding = 'utf-8'

class OctobotSettings:


    def __init__(self, filepath):
        self.__filepath = filepath
        self.__yaml = YamlObject()

    def reload(self):
        with open(self.__filepath, 'r', encoding="utf-8") as f:
            self.__yaml_data = self.__yaml.load(f)
        self.__yaml.dump(self.__yaml_data, sys.stdout)
        return self

    def save(self):
        with open(self.__filepath, 'w', encoding="utf-8") as f:
            self.__yaml.dump(self.__yaml_data, f)
        return self

    def show_all(self):
        return pyaml.dump(self.__yaml_data)

    def get_admin(self):
        return self.__yaml_data['main']['admin']

    def get_files_dir(self):
        return self.__yaml_data['main']['filesdir']

    def get_api_key(self):
        return self.__yaml_data['main']['key']

    def get_octoprint_url(self):
        return self.__yaml_data['main']['octoprint']

    def get_bot_token(self):
        return self.__yaml_data['main']['token']

    def is_silent(self):
        return self.__yaml_data['misc']['silent']

    def is_silent_photos(self):
        return self.__yaml_data['misc']['silent_photos']

    def is_silent_z_change(self):
        return self.__yaml_data['misc']['silent_z_change']

    def toggle_silent(self):
        self.__yaml_data['misc']['silent'] = not self.__yaml_data['misc']['silent']
        self.save()

    def toggle_silent_photos(self):
        self.__yaml_data['misc']['silent_photos'] = not self.__yaml_data['misc']['silent_photos']
        self.save()

    def toggle_silent_z_change(self):
        self.__yaml_data['misc']['silent_z_change'] = notself .__yaml_data['misc']['silent_z_change']
        self.save()

    def get_cameras(self):
        return self.__yaml_data['printer']['cameras']

    def get_camera(self, number):
        return self.__yaml_data['printer']['cameras'][number]

    def cameras_count(self):
        return len(self.__yaml_data['printer']['cameras'])





    def check_user(self, user_id):
        if str(user_id) == str(self.get_admin()):
            return True
        else:
            return False


if __name__ == '__main__':
    s = OctobotSettings('config.yaml').reload().save()