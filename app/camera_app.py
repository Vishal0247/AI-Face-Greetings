import cv2
import os
from detection.face_detector import FaceDetector
from detection.face_quality import FaceQualityChecker
from recognition.enrollment import EnrollmentManager
from recognition.lbph_recognizer import LBPHFaceRecognizer
from recognition.verification import VerificationManager
from audio.audio_manager import AudioManager
from detection.liveness import BlinkDetector

class CameraApp:
    def __init__(self):
        # Initialize all modules
        self.detector = FaceDetector()
        self.quality_checker = None # Will initialize on first frame
        self.enroll_manager = EnrollmentManager()
        self.verifier = VerificationManager()
        self.recognizer = LBPHFaceRecognizer()
        self.audio_manager = AudioManager()
        self.liveness = BlinkDetector()
        self.liveness_passed = False
        
        # Train model immediately on startup
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "people")
        self.recognizer.train(data_dir)
        
        # State variables to share with the web frontend
        self.status_text = "Initializing..."
        self.is_valid = False
        self.extra_status = ""
        self.verified_name = None
        
        # Video Logger State
        self.video_buffer = []
        self.is_recording = False
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.is_recording = False
        self.video_buffer = []
        self.session_name = "Unknown"

    def draw_guide_and_status(self, frame):
        center_x = self.width // 2
        center_y = self.height // 2
        radius = 120
        
        if self.verified_name is not None:
            color = (255, 255, 0) # Cyan
        else:
            color = (0, 255, 0) if self.is_valid else (0, 0, 255)
        
        cv2.circle(frame, (center_x, center_y), radius, color, 2)
        
        # Note: We still draw the guide on the video feed, but we omit the text 
        # because the HTML frontend will display the text much prettier!

    def process_frame(self, frame):
        """Processes a single frame array from the client, updates state, and returns the audio to play if any."""
        # Normalize to standard width of 640 so our quality thresholds (120, 300, 80px) work consistently across all devices
        height, width = frame.shape[:2]
        if width != 640:
            scale = 640.0 / width
            frame = cv2.resize(frame, (640, int(height * scale)))
            
        height, width, _ = frame.shape
        
        # Initialize or re-initialize if the aspect ratio/device changed (e.g., from laptop landscape to phone portrait)
        if self.quality_checker is None or self.quality_checker.frame_width != width or self.quality_checker.frame_height != height:
            self.quality_checker = FaceQualityChecker(width, height)
            
        frame = cv2.flip(frame, 1)
        faces = self.detector.detect_faces(frame)
        
        # --- SESSION RESET & LOGGING LOGIC ---
        if len(faces) == 0:
            self.audio_manager.reset_session()
            self.audio_manager.stop_greeting()
            
            # Stop recording and save if we have enough frames
            if self.is_recording:
                print(f"[DEBUG] Face left. is_recording={self.is_recording}, buffer_len={len(self.video_buffer)}")
                if len(self.video_buffer) > 5:
                    import threading
                    import datetime
                    import imageio
                    
                    def save_video(frames, name_guess):
                        try:
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            filename = f"{timestamp}_{name_guess}.gif"
                            filepath = os.path.join(self.log_dir, filename)
                            print(f"[DEBUG] Saving video to {filepath}")
                            
                            # Convert BGR to RGB for imageio
                            rgb_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames]
                            imageio.mimsave(filepath, rgb_frames, fps=7)
                            print(f"[LOGGER] Saved recent scan to {filename}")
                        except Exception as e:
                            import traceback
                            print(f"[LOGGER] Error saving video: {e}")
                            traceback.print_exc()
                            
                    # Save asynchronously so we don't freeze the camera
                    threading.Thread(target=save_video, args=(self.video_buffer.copy(), self.session_name)).start()
                
            self.video_buffer = []
            self.is_recording = False
            self.session_name = "Unknown"
            
        else:
            # Face detected, start/continue recording
            self.is_recording = True
            if len(self.video_buffer) < 35: # Max 5 seconds
                self.video_buffer.append(frame.copy())
            elif len(self.video_buffer) == 35:
                # Force save if they stand there too long, to ensure we get it
                pass # Or just stop appending
            
        self.status_text, self.is_valid = self.quality_checker.check_quality(faces)
        
        self.extra_status = ""
        self.verified_name = None
        
        if self.enroll_manager.is_enrolling:
            self.extra_status = self.enroll_manager.process_frame(frame, faces, self.is_valid)
            
            # If enrollment just finished, retrain the model with new data!
            if not self.enroll_manager.is_enrolling and self.extra_status.startswith("Enrollment complete"):
                data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "people")
                self.recognizer.train(data_dir)
                print(f"[INFO] Model retrained after enrollment!")
            
        else:
            if not self.is_valid:
                self.liveness.reset()
                self.liveness_passed = False
                self.verified_name = self.verifier.handle_invalid_frame()
                if self.verified_name is None:
                    self.audio_manager.stop_greeting()
                    self.audio_manager.reset_session()
                    
            elif self.recognizer.is_trained:
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                
                if not self.liveness_passed:
                    num_eyes = self.detector.detect_eyes(frame, faces[0])
                    if self.liveness.check_liveness(num_eyes):
                        self.liveness_passed = True
                        
                if not self.liveness_passed:
                    self.extra_status = "Blink to verify..."
                    self.verified_name = None
                else:
                    raw_name, distance = self.recognizer.predict(face_roi)
                    self.extra_status, self.verified_name = self.verifier.process_prediction(raw_name, distance)
                    if self.verified_name:
                        self.session_name = self.verified_name
                
                # RETURN AUDIO INSTRUCTION INSTEAD OF PLAYING ON SERVER
                if self.verified_name is not None:
                    # We will return the verified_name so the frontend can play it
                    pass

        # We no longer draw UI on the server-side frame, the frontend will handle UI.
        
        return self.verified_name

    def enroll_from_image(self, name, frame):
        """Enroll a person from a static image frame."""
        # Scale down huge uploaded photos so the face detector can reliably find faces
        height, width = frame.shape[:2]
        if width > 800:
            scale = 800.0 / width
            frame = cv2.resize(frame, (800, int(height * scale)))
            
        faces = self.detector.detect_faces(frame)
        
        if len(faces) == 0:
            return False, "No face detected in the uploaded image. Try another photo."
        if len(faces) > 1:
            return False, "Multiple faces detected. Please upload an image with only one person."
            
        x, y, w, h = faces[0]
        face_roi = frame[y:y+h, x:x+w]
        
        # Save the face
        self.enroll_manager.save_face_from_image(name, face_roi)
        
        # Retrain the model
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "people")
        self.recognizer.train(data_dir)
        
        return True, f"Successfully enrolled {name}!"

    def get_state(self):
        """Returns the current state for the web frontend JSON API."""
        return {
            "status_text": self.status_text,
            "is_valid": self.is_valid,
            "extra_status": self.extra_status,
            "verified_name": self.verified_name,
            "is_enrolling": self.enroll_manager.is_enrolling,
            "enroll_name": self.enroll_manager.person_name if self.enroll_manager.is_enrolling else None
        }

    def release(self):
        pass
