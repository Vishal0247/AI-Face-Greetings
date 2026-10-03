class VerificationManager:
    def __init__(self):
        # --- CALIBRATION SETTINGS ---
        self.absolute_threshold = 85.0  
        self.required_consecutive_frames = 5
        
        # State tracking
        self.history = [] 
        self.verified_person = None
        
        # Grace Period for Stability
        self.invalid_frames_count = 0
        self.max_invalid_frames = 2 # Drops the identity almost instantly when they leave the circle
        
    def reset(self):
        """
        Resets the history completely.
        """
        self.history = []
        self.verified_person = None
        
    def handle_invalid_frame(self):
        """
        Called when the face is missing, moving, or badly positioned.
        Provides a grace period before resetting the verified state to prevent flickering.
        Returns the CURRENT verified person (which becomes None if grace period expires).
        """
        self.invalid_frames_count += 1
        if self.invalid_frames_count > self.max_invalid_frames:
            self.history = []
            self.verified_person = None
            
        return self.verified_person
        
    def process_prediction(self, predicted_name, distance):
        """
        Applies our strict security rules to a raw prediction.
        Returns: (status_text_to_display, verified_name_or_none)
        """
        # We got a good frame, reset the grace counter
        self.invalid_frames_count = 0
        
        # RULE 1: Absolute Threshold (Reject if distance is too high)
        if distance > self.absolute_threshold:
            predicted_name = "UNKNOWN"
            
        # Add this frame's guess to our short-term memory
        self.history.append(predicted_name)
        
        # Keep only the last 'required_consecutive_frames' items
        if len(self.history) > self.required_consecutive_frames:
            self.history.pop(0)
            
        # If we haven't gathered enough stable frames yet
        if len(self.history) < self.required_consecutive_frames:
            return f"Verifying... ({len(self.history)}/{self.required_consecutive_frames})", self.verified_person
            
        # RULE 2: Multi-Frame Consistency
        # Check if ALL items in our history are exactly the same
        all_match = all(name == self.history[0] for name in self.history)
        
        if all_match:
            # They all match!
            if self.history[0] == "UNKNOWN":
                return "Unknown Person", None
            else:
                self.verified_person = self.history[0]
                return f"IDENTITY VERIFIED: {self.verified_person}!", self.verified_person
        else:
            # The predictions are fluctuating (e.g., Vishal, Unknown, Vishal...)
            return "Verifying... (Unstable match)", self.verified_person
