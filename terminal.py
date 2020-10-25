import time
import locale
from os import popen
from threading import Thread
from gettext import translation

from kivy.app import App
from kivy import require
from kivy.clock import Clock
from kivy.config import Config
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty

from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager, Screen

import config
from dataprovider import DataProvider
from rfidprovider import RfidProvider

require('1.11.1')


def _(*args):
    """
    Translator
    :param args: text to translate
    :return: translated text
    """
    return App.get_running_app().get_text(*args)


def change_screen(name, data=None):
    """
    Show another screen of the app
    :param name: name of the screen (terminal.kv)
    :param data: data to show on the selected screen
    :return: None
    """
    app = App.get_running_app()
    app.root.current = name
    if data:
        app.root.get_screen(name).show(data)


def show_user(tag):
    """
    Shows user info screen
    :param tag: serial number
    :return: None
    """
    change_screen('user', tag)


def show_error(message):
    """
    Shows error screen
    :param message: text to show
    :return: None
    """
    change_screen('error', message)


class CurrentWorkingWidget(StackLayout):
    """
    Shows the currently working employees in a table
    """

    def __init__(self, **kwargs):
        """
        Starts update thread every 15 seconds
        :param kwargs: kivy
        """
        super(CurrentWorkingWidget, self).__init__(**kwargs)
        self.widget_list = []
        self.worker = None
        Clock.schedule_interval(self.start_thread, 15)
        self.start_thread()

    def start_thread(self, *args):
        """
        Checks if update thread is running and starts it if not
        :param args: kivy
        :return: None
        """
        if self.worker and self.worker.is_alive():
            Logger.warning('Terminal: Update thread for working users is still running')
        else:
            self.worker = Thread(target=self.update_widgets)
            self.worker.start()

    def update_widgets(self, *args):
        """
        Update Label widgets without removing them (no flickering on RPI Zero W)
        by diffing current and new widgets. Adding and removing in main thread via
        kivy's schedule_once()
        :param args: kivy things
        :return: None
        """
        new_widgets = []
        working = dp.working_users()
        if len(working) > 0:
            for name, clock_in, user_id in working:
                if name is None:
                    name = _('Unknown ') + user_id
                item = Label(text_size=(250, 40), halign='left', font_size='20sp',
                             size_hint=(0.3, 0.01), text=clock_in + ' ' + name)
                new_widgets.append(item)

        remove = self.widget_list.copy()
        for old in self.widget_list:
            for new in new_widgets:
                if old.text == new.text:
                    remove.remove(old)

        add = new_widgets.copy()
        for new in new_widgets:
            for old in self.widget_list:
                if old.text == new.text:
                    add.remove(new)

        Clock.schedule_once(lambda x: self.remove_working_employees(remove), 0)
        Clock.schedule_once(lambda x: self.add_working_employees(add), 0)

    def add_working_employees(self, items):
        """
        Adds labels to table and to internal list
        :param items: labels
        :return: None
        """
        for item in items:
            self.add_widget(item)
            self.widget_list.append(item)

    def remove_working_employees(self, items):
        """
        Removes labels from table and from internal list
        :param items: labels
        :return: None
        """
        for item in items:
            self.remove_widget(item)
            self.widget_list.remove(item)


class ClockWidget(ButtonBehavior, BoxLayout):
    """
    Home screen clock
    """
    hours_minutes = StringProperty()
    seconds = StringProperty()
    date_string = StringProperty()

    def __init__(self, **kwargs):
        """
        Schedules clock update for every second
        :param kwargs: kivy
        """
        super(ClockWidget, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_time, 1)
        self.update_time()
        self.press_time = time.time()
        self.press_counter = 0

    def update_time(self, *args):
        """
        Updates current time
        :param args: kivy
        :return: None
        """
        self.hours_minutes = time.strftime('%H:%M', time.localtime())
        self.seconds = time.strftime('%S', time.localtime())
        self.date_string = time.strftime('%A, %d. %b %Y', time.localtime())

    def on_press(self):
        """
        Hidden admin screen, press 3 times in 5 seconds to get there
        :return: None
        """
        current_time = time.time()
        if current_time - self.press_time < 5:
            self.press_counter += 1
            if self.press_counter == 3:
                self.press_counter = 0
                change_screen('admin', None)
        else:
            self.press_counter = 1
            self.press_time = time.time()


class BackButton(ButtonBehavior, Image):
    pass


class HomeScreen(Screen):
    """
    Home screen with clock and currently working employees
    """
    current_working = ObjectProperty()

    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.worker = None

    def on_enter(self, *args):
        """
        Starts thread that waits for a RFID tag
        :param args: kivy
        :return: None
        """
        if self.worker and self.worker.is_alive():
            Logger.warning('Terminal: Rfid worker thread not exited correctly (coming from admin screen?)')
        else:
            self.worker = Thread(target=self.read_rfid_tag, daemon=True)
            self.worker.start()

    def read_rfid_tag(self, *args):
        """
        Thread waiting for RFID tag, updates UI in main thread
        :param args: kivy
        :return: None
        """
        uid = rp.read_uid()
        if not uid or self.manager.current != 'home':
            return
        Clock.schedule_once(lambda x: show_user(uid), 0)


class UserScreen(Screen):
    """
    User screen with image, info about worked hours and arrive/leave buttons
    """
    welcome = StringProperty()
    today_hours = StringProperty()
    week_hours = StringProperty()
    last_week_hours = StringProperty()
    holidays = StringProperty()
    user_image = StringProperty()

    def __init__(self, **kwargs):
        super(UserScreen, self).__init__(**kwargs)
        self.user_id = None
        self.worker = None

    def show(self, tag):
        """
        Updates properties with current user data and
        starts thread to load info about worked hours later
        :param tag: serial number
        :return: None
        """
        self.today_hours = ''
        self.week_hours = ''
        self.last_week_hours = ''
        self.holidays = ''

        resp = dp.user_info(tag)
        if not resp:
            show_error(_('User does not exist: ') + str(tag))
            return

        self.welcome = _('Hello ') + resp[0].split(' ')[0] + '!'
        self.user_image = resp[1]
        self.user_id = resp[2]

        if self.worker and self.worker.is_alive():
            Logger.error('Terminal: Get user data thread is still running')
        else:
            self.worker = Thread(target=self.get_data, daemon=True)
            self.worker.start()

    def get_data(self):
        """
        Retrieves info about worked hours, update of UI in main thread
        :return: None
        """
        resp = None
        if self.user_id:
            resp = dp.user_work_summary(self.user_id)
        if not resp:
            return
        Clock.schedule_once(lambda x: self.update_user_data(resp), 0)

    def update_user_data(self, data):
        """
        Updates UI with given data
        :param data: array with worked minutes and vacation days
        :return: None
        """
        self.today_hours = "{:02d}".format(int(data[0] / 60)) + ':' + "{:02d}".format(data[0] % 60) + ' h'
        self.week_hours = "{:02d}".format(int(data[1] / 60)) + ':' + "{:02d}".format(data[1] % 60) + ' h'
        self.last_week_hours = "{:02d}".format(int(data[2] / 60)) + ':' + "{:02d}".format(data[2] % 60) + ' h'
        self.holidays = str(data[3]) + _(' Days')

    def clock_in(self):
        """
        Clocks in user and shows error or welcome/goodbye screen
        :return: None
        """
        if self.user_id:
            ret = dp.clock_in(self.user_id)
            if ret:
                change_screen('clock')
                screen = self.parent.get_screen('clock')
                screen.show(True)
            elif ret is False:
                show_error(_('Your are already clocked in.'))
            else:
                show_error(_('Server error. Could not clock in user. ID: ') + str(self.user_id))
        else:
            Logger.error('Terminal: no user id set to clock in')

    def clock_out(self):
        """
        Clocks out user and shows error or welcome/goodbye screen
        :return: None
        """
        if self.user_id:
            ret = dp.clock_out(self.user_id)
            if ret:
                change_screen('clock')
                screen = self.parent.get_screen('clock')
                screen.show(False)
            elif ret is False:
                show_error(_('Your are already clocked out.'))
            else:
                show_error(_('Server error. Could not clock out user. ID: ') + str(self.user_id))
        else:
            Logger.error('Terminal: no user id set to clock out')


class ClockInOutScreen(Screen):
    """
    Welcome and goodbye screen
    """
    current_time = StringProperty()
    message = StringProperty()
    image = StringProperty()

    def __init__(self, **kwargs):
        super(ClockInOutScreen, self).__init__(**kwargs)
        self.timer = None

    def back(self):
        """
        Back button, cancels automatic back
        :return: None
        """
        if self.timer:
            self.timer.cancel()
        change_screen('home')

    def show(self, clock_in):
        """
        Shows Welcome/Goodbye message with door image and
        starts timer to go back after 3 seconds
        :param clock_in: True if user clocked in
        :return: None
        """
        self.current_time = time.strftime('%H:%M Uhr', time.localtime())
        if clock_in:
            self.image = 'images/clockin.png'
            self.message = _('Welcome!')
        else:
            self.image = 'images/clockout.png'
            self.message = _('Goodbye!')
        App.get_running_app().root.get_screen('home').current_working.start_thread()
        self.timer = Clock.schedule_once(lambda x: change_screen('home'), 3)


class ErrorScreen(Screen):
    message = StringProperty()

    def show(self, message):
        """
        Shows error message
        :param message: error message
        :return: None
        """
        self.message = message

    @staticmethod
    def back():
        """
        Back button
        :return: None
        """
        change_screen('home')


class AdminScreen(Screen):
    message = StringProperty()

    def on_enter(self, *args):
        """
        Shows time and all IP addresses
        :param args: kivy
        :return: None
        """
        t = time.strftime("%a, %d %b %Y %H:%M:%S")
        ips = popen('hostname -I').read().split(' ')
        i = '\n'.join(ips)
        self.message = t + '\n' + i

    @staticmethod
    def back():
        """
        Back button
        :return: None
        """
        change_screen('home')


class GlobalScreenManager(ScreenManager):
    """
    Manager for different screens
    """

    @staticmethod
    def build():
        return ScreenManager()


class Terminal(App):
    """
    Main app
    """

    def __init__(self, lang):
        """
        Initializes kivy app and sets language
        :param lang: supported language e.g. 'de'
        """
        super().__init__()
        self.lang = translation('terminal', localedir='lang', languages=[lang], fallback=True)

    def build(self):
        """
        Sets window settings and starts ScreenManager with first screen (home)
        :return: GlobalScreenManager
        """
        # set configuration
        Config.set('graphics', 'resizable', False)
        Config.set('graphics', 'borderless', True)
        Config.set('graphics', 'height', 480)
        Config.set('graphics', 'width', 800)
        Config.set('graphics', 'show_cursor', '0')
        locale.setlocale(locale.LC_ALL, config.locale)

        return GlobalScreenManager()

    def on_stop(self):
        """
        Graceful exit
        :return: None
        """
        Logger.info('Terminal: GPIO cleanup and exit')
        rp.cleanup()

    def get_text(self, *args):
        """
        Translation
        :param args: text
        :return: translated text
        """
        return self.lang.gettext(*args)


if __name__ == '__main__':
    try:
        dp = DataProvider(config.hostname, config.port, config.terminal_id, config.api_key)
        rp = RfidProvider(config.bus, config.device, config.irq, config.rst)
        Terminal(config.lang).run()
    except KeyboardInterrupt:
        App.get_running_app().stop()
