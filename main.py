from flask import Flask
from flask_socketio import SocketIO
from WakeUpVoiceDetector import WakeUpVoiceDetector
from STTController import STTController
from BotController import BotController
from TTSController import TTSController
import numpy as np
import sounddevice as sd
import time


import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
# os.environ['TF_FOCE_GPU_ALLOW_GROWTH'] = "true"
import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


SAMPLE_RATE = 16000
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app,
    cors_allowed_origins='*',
    cors_credentials=True)
    
@socketio.on('connect')
def handle_connect():
    global session_audio_buffer
    global command_audio_buffer
    global wakeUpWordDetected
    global leftOver
    session_audio_buffer = b""
    command_audio_buffer = b""
    wakeUpWordDetected = False
    leftOver = b""
    stt.create_stream()
    write_output('client connected')

@socketio.on('disconnect')
def handle_disconnect():
    global is_sample_tagging
    is_sample_tagging = False
    sd.play(np.frombuffer(session_audio_buffer, dtype=np.int16), 16000)
    
    session_id = str(int(time.time()*1000))
    with open(f"sample-audio-binary/{session_id}_binary.txt", mode='wb') as f:
        f.write(session_audio_buffer)

    write_output('debug, testing the whole audio of the session')
    stt.reset_audio_stream()
    stt.create_stream()
    result = stt.process_audio_stream(session_audio_buffer)
    write_output(result)

    write_output('client disconnected')
 
def setup_sample_tagging():
    write_output('set in sample tagging')
    global is_sample_tagging
    is_sample_tagging = True
    stt.set_sample_tagging_focus()

def kill_sample_tagging():
    write_output('kill sample tagging')
    global is_sample_tagging
    is_sample_tagging = False
    stt.set_regular_focus()
     # TODO consider also case of termination using exit word

@socketio.on('stream-wakeup')
def handle_stream_audio(data):
    wakeUpWordDetected = wakeUpWordDetector.process_audio_stream(data)
    if wakeUpWordDetected:
        write_output("detected wakeup word")
        socketio.emit('wake-up')    

@socketio.on('stream-audio')
def handle_stream_audio(data):
    global stt_res_buffer
    stt_res_buffer = None
    global command_audio_buffer
    global session_audio_buffer
    if len(command_audio_buffer) == 0:
        write_output("recieving first stream of audio command")
    command_audio_buffer += data
    session_audio_buffer += data

    stt_res = stt.process_audio_stream(data)
    if stt_res:
        socketio.emit('stt-response', stt_res)
        write_output('User: ' + str(stt_res))

        with open(f"sample-audio-binary/{stt_res['text'].replace(' ', '_')}_binary.txt", mode='wb') as f:
            f.write(command_audio_buffer)
        command_audio_buffer = b""
        
        global is_sample_tagging
        if is_sample_tagging:
            write_output("is sample taggin on..")
            # TERMINATION SCHEME BY <OVER> IN SAMPLE-TAGGING
            if stt_res_buffer is not None:
                write_output("appending to buffer - sample tagging")
                stt_res_buffer = stt._combine_outcomes([stt_res_buffer, stt_res])
            stt_res_buffer = stt_res
            if not ("over" in stt_res['text'].rstrip()[-30:]):
                return
            stt_res = stt_res_buffer
            stt_res_buffer = None
            

        bot_res = bot.send_user_message(stt_res['text'])
        print('SENVA: ' + str(bot_res))    
        bot_text = bot_res.get('text')
        if bot_text:
            bot_text = ' '.join(bot_text)
            voice_bytes = tts.get_audio_bytes_stream(bot_text)
            write_output('emmiting voice')
            socketio.emit('bot-voice', voice_bytes)
        else:
            print('no text')

        bot_commands = bot_res.get('commands')
        if bot_commands:
            sample_command = bot_commands[0].get('sample')
            sample_details_command =  bot_commands[0].get('Sample Details')
            if sample_command is not None:
                write_output("tagging a sample scenario")
                setup_sample_tagging()
            elif sample_details_command is not None:
                write_output("sample tagging finished successfully")
                kill_sample_tagging()
            elif sample_command is not None and sample_command is False:
                write_output("sample tagging exited")
                kill_sample_tagging()
            write_output('emitting commands ' +  str(bot_res.get('commands')))
        else:
            print('no commands')
        socketio.emit('bot-response', bot_res)

@socketio.on('reset-audio-stream')
def handle_reset_audio_stream():
    stt.reset_audio_stream()

@socketio.on('trial')
def handle_trial(data):
    write_output('received trial')
    write_output(data)

def write_output(msg, end='\n'):
    print(str(msg), end=end, flush=True)


if __name__ == '__main__':
    print("Initializing WakeUpWordDetector")
    wakeUpWordDetector = WakeUpVoiceDetector()

    print("Initializing STT Controller")
    stt = STTController(
                    sample_rate=SAMPLE_RATE,
                    model_path='models/ds-model/deepspeech-0.9.3-models',
                    load_scorer=True,
                    silence_threshold=250,
                    vad_aggressiveness=3,
                    frame_size = 320
                )
    stt.set_regular_focus()

    is_sample_tagging = False
    print("Initializing Bot Controller")
    bot = BotController()
    print("Initializing TTS Controller")
    tts = TTSController()    
    print("Server is about to be Up and Running..")

    socketio.run(app, host='0.0.0.0', port=4000)    