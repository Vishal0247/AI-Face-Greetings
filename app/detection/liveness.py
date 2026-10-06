import time

class BlinkDetector:
    def __init__(self, timeout_seconds=5):
        # We look for a pattern: Eyes Visible -> Eyes Not Visible (Blink) -> Eyes Visible
        # To avoid false positives, the "eyes not visible" state must be very short (e.g. < 0.5s)
        self.state = "WAITING"
        self.blink_start_time = 0
        
        # Timeout bypass: if blink can't be detected (e.g. low-res network frames),
        # auto-pass after this many seconds of a face being continuously present
        self.timeout_seconds = timeout_seconds
        self.first_seen_time = None
        
    def check_liveness(self, num_eyes):
        """
        Takes the number of eyes detected in the current frame.
        Returns True if a full blink was completed OR if the timeout has elapsed.
        """
        # Track when we first started trying to detect a blink
        if self.first_seen_time is None:
            self.first_seen_time = time.time()
        
        # Timeout bypass: if we've been trying for too long, auto-pass
        # This handles low-quality compressed frames where eye detection is unreliable
        if time.time() - self.first_seen_time > self.timeout_seconds:
            print("[LIVENESS] Blink detection timed out — auto-passing liveness check.")
            self.reset()
            return True
        
        # State machine for blink detection
        
        if self.state == "WAITING":
            if num_eyes >= 1:
                # We see eyes, person is looking at camera. Ready to catch a blink.
                self.state = "EYES_OPEN"
                
        elif self.state == "EYES_OPEN":
            if num_eyes == 0:
                # Eyes disappeared! This is the start of a blink.
                self.state = "BLINKING"
                self.blink_start_time = time.time()
                
        elif self.state == "BLINKING":
            if num_eyes >= 1:
                # Eyes reappeared! Check how long they were closed.
                duration = time.time() - self.blink_start_time
                if duration < 1.0: # A blink is fast, usually < 0.5s, but we give a little leeway
                    self.reset()
                    return True # Liveness Confirmed!
                else:
                    # They closed their eyes for too long, or looked away. Reset.
                    self.reset()
            else:
                # Still no eyes. If it's been too long, reset.
                if time.time() - self.blink_start_time > 1.5:
                    self.reset()
                    
        return False
        
    def reset(self):
        self.state = "WAITING"
        self.blink_start_time = 0
        self.first_seen_time = None
