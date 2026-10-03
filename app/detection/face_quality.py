import math

class FaceQualityChecker:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Center of the screen
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        
        # Stability tracking: remembering where the face was in the previous frame
        self.last_face_center = None

    def check_quality(self, faces):
        """
        Evaluates the detected faces against our strict requirements.
        Returns: (status_text, is_valid_boolean)
        """
        # RULE 1: Must have exactly one face
        if len(faces) == 0:
            self.last_face_center = None
            return "Position your face inside the circle.", False
            
        if len(faces) > 1:
            self.last_face_center = None
            return "Multiple faces! Please ensure only one person is visible.", False
            
        # Extract the single face's coordinates
        x, y, w, h = faces[0]
        
        # Calculate the exact center of the detected face
        face_center_x = x + (w // 2)
        face_center_y = y + (h // 2)
        
        # RULE 2: Size Check (Not too far, not too close)
        if w < 120 or h < 120:
            self.last_face_center = None
            return "Face too small. Move closer.", False
            
        if w > 300 or h > 300:
            self.last_face_center = None
            return "Face too large. Move back slightly.", False
            
        # RULE 3: Position Check (Must be inside our green guide)
        # Using Pythagorean theorem to calculate distance from screen center
        distance_from_center = math.sqrt((face_center_x - self.center_x)**2 + (face_center_y - self.center_y)**2)
        
        # We give an 80-pixel leniency zone (increased from 50) to prevent flickering
        if distance_from_center > 80:
            self.last_face_center = None
            return "Center your face in the guide.", False
            
        # RULE 4: Stability Check (No excessive movement)
        if self.last_face_center is not None:
            last_x, last_y = self.last_face_center
            movement = math.sqrt((face_center_x - last_x)**2 + (face_center_y - last_y)**2)
            
            # Update the memory for the next frame
            self.last_face_center = (face_center_x, face_center_y)
            
            # If the face moved more than 30 pixels (increased from 15 to handle Haar jitter)
            if movement > 30:
                return "Kindly stay still...", False
        else:
            # First time we see a valid face, we remember it but wait for the next frame to prove stability
            self.last_face_center = (face_center_x, face_center_y)
            return "Hold still...", False 
            
        # RULE 5: Frontal Pose Check
        # Our chosen Haar cascade model ('haarcascade_frontalface_default') is specifically trained
        # to only detect frontal faces. If the user turns their head too much sideways or up/down, 
        # the detector naturally drops the face, returning len(faces) == 0.
        
        # If it passed ALL rules, we are ready!
        return "Ready! Face is valid and stable.", True
