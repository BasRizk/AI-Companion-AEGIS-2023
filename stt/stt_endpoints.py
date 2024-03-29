import time
import torch
from loguru import logger
from transformers import pipeline
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from faster_whisper import WhisperModel
from .data_buffer import DataBuffer
from .audio_packet import AudioPacket


class WhisperEndpoint:
    def __init__(self, model="openai/whisper-tiny.en", device=None):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu" or device
        # processor = WhisperProcessor.from_pretrained(model)
        # model = WhisperForConditionalGeneration.from_pretrained(f"openai/whisper-{model}").to(self.device)
        # model.to_bettertransformer()
        # self.model = pipeline(
        #     "automatic-speech-recognition",
        #     model=model,
        #     feature_extractor=processor.feature_extractor,
        #     tokenizer=processor.tokenizer,
        #     # chunk_length_s=30,
        #     device=self.device,
        # )

        model = "guillaumekln/faster-whisper-tiny"
        self.model = WhisperModel(model)

        from queue import Queue

        self.input_queue = Queue()
        # self.output_queue = Queue()

    def buffer_audio_packet(self, audio_packet: AudioPacket):
        self.input_queue.put(audio_packet)

    def create_stream(self):
        self.reset()

    def get_transcription(self):
        print("Waiting for transcription ... ")
        if self.input_queue.qsize() == 0:
            return None

        # unpack as many as possible from queue
        with self.input_queue.mutex:
            audio_packets = list(self.input_queue.queue)
            # clear queue
            self.input_queue.queue.clear()
        # print('Transcribing ... ', f'{len(audio_packets)} packets')
        audio_packet = sum(audio_packets, AudioPacket.get_null_packet())
        print(
            "Transcribing ... ",
            f"{len(audio_packet)} bytes at {audio_packet.sample_rate} Hz",
        )

        # save this data as audio file
        # import scipy.io.wavfile as wav
        # wav.write('debug_audio.wav', audio_packet.sample_rate, audio_packet.float)

        # data = {
        #     'raw': audio_packet.float,
        #     'sampling_rate': audio_packet.sample_rate,
        # }
        # print('Transcribing ... ', f' at {data["sampling_rate"]} Hz')
        data = audio_packet.float

        start = time.time()
        # _out = self.model(data, generate_kwargs={"max_new_tokens": 128})
        segments, _ = self.model.transcribe(
            data,
            vad_filter=True,
        )
        _out = list(segments)
        if len(_out) > 1:
            logger.debug("detected {} segments".format(len(_out)))
        # print(_out)

        _out = " ".join([segment.text for segment in _out])

        logger.success(f"Took {time.time() - start} seconds")
        return _out

    def reset(self):
        self.input_queue.queue.clear()
        # self.output_queue.queue.clear()
