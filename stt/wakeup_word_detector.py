import pvporcupine
import sys
import struct
from threading import Thread
from .data_buffer import DataBuffer
from .audio_packet import AudioPacket

class WakeUpVoiceDetector(Thread):
    """Wake Up Word Detector using Porcupine"""
    
    def __init__(
            self,
            access_key = 
                [
                    "Sf/52ItzMqpOpPQbsiN8g4WNOu+7VclIJZlwMZyI5+1KNlDZjZBrGA==",
                    "GJxnDyQx7BWTkVdrE4sW/raxWZGmpxXmLN71urcgCugdSURn5enYBA==",
                    "126kyqRJC8iIG41p8NZqo6DNb3wKrAN1Ilv+PQ/xdMxn8Q8MfTvCsQ=="
                ],
            keyword_paths = [
                [
                    "models/pvprocupine/%s/Hello-Eva_en_windows_v2_2_0/hello-Eva_en_windows_v2_2_0.ppn",
                    "models/pvprocupine/%s/Traveller_en_windows_v2_2_0/Traveller_en_windows_v2_2_0.ppn",
                    "models/pvprocupine/%s/habibi_en_windows_v2_2_0/habibi_en_windows_v2_2_0.ppn"
                ]
            ],
            sensitivities=None):
        """Initialize WakeUpVoiceDetector
        
        Args:
            access_key (List[str], optional): Accesses keys for Porcupine.
            keyword_paths (List[List[str]], optional): Pathes to keywords files. 
            sensitivities (List[float], optional): Sensitivities for keywords. Defaults to None (equal senstivities).
        """
        super(WakeUpVoiceDetector, self).__init__()

        try:
            if sys.platform.startswith('linux'):
                keyword_paths = keyword_paths[1]
            elif sys.platform.startswith('win'):
                keyword_paths = keyword_paths[0]
                print(f'Keywords set {keyword_paths}')
            else:
                raise NotImplementedError()
        except:
            raise Exception("Unsupported Platform")    

        alternate_i = 0
        initialized = False
        while not initialized:
            self._access_key = access_key[alternate_i]
            self._keyword_paths = [k % alternate_i for k in keyword_paths]
            print(f'Trying keywords_paths {keyword_paths}')
            self._sensitivities = sensitivities
            try:            
                self.porcupine_handle = pvporcupine.create(
                        access_key=self._access_key,
                        keyword_paths=self._keyword_paths,
                        sensitivities=self._sensitivities)
                initialized = True
            except:
                print('Reswitching Access Key')
                alternate_i += 1 
                
        self.frame_size = 1024
        self.buffer = DataBuffer(self.frame_size)
    
    def reset_data_buffer(self):
        """Reset data buffer"""
        self.buffer.reset()

    def feed_audio(self, audio_packet: AudioPacket):
        """Feed audio packet to buffer
        
        Args:
            audio_packet (AudioPacket): Audio packet to feed procupine hot-word detector
        """
        self.buffer.add(audio_packet)
        
    def process_audio_stream(self) -> bool: 
        """Process audio stream and return True if wake word is detected
        
        Returns:
            bool: True if wake word is detected    
        """
        # Utilize full audio_packet instead
        for frame in self.buffer:
            # Process only proper frame sizes
            if len(frame) < self.frame_size:
                break
            # print("\nProcessing", flush=True)
            pcm = struct.unpack_from("h" *self.porcupine_handle.frame_length, frame.bytes)
            result = self.porcupine_handle.process(pcm)
            if result >= 0:
                self.reset_data_buffer()
                return True