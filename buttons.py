from aiogram.utils.keyboard import ReplyKeyboardBuilder

menu = ReplyKeyboardBuilder()
menu.button(text="/Moves")
menu.button(text="/Presets")
menu.button(text="/Photos")
menu.button(text="/Streams")
menu.button(text="/Settings")
menu.adjust(2)

moves = ReplyKeyboardBuilder()
moves.button(text="/move left")
moves.button(text="/move right")
moves.button(text="/move left_2s")
moves.button(text="/move right_2s")
moves.button(text="/move left_1s")
moves.button(text="/move right_1s")
moves.button(text="/move left_micro")
moves.button(text="/move right_micro")
moves.button(text="/move up")
moves.button(text="/move down")
moves.button(text="/move up_micro")
moves.button(text="/move down_micro")
moves.button(text="/Back")
moves.adjust(2)

presets = ReplyKeyboardBuilder()
presets.button(text="/Full_left")
presets.button(text="/Home")
presets.button(text="/Full_right")
presets.button(text="/Back")
presets.adjust(3)

photos = ReplyKeyboardBuilder()
photos.button(text="/Get_photo")
photos.button(text="/Force_get_photo")
photos.button(text="/Back")
photos.adjust(2)

streams = ReplyKeyboardBuilder()
streams.button(text="/stream")
streams.button(text="/stop_stream")
streams.button(text="/Back")
streams.adjust(2)

settings = ReplyKeyboardBuilder()
settings.button(text="/Power")
settings.button(text="/Led")
settings.button(text="/Rotate")
settings.button(text="/Reboot")
settings.button(text="/Ping")
settings.button(text="/Edit_ip")
settings.button(text="/Stats")
settings.button(text="/Back")
settings.adjust(2)

power = ReplyKeyboardBuilder()
power.button(text="/power on")
power.button(text="/power off")
power.button(text="/back")
power.adjust(2)

led = ReplyKeyboardBuilder()
led.button(text="/led on")
led.button(text="/led off")
led.button(text="/back")
led.adjust(2)

rotate = ReplyKeyboardBuilder()
rotate.button(text="/rotate on")
rotate.button(text="/rotate off")
rotate.button(text="/back")
rotate.adjust(2)

reboot = ReplyKeyboardBuilder()
reboot.button(text="/reboot_main")
reboot.button(text="/reboot_os")
reboot.button(text="/reboot_cam")
reboot.button(text="/back")
reboot.adjust(3)
