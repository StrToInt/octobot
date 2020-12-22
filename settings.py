import yaml, pyaml
from pprint import pprint

class OctobotSettings:

    def __init__(self, filepath):
        self.__filepath = filepath
        self.reload()

    def reload(self):
        with open(self.__filepath) as f:
            self.__yaml_data = yaml.safe_load(f)

    def save(self):
        with open(self.__filepath, 'w') as f:
            yaml.dump(self.__yaml_data, f, default_flow_style=False)

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

    def check_user(self, user_id):
        if str(user_id) == str(self.get_admin()):
            return True
        else:
            return False

if __name__ == '__main__':
    s = OctobotSettings('config.yaml')
    print(s.show_all())