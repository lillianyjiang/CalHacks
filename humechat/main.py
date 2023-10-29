from importlib.metadata import files
import threading
import asyncio
import os
import cv2
import time
import traceback
import websockets
import numpy as np
import base64
import json

from pynput import keyboard
from pvrecorder import PvRecorder
from whispercpp import Whisper
from chat import message, store_emotions
from playsound import playsound
from hume import HumeStreamClient, HumeClientException, HumeBatchClient
from hume.models.config import FaceConfig, BurstConfig
from gtts import gTTS

# Configurations
HUME_API_KEY = "VbiYShiDrtyMySWqUodZMSaOZdyf7Tm0vdKIHBvBmaO6IaV9" # paste your API Key here
HUME_FACE_FPS = 1 / 3  # 3 FPS

TEMP_FILE = 'temp.jpg'
TEMP_WAV_FILE = 'temp.wav'

# Initialize whisper model, pyttsx3 engine, and pv recorder
w = Whisper.from_pretrained("tiny.en")
recorder = PvRecorder(device_index=-1, frame_length=512)

# Global variables
recording = False
recording_data = []

# Webcam setup
cam = cv2.VideoCapture(0)
batch_client = HumeBatchClient(HUME_API_KEY)
client = HumeStreamClient(HUME_API_KEY)
configs = [FaceConfig(identify_faces=True)]
#change out this webcam loop to do it and remove the press space to record voice part
async def webcam_loop():
    while True:
        try:
            async with client.connect(configs) as socket: 
                print("(Connected to Hume API!)")
                while True:
                    if not recording:
                        _, frame = cam.read()
                        cv2.imwrite(TEMP_FILE, frame)
                        result = await socket.send_file(TEMP_FILE)
                        store_emotions(result)
                        await asyncio.sleep(1 / 3)
            # configs2 = BurstConfig()
            # async with client.connect(configs2) as socket:
            #     print("(Connected to Hume API!)")
            #     result = await socket.send_file("<your-audio-filepath>")
            #     print(result)
                        

        except websockets.exceptions.ConnectionClosedError:
            print("Connection lost. Attempting to reconnect in 1 seconds.")
            time.sleep(1)
        except HumeClientException:
            print(traceback.format_exc())
            break
        except Exception:
            print(traceback.format_exc())
        


def start_asyncio_event_loop(loop, asyncio_function):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio_function)


def recording_loop():
    global recording_data, recording
    while recording:
        frame = recorder.read()
        recording_data.append(frame)
    recorder.stop()
    print("(Recording stopped...)")

    json_str = json.dumps(recording_data) #tried to convert to a string 
    #print("type: ", type(json_str))

    # Now you can send this string
    #result = batch_client.submit_job([], [BurstConfig()], files=json_str)
    result = batch_client.submit_job([json_str], [BurstConfig()])

    #recording_data = np.hstack(recording_data).astype(np.int16).flatten().astype(np.float32) / 32768.0 # this may be wrong
    #result = batch_client.submit_job([], configs, files=recording_data)
    result.await_complete()
    result.download_predictions("predictions.json")
    print("Predictions downloaded to predictions.json")
    # func(result) about burst data 

    # below code does text to speech 
    # recording_data = np.hstack(recording_data).astype(np.int16).flatten().astype(np.float32) / 32768.0
    # transcription = w.transcribe(recording_data)
    # response = message(transcription)
    
    # tts = gTTS(text=response, lang='en')
    # tts.save(TEMP_WAV_FILE) # adding audio and video separately. recorder records audio. send wave file through the API and specify the two configs through the web socket 
    # playsound(TEMP_WAV_FILE)
    # os.remove(TEMP_WAV_FILE)


def on_press(key):
    global recording, recording_data, recorder
    if key == keyboard.Key.space:
        if recording:
            recording = False
        else:
            recording = True
            recording_data = []
            recorder.start()
            print("(Recording started...)")
            threading.Thread(target=recording_loop).start()


new_loop = asyncio.new_event_loop()

threading.Thread(target=start_asyncio_event_loop, args=(new_loop, webcam_loop())).start()

with keyboard.Listener(on_press=on_press) as listener:
    print("Speak to Joaquin!")
    print("(Press spacebar to speak. To finish speaking, press spacebar again)")
    listener.join()
