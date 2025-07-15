from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor
from os import remove
from time import time

import cv2
from aiogram.types import FSInputFile

from config import cam_host, bot

rtsp_url = f'rtsp://{cam_host}/ch0_1.h264'
record_duration = 30  # Длительность фрагмента
streaming = False

output_file = "video.mp4"
executor = ThreadPoolExecutor(max_workers=1)


def recording():
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return None

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0  # fallback если fps не определился
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    start_time = time()

    while (time() - start_time) < record_duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    out.release()
    cap.release()
    return True


async def record(chat_id):
    loop = get_event_loop()
    while streaming:
        success = await loop.run_in_executor(executor, recording)
        if success:
            if streaming:
                video = FSInputFile(output_file)
                await bot.send_video(chat_id, video)
                remove(output_file)
            else:
                remove(output_file)


async def start_streaming(chat_id):
    global streaming
    streaming = True
    await record(chat_id)


async def stop_streaming():
    global streaming
    streaming = False
