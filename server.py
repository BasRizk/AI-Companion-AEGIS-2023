#!/usr/bin/env python -W ignore::DeprecationWarning
import logging
logging.basicConfig(level=logging.DEBUG)
import os, argparse
from flask import Flask
from flask_socketio import SocketIO, Namespace, emit
from assistant_controller import AssistantController
from storage_manager import StorageManager, write_output
from multiprocessing import Lock
from memory import WorldState

# import tensorflow as tf

# @socketio.on_error_default  # handles all namespaces without an explicit error handler
# def default_error_handler(e):
#     write_output(f'Error debug {e}')
#     # stt.reset_audio_stream()
#     # # TODO reset anything   
    
socketio: SocketIO = None  
class DigitalAssistant(Namespace):
    """Digital Assistant SocketIO Namespace"""
    
    def __init__(self, namespace='/', assistant_name='SENVA', shutdown_bot=False, verbose=False):
        super().__init__(namespace)
        self.namespace = namespace
        self.assistant_controller = AssistantController(
            name=assistant_name, shutdown_bot=shutdown_bot, verbose=verbose
        )
        self.lock = Lock()        
        self.responding_task = socketio.start_background_task(self.bg_responding_task)
        self.verbose = verbose # TODO use it
        logging.info("Server is about to be Up and Running..")
        
    def on_connect(self):
        logging.info('client connected')
        StorageManager.establish_session()
        bot_voice_bytes = self.assistant_controller.startup()
        if bot_voice_bytes:
            logging.info('emmiting bot_voice')
            socketio.emit('bot_voice', bot_voice_bytes)
            
    def on_disconnect(self):
        logging.info('client disconnected\n')
        with self.lock:
            self.assistant_controller.clean_up()  
        StorageManager.clean_up()  
    
    def on_read_tts(self, data):
        write_output(f'request to read data {data}')
        audio_bytes = self.assistant_controller.read_text(data)
        emit("bot_voice", audio_bytes)
    
    def on_stream_audio(self, audio_data):
        with self.lock:
            # Feeding in audio stream
            self.assistant_controller.feed_audio_stream(audio_data) 
        
    def on_trial(self, data):
        write_output(f'received trial: {data}')
    
    def on_stream_text(self, command):
        if not isinstance(command, str):
            raise Exception("Datatype is not supported")
        # breakpoint()
        command = {"text": command}
        logging.info(f'User: {command}')
        self.bot_respond(command)
        
    def on_update_world_state(self, state):
        WorldState.update(state)

    def bg_responding_task(self):
        # READ BUFFER AND EMIT AS NEEDED
        # counter = 0
        while True:
            socketio.sleep(0.01)
            # counter += 1
            with self.lock:
                if self.assistant_controller.is_awake():
                    # write_output(f'is awake {counter}: {self.assistant_controller.is_awake()}', end='\r')
                    self.apply_communication_logic()
                    # TODO introduce timeout
                else:
                    # start = time.time()
                    wakeUpWordDetected =\
                        self.assistant_controller.is_wake_word_detected()
                    # write_output(f'took {time.time() - start}', end='\r')
                    if wakeUpWordDetected:
                        logging.info("detected wakeup word")
                        socketio.emit('wake_up')    
                        # Now assisant is awake
                    
                    is_procedural = self.assistant_controller.process_if_procedural_step()
                    # Include timestamps
                    if is_procedural:
                        bot_res, bot_voice_bytes = is_procedural
                        # Include timestamps
                        if bot_voice_bytes:
                            logging.info('emmiting bot_voice')
                            socketio.emit('bot_voice', bot_voice_bytes)
                        
                        if bot_res: # None only if bot is shutdown
                            logging.info("emitting bot_response")
                            socketio.emit('bot_response', bot_res)
                        else:
                            logging.warn('bot is shutdown')
                            socketio.emit('bot_repsonse', {
                                'msg': 'bot is shutdown' 
                            })

    def apply_communication_logic(self):  
        stt_res = self.assistant_controller.process_audio_buffer()
        if stt_res is None:
            return
        
        # Now assisant is not awake
        logging.info(f'User: {stt_res}')
        socketio.emit('stt_response', stt_res)
    
        # TODO check logic of is_awake
        # is_procedural_step = self.assistant_controller.process_if_procedural_step()
        # if is_procedural_step:
        #     return
        
        self.bot_respond(stt_res)
    
    def bot_respond(self, stt_res):
        bot_res, bot_voice_bytes =\
            self.assistant_controller.respond(stt_res['text'])

        # TODO Include timestamps
        if bot_voice_bytes:
            logging.info('emmiting bot_voice')
            socketio.emit('bot_voice', bot_voice_bytes)
        
        if bot_res: # None only if bot is shutdown
            logging.info("emitting bot_response")
            socketio.emit('bot_response', bot_res)
        else:
            logging.warn('bot is shutdown')
            socketio.emit('bot_repsonse', {
                'msg': 'bot is shutdown' 
            })


if __name__ == "__main__":    
    # TODO use a yml config file with internal configurations
    parser = argparse.ArgumentParser(description='Digital Assistant Endpoint')
    parser.add_argument('--cpu', dest='cpu', type=bool, default=False, help='Use CPU instead of GPU')
    parser.add_argument('--port', dest='port', type=int, default=4000, help='Port number')
    parser.add_argument('--name', dest='name', type=str, default='Traveller',
                        help='Digital Assistant Name')
    parser.add_argument('--shutdown_bot', dest='shutdown_bot', type=bool, default=False,
                        help='Shutdown bot')
    parser.add_argument('--debug', dest='debug', type=bool, default=False, help='Debug mode')
    parser.add_argument('--verbose', dest='verbose', type=bool, default=False, help='Verbose mode')
    parser.add_argument('--log', dest='log', type=bool, default=False, help='Log mode')
    parser.add_argument('--flask_secret_key', dest='flask_secret_key', 
                        type=str, default='secret!', help='Flask secret key')
    args = parser.parse_args()



    if args.cpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    else:
        # print(tf.config.list_physical_devices('GPU'))
        # tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
        pass
        
    app = Flask(__name__)
    app.config['SECRET_KEY'] = args.flask_secret_key
    socketio = SocketIO(
        app,
        cors_allowed_origins='*', cors_credentials=True,
        logger=args.log, engineio_logger=args.log
    )

    digital_assistant_name = args.name
    digital_assistant = DigitalAssistant(
        namespace='/', 
        assistant_name=digital_assistant_name,
        shutdown_bot=args.shutdown_bot,
        verbose=args.verbose
    )
    socketio.on_namespace(digital_assistant)    
    
    # Show all loggings levels in console
    logging.basicConfig(level=logging.DEBUG)
    
    # host_ip_address = socket.gethostbyname(socket.gethostname())
    logging.info(f'\nYour Digital Assistant {digital_assistant_name} running on port {args.port}')
    logging.info('Hints:')
    logging.info('1. Run "ipconfig" in your terminal and use Wireless LAN adapter Wi-Fi IPv4 Address')
    logging.info('2. Ensure your client is connected to the same WIFI connection')
    logging.info('3. Ensure firewall shields are down in this particular network type with python')
    logging.info('4. Ensure your client microphone is not used by any other services such as windows speech-to-text api')
    logging.info('Fight On!')
    
    socketio.run(
        app, host='0.0.0.0',
        port=args.port, 
        use_reloader=False
    )  