from time import time
from hashlib import sha1
from kivy.logger import Logger
from requests import get, post
from datetime import datetime


class DataProvider:

    def __init__(self, host, port, terminal_id, auth):
        """
        Provides data taken from timeclock server
        :param host: IP address or hostname
        :param port: port number
        :param terminal_id: identifier of terminal user
        :param auth: authentication token of terminal user
        """
        self.host = host
        self.port = port
        self.terminal_id = terminal_id
        self.auth = auth
        self.employees = []
        self.last_update = 0
        self.__update_employees()

    def __update_employees(self):
        try:
            update = int(self.__get('update')['updated_at'])
            if self.last_update < update:
                self.last_update = update
                data = self.__get('users')
                for user in data:
                    image = 'data/empty.jpg'
                    if user['image']:
                        image = 'data/' + user['image']
                        self.__download_image(user['id'], 'data/' + user['image'])
                    self.employees.append({
                        'id': str(user['id']),
                        'name': user['name'],
                        'tag': user['tag'],
                        'picture': image
                    })
        except Exception as e:
            Logger.error('DataProvider: ' + str(e))

    def __get_user_data(self, desc, value):
        for item in self.employees:
            if item[desc] == value:
                return item
        return None

    def __header(self):
        timestamp = str(int(time()))
        sha = sha1()
        sha.update((timestamp + self.auth).encode('utf-8'))
        token = sha.hexdigest()
        return {'Authorization': 'Bearer ' + self.terminal_id + ':' + timestamp + ':' + token}

    def __url(self, endpoint):
        return 'http://' + self.host + ':' + self.port + '/api/terminal/' + endpoint

    def __get(self, endpoint, data=None):
        resp = get(self.__url(endpoint), headers=self.__header(), json=data)
        return resp.json()

    def __post(self, endpoint, data):
        return post(self.__url(endpoint), headers=self.__header(), json=data).json()

    def __download_image(self, user_id, path):
        resp = get(self.__url('image'), headers=self.__header(), json={'user_id': user_id})
        with open(path, 'wb') as file:
            file.write(resp.content)

    def user_info(self, tag):
        """
        Returns user data
        :param tag: rfid tag identifier
        :return: None or (name, picture path, user_id)
        """
        data = self.__get_user_data('tag', tag)
        if data:
            return data['name'], data['picture'], data['id']

    def user_work_summary(self, user_id):
        """
        Gets work summary from timeclock server
        :param user_id: identifier of timeclock user
        :return: None or (today, week, last_week, vacation)
        """
        try:
            data = self.__get('summary', {'user_id': user_id})
            return int(round(data['today'] / 60)), int(round(data['this_week'] / 60)), \
                   int(round(data['last_week'] / 60)), int(data['vacation'])
        except Exception as e:
            Logger.error('DataProvider: ' + str(e))
            return None

    def clock_in(self, user_id):
        """
        Clocks in user
        :param user_id: identifier of timeclock user
        :return: True if successful, False if already clocked in, None if error
        """
        try:
            if self.__post('in', {'user_id': user_id}) == True:
                return True
            else:
                return None
        except Exception as e:
            Logger.error('DataProvider: ' + str(e))
            return None

    def clock_out(self, user_id):
        """
        Clocks out user
        :param user_id: identifier of timeclock user
        :return: True if successful, False if not clocked in, None if error
        """
        try:
            if self.__post('out', {'user_id': user_id}) == True:
                return True
            else:
                return None
        except Exception as e:
            Logger.error('DataProvider: ' + str(e))
            return None

    def working_users(self):
        """
        Returns list of clocked in users
        :return: list of tuples (name, start, user_id)
        """
        # check if employee list needs an update (ugly)
        self.__update_employees()
        user_id_list = []
        try:
            data = self.__get('working')
            for item in data:
                name = None
                user = self.__get_user_data('id', str(item['user_id']))
                if user:
                    name = user['name']
                start = datetime.fromtimestamp(item['clock_in']).strftime('%H:%M')
                user_id_list.append((name, start, str(item['user_id'])))
        except Exception as e:
            Logger.error('DataProvider: ' + str(e))
        return user_id_list
