import asyncio
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import cv2
import requests
from aiogram import BaseMiddleware
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile, URLInputFile, Update
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Конфигурация бота
TOKEN = '*******'
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='html'))
dp = Dispatcher()

# Конфигурация камеры
cam_host = '*******'
RTSP_URL = f'rtsp://{cam_host}/ch0_1.h264'

RECORD_DURATION = 20  # Длительность видеофрагмента в секундах

# Ссылки на фото
HiRes_PHOTO_URL = f'http://{cam_host}/cgi-bin/snapshot.sh?res=high&watermark=no'
LowRes_PHOTO_URL = f'http://{cam_host}/cgi-bin/snapshot.sh?res=low&watermark=no'

# создание фото
image_high = URLInputFile(HiRes_PHOTO_URL, filename='snapshot_high.sh')
image_low = URLInputFile(LowRes_PHOTO_URL, filename='snapshot_low.sh')

# Путь к видеофайлам
VIDEO_FILE_1 = 'video1.mp4'
VIDEO_FILE_2 = 'video2.mp4'

video_queue = asyncio.Queue()  # Очередь для хранения видеофайлов
streaming = False  # Флаг для хранения текущего состояния стрима

allowed_user = {*******}  # allowed users


class UserFilterMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        if event.from_user.id not in allowed_user:
            await event.reply("Извините, но вы не можете пользоваться этим ботом.")
            return
        return await handler(event, data)


dp.message.middleware(UserFilterMiddleware())

# Кнопки
builder = ReplyKeyboardBuilder()
builder.button(text="/Moves")
builder.button(text="/Presets")
builder.button(text="/Photos")
builder.button(text="/Streams")
builder.button(text="/Settings")
builder.adjust(2)

moves = ReplyKeyboardBuilder()
moves.button(text="/move left")
moves.button(text="/move right")
moves.button(text="/move left_2s")
moves.button(text="/move right_2s")
moves.button(text="/move left_1s")
moves.button(text="/move right_1s")
moves.button(text="/move up")
moves.button(text="/move down")
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
settings.button(text="/Private_mode")
settings.button(text="/Power")
settings.button(text="/Led")
settings.button(text="/Rotate")
settings.button(text="/Reboot")
settings.button(text="/Back")
settings.adjust(2)

private = ReplyKeyboardBuilder()
private.button(text="/private on")
private.button(text="/private off")
private.button(text="/back")
private.adjust(2)

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


# Функция для записи видеофрагмента
def record_video(output_file):
    logger.info(f"Начало записи видео: {output_file}")
    while streaming:
        cap = cv2.VideoCapture(RTSP_URL)
        if not cap.isOpened():
            logger.error("Не удалось открыть RTSP поток")
            return False

        # Настройки видео записи
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, 25.0, (int(cap.get(3)), int(cap.get(4))))

        start_time = cv2.getTickCount()
        while (cv2.getTickCount() - start_time) / cv2.getTickFrequency() < RECORD_DURATION:
            ret, frame = cap.read()
            if not ret:
                logger.error("Не удалось получить кадр из RTSP потока")
                break
            out.write(frame)

        cap.release()
        out.release()

        # Проверка размера файла
        if os.path.getsize(output_file) == 0:
            logger.error(f"Видео файл пустой: {output_file}")
            return False

        logger.info(f"Запись видео завершена: {output_file}")
        return True


# Асинхронная функция для записи видео и добавления его в очередь
async def video_recorder(loop):
    with ThreadPoolExecutor(max_workers=1) as executor:
        video_index = 0
        while streaming:
            output_file = f'video_{video_index}.mp4'
            success = await loop.run_in_executor(executor, record_video, output_file)
            if success:
                await video_queue.put(output_file)
            video_index = (video_index + 1) % 2


# Асинхронная функция для отправки видео из очереди
async def video_sender(chat_id):
    while streaming:
        video_file = await video_queue.get()
        if video_file:
            logger.info(f"Отправка видео: {video_file}")
            try:
                video = FSInputFile(video_file)
                await bot.send_video(chat_id, video)
                os.remove(video_file)
                logger.info(f"Видео отправлено и удалено: {video_file}")
            except Exception as e:
                logger.error(f"Ошибка при отправке видео: {e}")
            finally:
                video_queue.task_done()


# Функция остановки стриминга
async def stop_stream(message: Message):
    global streaming
    if not streaming:
        await message.answer("Стрим не активен.")
        return

    logging.info("Остановка стрима...")
    streaming = False
    # Остановка задач записи и отправки видео
    # Ожидание завершения всех задач в очереди
    await video_queue.join()
    # Подготовка к выходу
    await bot.send_message(message.chat.id, "Стрим успешно остановлен.")


# Функция для управления камерой
async def control_camera(args):
    if len(args) == 2:
        match args[1]:
            case 'left' | 'left_2s' | 'left_1s':
                direction = 'left'
            case 'right' | 'right_2s' | 'right_1s':
                direction = 'right'
            case 'up':
                direction = 'up'
            case 'down':
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
            case _:
                await bot.send_message(chat_id, "Некорректная команда.")
                wait = 0.1

    url = f'http://{cam_host}/cgi-bin/ptz.sh?dir={direction}&time={duration}'
    requests.post(url)

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
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Здравствуйте, {message.from_user.full_name}!", reply_markup=builder.as_markup())


@dp.message(Command('Back'))
async def cmd_back(message: Message):
    await message.answer('Ok', reply_markup=builder.as_markup())


@dp.message(Command('back'))
async def cmd_back1(message: Message):
    await message.answer('Ok', reply_markup=settings.as_markup())


@dp.message(Command('Reboot'))
async def cmd_reboot():
    requests.post(f'http://{cam_host}/cgi-bin/reboot.sh')


@dp.message(Command('Moves'))
async def cmd_moves(message: Message):
    await message.answer('Ok', reply_markup=moves.as_markup())


@dp.message(Command('Presets'))
async def cmd_presets(message: Message):
    await message.answer('Ok', reply_markup=presets.as_markup())


@dp.message(Command('Photos'))
async def cmd_photos(message: Message):
    await message.answer('Ok', reply_markup=photos.as_markup())


@dp.message(Command('Streams'))
async def cmd_streams(message: Message):
    await message.answer('Ok', reply_markup=streams.as_markup())


@dp.message(Command('Settings'))
async def cmd_settings(message: Message):
    await message.answer('Ok', reply_markup=settings.as_markup())


@dp.message(Command('Private_mode'))
async def cmd_private_mode(message: Message):
    await message.answer('Ok', reply_markup=private.as_markup())


@dp.message(Command('Power'))
async def cmd_power(message: Message):
    await message.answer('Ok', reply_markup=power.as_markup())


@dp.message(Command('Led'))
async def cmd_led(message: Message):
    await message.answer('Ok', reply_markup=led.as_markup())


@dp.message(Command('Rotate'))
async def cmd_rotate(message: Message):
    await message.answer('Ok', reply_markup=rotate.as_markup())


# Обработчик команды /move
@dp.message(Command('move'))
async def move_command(message: Message):
    chat_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    wait = await control_camera(args)
    await asyncio.sleep(wait)
    await bot.send_photo(chat_id, image_low)


@dp.message(Command('private'))
async def command_private(message: Message):
    args = message.text.split(maxsplit=1)
    url = f'http://{cam_host}/cgi-bin/privacy.sh?value={args[1]}'
    requests.post(url)


@dp.message(Command('power'))
async def command_power(message: Message):
    arg = case_yes_no(text=message.text)
    url = f'http://{cam_host}/cgi-bin/camera_settings.sh?switch_on={arg}'
    requests.post(url)


@dp.message(Command('led'))
async def command_led(message: Message):
    arg = case_yes_no(text=message.text)
    url = f'http://{cam_host}/cgi-bin/camera_settings.sh?led={arg}'
    requests.post(url)


@dp.message(Command('rotate'))
async def command_rotate(message: Message):
    arg = case_yes_no(text=message.text)
    url = f'http://{cam_host}/cgi-bin/camera_settings.sh?rotate={arg}'
    requests.post(url)


@dp.message(Command('Get_photo'))
async def photo_command(message: Message):
    chat_id = message.from_user.id
    await bot.send_photo(chat_id, image_high)


@dp.message(Command('Force_get_photo'))
async def low_photo_command(message: Message):
    chat_id = message.from_user.id
    await bot.send_photo(chat_id, image_low)


@dp.message(Command('Full_left'))
async def full_left(message: Message):
    chat_id = message.from_user.id
    url = f'http://{cam_host}/cgi-bin/preset.sh?action=go_preset&num=0'
    requests.post(url)
    await asyncio.sleep(10)
    await bot.send_photo(chat_id, image_low)


@dp.message(Command('Full_right'))
async def full_right(message: Message):
    chat_id = message.from_user.id
    url = f'http://{cam_host}/cgi-bin/preset.sh?action=go_preset&num=1'
    requests.post(url)
    await asyncio.sleep(10)
    await bot.send_photo(chat_id, image_low)


@dp.message(Command('Home'))
async def to_home(message: Message):
    chat_id = message.from_user.id
    url = f'http://{cam_host}/cgi-bin/preset.sh?action=go_preset&num=2'
    requests.post(url)
    await asyncio.sleep(6)
    await bot.send_photo(chat_id, image_high)


@dp.message(Command('stream'))
async def start_live_stream(message: Message):
    global streaming
    if streaming:
        await message.answer("Стрим уже запущен.")
        return

    streaming = True
    await message.answer("Стрим начат.")
    loop = asyncio.get_event_loop()
    recorder_task = loop.create_task(video_recorder(loop))
    sender_task = loop.create_task(video_sender(message.chat.id))
    await asyncio.gather(recorder_task, sender_task)


@dp.message(Command('stop_stream'))
async def stop_stream(message: Message):
    await stop_stream(message)


# Запуск бота
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logger = logging.getLogger(__name__)
    asyncio.run(dp.start_polling(bot))
