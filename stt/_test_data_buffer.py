# go to parent directory
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from time import sleep
from data_buffer import DataBuffer
from audio_packet import AudioPacket


print("Testing DataBuffer ...")
import random

buff = DataBuffer(frame_size=320, max_queue_size=100)

packets = []
for i in range(3):
    audio_packet = AudioPacket(
        {
            "sampleRate": 16000,
            "numChannels": 1,
            "timestamp": time.time(),
            "bytes": b"0" * 320,
        },
        is_processed=True,
    )
    sleep(random.randint(0, 3) * 0.3)
    packets.append(audio_packet)

# shuffle packets
random.shuffle(packets)

for packet in packets:
    buff.put(packet)

for packet in reversed(packets):
    buff.put(packet)

# print all timestamps
for packet in buff.queue.queue:
    print(packet.timestamp)

print([x.timestamp for x in buff.queue.queue])
print(f"There are {len(buff.queue.queue)} packets in the queue")


# sum up all packets
sum_packet = sum(buff, AudioPacket.get_null_packet())
print("Testing DataBuffer Done!")
