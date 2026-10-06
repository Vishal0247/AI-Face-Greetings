import os
import platform

# Only import ctypes on Windows where we use winmm for audio playback
IS_WINDOWS = platform.system() == 'Windows'
if IS_WINDOWS:
    import ctypes

class AudioManager:
    def __init__(self, audio_dir="data/audio"):
        self.audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", audio_dir)
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            
        # Session state
        self.currently_greeted_person = None
        self.current_playing_file = None
        
    def reset_session(self):
        """
        Called when the user leaves the camera view.
        Allows them to be greeted again if they return later.
        """
        if self.currently_greeted_person is not None:
            print(f"[AUDIO] Session ended for {self.currently_greeted_person}. System ready for next greeting.")
            self.currently_greeted_person = None
            
    def stop_greeting(self):
        """
        Stops the audio immediately if it's currently playing.
        We call this when the user leaves the camera view.
        """
        if self.current_playing_file is not None:
            print("[AUDIO] Stopping greeting because person left.")
            
            if IS_WINDOWS:
                # Send stop command to Windows Media API
                ctypes.windll.winmm.mciSendStringW(f'stop "{self.current_playing_file}"', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'close "{self.current_playing_file}"', None, 0, None)
            self.current_playing_file = None
        
    def play_greeting(self, person_name):
        """
        Plays the personalized greeting if they haven't been greeted yet this session.
        """
        # 1. If we already greeted them this session, do nothing!
        if self.currently_greeted_person == person_name:
            return False
            
        # 2. Look for their personalized audio file
        valid_extensions = [".mp3", ".m4a", ".wav", ".ogg", ".webm", ".aac", ".flac"]
        audio_file = None
        
        for ext in valid_extensions:
            potential_file = os.path.join(self.audio_dir, f"{person_name}{ext}")
            if os.path.exists(potential_file):
                audio_file = potential_file
                break
        
        if audio_file is None:
            print(f"[AUDIO] No audio file found for {person_name}. Generating one using AI...")
            try:
                from gtts import gTTS
                audio_file = os.path.join(self.audio_dir, f"{person_name}.mp3")
                tts = gTTS(text=f"Welcome back, {person_name}! Great to see you today.", lang='en', slow=False)
                tts.save(audio_file)
            except Exception as e:
                print(f"[AUDIO] Error generating TTS audio: {e}")
                self.currently_greeted_person = person_name
                return False
            
        # 3. Play the audio (only on Windows; on other platforms the web frontend handles playback)
        try:
            print(f"\n==========================================")
            print(f"[AUDIO] Playing personalized greeting for {person_name}!")
            print(f"==========================================\n")
            
            self.currently_greeted_person = person_name
            self.current_playing_file = audio_file
            
            if IS_WINDOWS:
                # Stop any currently playing audio on this file just in case
                ctypes.windll.winmm.mciSendStringW(f'close "{audio_file}"', None, 0, None)
                
                # Play the file using the robust Windows API
                error_code = ctypes.windll.winmm.mciSendStringW(f'play "{audio_file}"', None, 0, None)
                
                if error_code != 0:
                    print(f"[AUDIO] Windows API failed to play file. It might not support this specific format.")
            else:
                print("[AUDIO] Non-Windows platform: audio will be played by the web frontend.")
                
            return True
        except Exception as e:
            print(f"[AUDIO] Error playing audio: {e}")
            return False
