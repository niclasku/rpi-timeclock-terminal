from kivy.logger import Logger


class RfidProvider:

    def __init__(self, bus, device, irq, rst):
        """
        Initializes RFID device if needed library is installed.
        Running in developer mode if not.
        :param bus: SPI device's bus number
        :param device: SPI device's device number
        :param irq: GPIO connected to interrupt pin
        :param rst: GPIO connected to reset pin
        """
        self.dev_mode = False
        try:
            from pirc522 import RFID
            self.reader = RFID(bus=bus, device=device, pin_irq=irq, pin_rst=rst)
        except ImportError:
            Logger.warning('RfidProvider: Running in developer mode')
            self.dev_mode = True

    def read_uid(self):
        """
        Read tag UID
        :return: String id
        """
        if self.dev_mode:
            return
        try:
            while True:
                self.reader.wait_for_tag()
                (error, tag_type) = self.reader.request()
                if not error:
                    (error, uid) = self.reader.anticoll()
                    if not error:
                        return ''.join(str(x) for x in uid)
        except Exception as e:
            Logger.error('RfidProvider: ' + str(e))

    def cleanup(self):
        """
        Free the GPIOs
        :return: None
        """
        if self.dev_mode:
            return
        self.reader.cleanup()
