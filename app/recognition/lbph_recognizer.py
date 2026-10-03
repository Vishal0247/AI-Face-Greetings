import cv2
import os
import numpy as np
from recognition.base_recognizer import FaceRecognizer

class LBPHFaceRecognizer(FaceRecognizer):
    def __init__(self):
        # Create the LBPH model provided by opencv-contrib
        self.model = cv2.face.LBPHFaceRecognizer_create()
        
        # We need a way to map integer labels (0, 1, 2) back to names ("Vishal", "Rahul")
        self.label_to_name = {} 
        self.is_trained = False
        
    def train(self, data_dir):
        """
        Reads the saved enrollment images and trains the LBPH model.
        """
        faces = []
        labels = []
        current_label = 0
        
        print("\n--- Training Face Recognition Model ---")
        
        if not os.path.exists(data_dir):
            print("No training data found. Enroll someone first!")
            return False
            
        # Loop through every person's folder in data/people/
        for person_name in os.listdir(data_dir):
            person_dir = os.path.join(data_dir, person_name)
            
            if not os.path.isdir(person_dir):
                continue
                
            # Assign a unique integer label to this person
            self.label_to_name[current_label] = person_name
            person_faces_added = 0
            
            # Read all images for this person
            try:
                files = os.listdir(person_dir)
            except Exception as e:
                print(f"Skipping {person_name} during training: {e}")
                continue
                
            for filename in files:
                if filename.endswith(".jpg"):
                    img_path = os.path.join(person_dir, filename)
                    
                    # Load face in grayscale
                    face_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    if face_img is not None:
                        faces.append(face_img)
                        labels.append(current_label)
                        person_faces_added += 1
                        
            print(f"Loaded {person_faces_added} reference images for {person_name}")
            current_label += 1
            
        if len(faces) == 0:
            print("Not enough data to train. Enroll someone first!")
            return False
            
        # Train the OpenCV LBPH Model using our images and labels
        self.model.train(faces, np.array(labels))
        self.is_trained = True
        print("Training complete! Model is ready.")
        print("---------------------------------------\n")
        return True
        
    def predict(self, face_image):
        """
        Takes a face image, predicts the label.
        Returns: (name, distance)
        
        CRITICAL NOTE: In LBPH, 'confidence' is actually a DISTANCE measurement. 
        A LOWER distance means a BETTER match (the faces are mathematically closer).
        A distance of 0 means perfectly identical. 
        """
        if not self.is_trained:
            return "UNKNOWN", 999.0
            
        # LBPH requires grayscale images
        if len(face_image.shape) > 2:
            face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
        # Resize to exactly the same size we used during enrollment
        standard_face = cv2.resize(face_image, (200, 200))
        
        # Predict the identity
        label, distance = self.model.predict(standard_face)
        
        # Get the name string from our dictionary
        name = self.label_to_name.get(label, "UNKNOWN")
        return name, distance
