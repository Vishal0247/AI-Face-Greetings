import os
import cv2
import time

class EnrollmentManager:
    def __init__(self, data_dir="data/people"):
        # Where we will save the photos
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", data_dir)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.is_enrolling = False
        self.person_name = None
        self.samples_collected = 0
        self.required_samples = 3
        self.last_capture_time = 0
        self.capture_delay = 1.0 # Wait 1 second between captures so they aren't identical
        
    def start_enrollment(self, name):
        """Starts the enrollment process for a specific person."""
        self.person_name = name
        self.is_enrolling = True
        self.samples_collected = 0
        self.last_capture_time = time.time()
        
        # Create a directory specifically for this person
        person_dir = os.path.join(self.data_dir, self.person_name)
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
            
    def process_frame(self, frame, faces, is_valid):
        """
        Processes a frame during enrollment mode.
        It will ONLY capture a photo if the FaceQualityChecker said 'is_valid = True'.
        Returns a status string to display on screen.
        """
        if not self.is_enrolling:
            return ""
            
        if self.samples_collected >= self.required_samples:
            self.is_enrolling = False
            return f"Enrollment complete for {self.person_name}!"
            
        if not is_valid:
            # We don't capture bad faces!
            return f"Enrollment paused. Please follow the guide above."
            
        # The face is valid! Check if enough time has passed since our last capture
        current_time = time.time()
        if current_time - self.last_capture_time > self.capture_delay:
            # Time to CAPTURE!
            x, y, w, h = faces[0]
            
            # Crop exactly the face region out of the frame
            face_roi = frame[y:y+h, x:x+w]
            
            # Convert to grayscale (Recognition models usually prefer grayscale)
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Resize it to a standard size (e.g. 200x200) for consistency
            standard_face = cv2.resize(gray_face, (200, 200))
            
            # Save it to disk
            person_dir = os.path.join(self.data_dir, self.person_name)
            filename = os.path.join(person_dir, f"sample_{self.samples_collected + 1}.jpg")
            cv2.imwrite(filename, standard_face)
            
            # Update our counters
            self.samples_collected += 1
            self.last_capture_time = current_time
            
        return f"Capturing: {self.samples_collected}/{self.required_samples}"

    def save_face_from_image(self, name, face_roi):
        """Saves a cropped face ROI directly for enrollment, bypassing the live camera process."""
        person_dir = os.path.join(self.data_dir, name)
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
            
        # Convert to grayscale
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Resize to standard size
        standard_face = cv2.resize(gray_face, (200, 200))
        
        # Save augmented copies so the recognizer has a better dataset (Data Augmentation)
        # Original
        cv2.imwrite(os.path.join(person_dir, "sample_1.jpg"), standard_face)
        
        # Brighter
        bright = cv2.convertScaleAbs(standard_face, alpha=1.2, beta=30)
        cv2.imwrite(os.path.join(person_dir, "sample_2.jpg"), bright)
        
        # Darker
        dark = cv2.convertScaleAbs(standard_face, alpha=0.8, beta=-30)
        cv2.imwrite(os.path.join(person_dir, "sample_3.jpg"), dark)
        
        # Flipped
        flipped = cv2.flip(standard_face, 1)
        cv2.imwrite(os.path.join(person_dir, "sample_4.jpg"), flipped)
            
        return True
