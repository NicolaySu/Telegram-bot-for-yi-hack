from json import load, dump
from os import path, execv
from subprocess import run
from sys import argv, exit, executable
from time import sleep

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import URLInputFile
from requests import post

CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), "config.json")

# Шаблон конфигурации (на случай, если файл отсутствует)
DEFAULT_CONFIG = {
    "bot_token": "",
    "cam_host": "",
    "allowed_users": [],
    "debug": 1,
    "admin_id": None
}

# Конфигурация бота
if path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = load(f)
        TOKEN = config["bot_token"]
        cam_host = config["cam_host"]
        allowed_users = config["allowed_users"]
        debug = config["debug"]
        admin_id = config["admin_id"]

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='html'))
    dp = Dispatcher()
    rt = Router()

    # Объекты фото
    HiRes_PHOTO_URL = f'http://{cam_host}/cgi-bin/snapshot.sh?res=high&watermark=no'
    LowRes_PHOTO_URL = f'http://{cam_host}/cgi-bin/snapshot.sh?res=low&watermark=no'
    image_high = URLInputFile(HiRes_PHOTO_URL, filename='photo_high')
    image_low = URLInputFile(LowRes_PHOTO_URL, filename='photo_low')

else:  # Создание конфига по шаблону, если он отсутствует
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        dump(DEFAULT_CONFIG, f, indent=4)
    print('JSON не заполнен!!!')
    exit(1)


def restart(target):
    match target:
        case 'main':
            execv(executable, [executable] + argv)
        case 'os':
            run(["sudo", "reboot"])  # только Linux
        case 'cam':
            post(f'http://{cam_host}/cgi-bin/reboot.sh')


def ipconfig(ip):
    with open(CONFIG_PATH, "r+", encoding="utf-8") as f:
        data = load(f)
        data["cam_host"] = ip
        f.seek(0)
        dump(data, f, indent=4)
        f.truncate()
        sleep(3)
        restart('main')
