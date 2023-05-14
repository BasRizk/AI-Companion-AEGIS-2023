import collections

def vad_collector(sample_rate, frame_duration_ms,
                 padding_duration_ms, vad, frames):
   """Filters out non-voiced audio frames.
 
   Given a webrtcvad.Vad and a source of audio frames, yields only
   the voiced audio.
 
   Uses a padded, sliding window algorithm over the audio frames.
   When more than 90% of the frames in the window are voiced (as
   reported by the VAD), the collector triggers and begins yielding
   audio frames. Then the collector waits until 90% of the frames in
   the window are unvoiced to detrigger.
 
   The window is padded at the front and back to provide a small
   amount of silence or the beginnings/endings of speech around the
   voiced frames.
 
   Arguments:
 
   sample_rate - The audio sample rate, in Hz.
   frame_duration_ms - The frame duration in milliseconds.
   padding_duration_ms - The amount to pad the window, in milliseconds.
   vad - An instance of webrtcvad.Vad.
   frames - a source of audio frames (sequence or generator).
 
   Returns: A generator that yields PCM audio data.
   """
   num_padding_frames = int(padding_duration_ms / frame_duration_ms)
   # We use a deque for our sliding window/ring buffer.
   ring_buffer = collections.deque(maxlen=num_padding_frames)
   # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
   # NOTTRIGGERED state.
   triggered = False
 
   voiced_frames = []
   for frame in frames:
       is_speech = vad.is_speech(frame.bytes, sample_rate)
 
       if not triggered:
           ring_buffer.append((frame, is_speech))
           num_voiced = len([f for f, speech in ring_buffer if speech])
           # If we're NOTTRIGGERED and more than 90% of the frames in
           # the ring buffer are voiced frames, then enter the
           # TRIGGERED state.
           if num_voiced > 0.9 * ring_buffer.maxlen:
               triggered = True
               # We want to yield all the audio we see from now until
               # we are NOTTRIGGERED, but we have to start with the
               # audio that's already in the ring buffer.
               for f, s in ring_buffer:
                   voiced_frames.append(f)
               ring_buffer.clear()
       else:
           # We're in the TRIGGERED state, so collect the audio data
           # and add it to the ring buffer.
           voiced_frames.append(frame)
           ring_buffer.append((frame, is_speech))
           num_unvoiced = len([f for f, speech in ring_buffer if not speech])
           # If more than 90% of the frames in the ring buffer are
           # unvoiced, then enter NOTTRIGGERED and yield whatever
           # audio we've collected.
           if num_unvoiced > 0.9 * ring_buffer.maxlen:
               triggered = False
               yield b''.join([f.bytes for f in voiced_frames])
               ring_buffer.clear()
               voiced_frames = []
   # if triggered:
   #     pass
   # If we have any leftover voiced audio when we run out of input,
   # yield it.
   if voiced_frames:
       yield b''.join([f.bytes for f in voiced_frames])