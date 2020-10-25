# Hardware
Used standard hardware combined with a 3D printed case.

## List
- [Waveshare 5 inch HDMI touchscreen](https://www.waveshare.com/wiki/5inch_HDMI_LCD)
- [Raspberry Pi Zero W](https://www.raspberrypi.org/products/raspberry-pi-zero-w/)
- RC522 RFID Module
- LM2596S DC/DC Converter
- [12V DC socket (2,1 x 5,5 mm M8)](https://www.segor.de/#Q=DCBU2%252C5%252F5%252C5Z-M8&M=1)
- 12V power supply

## Connecting
Touchscreen on SPI0

| Touchscreen   | RPI Board Pin | Power Supply |
|---------------|---------------|--------------|
| 5V            | -             | 5V           |
| GND           | 6             | GND          |
| MOSI          | 19            | -            |
| MISO          | 21            | -            |
| SCK           | 23            | -            |
| P6            | 22            | -            |
| CE1           | 26            | -            |
| HDMI          | HDMI          | -            |

RC522 on SPI1

| RC522   | RPI Board Pin |
|---------|---------------|
| SDA     | 12            | 
| SCK     | 40            | 
| MOSI    | 38            | 
| MISO    | 35            | 
| IRQ     | 36            | 
| GND     | 39            | 
| RST     | 37            | 
| 3.3V    | 1             |


## Case
You can 3D print a case. There is a ```front.stl```, ```back.stl```, ```spacer.stl``` (between screw and touchscreen) 
and ```rc522_holder.stl``` in the ```hardware/stl/``` folder. Settings for Ender 3:
```
Layer Height: 0.2mm
Wall thickness: 1.2mm
Infill: 50%
Speed: 50mm/s
```

Used Screws:
- [2.9 x 6.5 mm self-tapping screw](https://www.bauhaus.info/blech-metall-spenglerschrauben/stabilit-blechschraube/p/10775854)
- [3.5 x 9.5 mm self-tapping screw](https://www.bauhaus.info/blech-metall-spenglerschrauben/stabilit-blechschraube/p/10775892)

## Advices
1. LM2596S module failed and I replaced it with an external 5V 3A power supply.
2. Replaced thread screws of the case with self-tapping screws.

## Photos
TODO