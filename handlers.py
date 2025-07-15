from asyncio import sleep
from json import loads

from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile, URLInputFile
from ping3 import ping
from requests import post

from buttons import *
from config import rt, cam_host, image_high, image_low, bot, ipconfig, restart
from video import start_streaming, stop_streaming


# Функция для управления камерой
async def control_camera(args):
    if len(args) == 2:
        match args[1]:
            case 'left' | 'left_2s' | 'left_1s' | 'left_micro':
                direction = 'left'
            case 'right' | 'right_2s' | 'right_1s' | 'right_micro':
                direction = 'right'
            case 'up' | 'up_micro':
                direction = 'up'
            case 'down' | 'down_micro':
                direction = 'down'

        match args[1]:
            case 'left' | 'right':
                duration = 3.45
                wait = 0.25
            case 'left_2s' | 'right_2s':
                duration = 1.65
                wait = 0.2
            case 'left_1s' | 'right_1s' | 'up' | 'down':
                duration = 0.9
                wait = 0.2
            case 'left_micro' | 'right_micro' | 'up_micro' | 'down_micro':
                duration = 0.2
                wait = 0.0

    url = f'http://{cam_host}/cgi-bin/ptz.sh?dir={direction}&time={duration}'
    post(url)

    return wait


def case_yes_no(text):
    args = text.split(maxsplit=1)
    match args[1]:
        case 'on':
            arg = 'yes'
        case 'off':
            arg = 'no'
    return arg


# Обработчики команд
@rt.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Здравствуйте, {message.from_user.full_name}!", reply_markup=menu.as_markup())


@rt.message(Command('Back'))
async def cmd_back(message: Message):
    await message.answer('Ok', reply_markup=menu.as_markup())


@rt.message(Command('back'))
async def cmd_back1(message: Message):
    await message.answer('Ok', reply_markup=settings.as_markup())


@rt.message(Command('Reboot'))
async def cmd_reboot(message: Message):
    await message.answer('Ok', reply_markup=reboot.as_markup())


@rt.message(Command('Moves'))
async def cmd_moves(message: Message):
    await message.answer('Ok', reply_markup=moves.as_markup())


@rt.message(Command('Presets'))
async def cmd_presets(message: Message):
    await message.answer('Ok', reply_markup=presets.as_markup())


@rt.message(Command('Photos'))
async def cmd_photos(message: Message):
    await message.answer('Ok', reply_markup=photos.as_markup())


@rt.message(Command('Streams'))
async def cmd_streams(message: Message):
    await message.answer('Ok', reply_markup=streams.as_markup())


@rt.message(Command('Settings'))
async def cmd_settings(message: Message):
    await message.answer('Ok', reply_markup=settings.as_markup())


@rt.message(Command('Power'))
async def cmd_power(message: Message):
    await message.answer('Ok', reply_markup=power.as_markup())


@rt.message(Command('Led'))
async def cmd_led(message: Message):
    await message.answer('Ok', reply_markup=led.as_markup())


@rt.message(Command('Rotate'))
async def cmd_rotate(message: Message):
    await message.answer('Ok', reply_markup=rotate.as_markup())


# Обработчик команды /move
@rt.message(Command('move'))
async def move_command(message: Message):
    chat_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    wait = await control_camera(args)
    await sleep(wait)
    await bot.send_photo(chat_id, image_low)


@rt.message(Command('power'))
async def command_power(message: Message):
    arg = case_yes_no(text=message.text)
    url = f'http://{cam_host}/cgi-bin/camera_settings.sh?switch_on={arg}'
    post(url)


@rt.message(Command('led'))
async def command_led(message: Message):
    arg = case_yes_no(text=message.text)
    url = f'http://{cam_host}/cgi-bin/camera_settings.sh?led={arg}'
    post(url)


@rt.message(Command('rotate'))
async def command_rotate(message: Message):
    arg = case_yes_no(text=message.text)
    url = f'http://{cam_host}/cgi-bin/camera_settings.sh?rotate={arg}'
    post(url)


@rt.message(Command('Get_photo'))
async def photo_command(message: Message):
    chat_id = message.from_user.id
    await bot.send_photo(chat_id, image_high)


@rt.message(Command('Force_get_photo'))
async def low_photo_command(message: Message):
    chat_id = message.from_user.id
    await bot.send_photo(chat_id, image_low)


@rt.message(Command('Full_left'))
async def full_left(message: Message):
    chat_id = message.from_user.id
    url = f'http://{cam_host}/cgi-bin/preset.sh?action=go_preset&num=0'
    post(url)
    await sleep(10)
    await bot.send_photo(chat_id, image_low)


@rt.message(Command('Full_right'))
async def full_right(message: Message):
    chat_id = message.from_user.id
    url = f'http://{cam_host}/cgi-bin/preset.sh?action=go_preset&num=1'
    post(url)
    await sleep(10)
    await bot.send_photo(chat_id, image_low)


@rt.message(Command('Home'))
async def to_home(message: Message):
    chat_id = message.from_user.id
    url = f'http://{cam_host}/cgi-bin/preset.sh?action=go_preset&num=2'
    post(url)
    await sleep(6)
    await bot.send_photo(chat_id, image_high)


@rt.message(Command('stream'))
async def start_live_stream(message: Message):
    await message.answer('Стрим начат.')
    await start_streaming(message.from_user.id)


@rt.message(Command('stop_stream'))
async def stop_stream(message: Message):
    await message.answer('Стрим остановлен.')
    await stop_streaming()


@rt.message(Command('Ping'))
async def ping_func(message: Message):
    await message.answer(f"Ping to {cam_host}:\n{str(ping(cam_host, unit="ms"))} Ms")


@rt.message(Command('Edit_ip'))
async def ip_func(message: Message):
    await message.answer('Введите новый ip, \n после этого код перезагрузится.')
    while True:
        @rt.message()
        async def config(message: Message):
            ipconfig(message.text)

        break


@rt.message(Command('reboot_main'))
async def reboot1(message: Message):
    await sleep(2)
    await message.answer('Ok')
    restart('main')


@rt.message(Command('reboot_os'))
async def reboot2(message: Message):
    await sleep(2)
    await message.answer('Ok')
    restart('os')


@rt.message(Command('reboot_cam'))
async def reboot3(message: Message):
    await message.answer('Ok')
    restart('cam')


@rt.message(Command('Stats'))
async def stats(message: Message):
    request = loads(post(f'http://{cam_host}/cgi-bin/get_configs.sh?conf=camera').text)
    await message.answer(f"""
Ip: {cam_host}
SWITCH_ON: {request["SWITCH_ON"]}
Led: {request["LED"]}
Rotate: {request["ROTATE"]}
""")
