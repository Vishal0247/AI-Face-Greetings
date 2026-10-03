import os
import urllib.request
import cv2

class FaceDetector:
    def __init__(self):
        # Sometimes OpenCV installations (like OpenCV 5.0) don't map the data paths correctly.
        # To make this perfectly robust, we will download the file directly into our project folder if it's missing.
        cascade_filename = 'haarcascade_frontalface_default.xml'
        
        # Get the current folder path (where this face_detector.py file is)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cascade_path = os.path.join(current_dir, cascade_filename)
        
        # If the file doesn't exist, download it from OpenCV's official GitHub
        if not os.path.exists(cascade_path):
            print(f"Downloading {cascade_filename} (this only happens once)...")
            url = f"https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{cascade_filename}"
            urllib.request.urlretrieve(url, cascade_path)
            print("Download complete!")

        eye_cascade_filename = 'haarcascade_eye_tree_eyeglasses.xml'
        self.eye_cascade_path = os.path.join(current_dir, eye_cascade_filename)
        if not os.path.exists(self.eye_cascade_path):
            print(f"Downloading {eye_cascade_filename} (this only happens once)...")
            url = f"https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{eye_cascade_filename}"
            urllib.request.urlretrieve(url, self.eye_cascade_path)
            print("Download complete!")

        # Load the pre-trained Haar Cascade model for frontal face detection
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.eye_cascade = cv2.CascadeClassifier(self.eye_cascade_path)
        
        if self.face_cascade.empty():
            print(f"CRITICAL ERROR: Failed to load cascade from {cascade_path}")
        
    def detect_faces(self, frame):
        """
        Detects faces in a given frame.
        Returns a list of rectangles representing the faces: [(x, y, width, height), ...]
        """
        # Face detection algorithms work much faster and more reliably on grayscale (black & white) images
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect the faces
        # - scaleFactor=1.1: Compensates for faces being closer or further away from the camera.
        # - minNeighbors=5: How many overlapping detections are needed to be confident it's a real face.
        # - minSize=(100, 100): Ignore tiny faces in the background; we only want faces close to the camera.
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )
        
        return faces

    def detect_eyes(self, frame, face_rect):
        """
        Detects eyes within a given face rectangle.
        Returns the number of eyes detected.
        """
        x, y, w, h = face_rect
        # Extract the face region of interest (ROI)
        roi_color = frame[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
        
        # Eyes are usually in the top half of the face
        half_h = int(h / 1.5)
        gray = gray[0:half_h, :]
        
        eyes = self.eye_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(20, 20)
        )
        return len(eyes)
