"""
Timeclock server address
"""
hostname = 'localhost'
port = '8000'

"""
Authorization of the timeclock's server special terminal user
"""
terminal_id = '3'
api_key = 't2GjYrSyYNqsoYag-Bqv'

"""
Locale has to be installed on the system
Languages currently supported: de, en
"""
locale = 'en_US.utf8'
lang = 'en'

"""
RFID device
/dev/spidevbus.device
e.g.: /dev/spidev1.0
irq = GPIO connected to interrupt pin RC522
rst = GPIO connected to reset pin RC522
"""
bus = 1
device = 0
irq = 36
rst = 37
