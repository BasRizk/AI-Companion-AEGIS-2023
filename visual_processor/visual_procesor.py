import base64
from storage_manager import StorageManager
from .data_buffer import DataBuffer
from .video_frame import VideoFrame

class VisualProcessor:
    def __init__(self):
        # TODO
        self.queue = []
    
    def feed(self, data):
        if len(self.queue) > 30:
            self._save_imgs_on_queue()
            breakpoint()
        img_data = base64.b64decode(data['frame'])
        self.queue.append(img_data)
        
    def _save_imgs_on_queue(self):
        for i, img_data in enumerate(self.queue):
            with open(f'img_{i}.jpeg', 'wb') as f:
                f.write(img_data)