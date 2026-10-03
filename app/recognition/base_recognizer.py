class FaceRecognizer:
    """
    Abstract base class for face recognition.
    This architecture allows us to easily swap out LBPH for a stronger Deep Learning model later 
    without changing the rest of our application code.
    """
    def train(self, data_dir):
        raise NotImplementedError("Subclasses must implement train()")
        
    def predict(self, face_image):
        raise NotImplementedError("Subclasses must implement predict()")
