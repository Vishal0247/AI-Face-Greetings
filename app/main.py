import cv2
import os
from detection.face_detector import FaceDetector
from detection.face_quality import FaceQualityChecker
from recognition.enrollment import EnrollmentManager
from recognition.lbph_recognizer import LBPHFaceRecognizer
from recognition.verification import VerificationManager
from audio.audio_manager import AudioManager

def draw_guide_and_status(frame, status_text, is_valid, extra_status="", verified_name=None):
    height, width, _ = frame.shape
    center_x = width // 2
    center_y = height // 2
    radius = 120
    
    if verified_name is not None:
        color = (255, 255, 0) # Cyan
    else:
        color = (0, 255, 0) if is_valid else (0, 0, 255)
    
    cv2.circle(frame, (center_x, center_y), radius, color, 2)
    
    (text_width, _), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    text_x = center_x - (text_width // 2)
    text_y = center_y - radius - 20
    cv2.putText(frame, status_text, (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
    if extra_status:
        cv2.putText(frame, extra_status, (50, height - 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

def main():
    print("========================================")
    print("      AI FACE GREETING SYSTEM")
    print("========================================")
    
    enroll_name = input("Enter a name to ENROLL (or press Enter to RECOGNIZE): ").strip()

    print("Initializing camera...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    ret, initial_frame = cap.read()
    if not ret:
        print("Error reading frame.")
        return
    height, width, _ = initial_frame.shape

    # Initialize all modules
    detector = FaceDetector()
    quality_checker = FaceQualityChecker(width, height)
    enroll_manager = EnrollmentManager()
    verifier = VerificationManager()
    recognizer = LBPHFaceRecognizer()
    audio_manager = AudioManager()
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "people")
    
    if enroll_name == "":
        recognizer.train(data_dir)
    else:
        enroll_manager.start_enrollment(enroll_name)
        print(f"Starting enrollment for {enroll_name}...")

    print("Camera opened successfully. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        faces = detector.detect_faces(frame)
        
        # --- SESSION RESET LOGIC ---
        if len(faces) == 0:
            audio_manager.reset_session()
            audio_manager.stop_greeting()
            
        status_text, is_valid = quality_checker.check_quality(faces)
        
        extra_status = ""
        verified_name = None
        
        if enroll_manager.is_enrolling:
            extra_status = enroll_manager.process_frame(frame, faces, is_valid)
            
        else:
            if not is_valid:
                # Ask the verifier to handle the invalid frame (this applies the grace period)
                verified_name = verifier.handle_invalid_frame()
                
                # If the grace period expired, the verifier returns None.
                if verified_name is None:
                    audio_manager.stop_greeting()
                    audio_manager.reset_session()
                    
            elif recognizer.is_trained:
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                
                raw_name, distance = recognizer.predict(face_roi)
                extra_status, verified_name = verifier.process_prediction(raw_name, distance)
                
                # --- PLAY AUDIO GREETING ---
                if verified_name is not None:
                    audio_manager.play_greeting(verified_name)

        draw_guide_and_status(frame, status_text, is_valid, extra_status, verified_name)

        if verified_name is not None:
            box_color = (255, 255, 0)
        else:
            box_color = (0, 255, 0) if is_valid else (0, 0, 255)
            
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), box_color, 2)

        cv2.imshow('AI Face Greeting - Live Camera', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera closed.")

if __name__ == "__main__":
    main()
