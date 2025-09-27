class HighScoreManager:
    """Manages reading and writing the high score to a file."""

    def __init__(self, filename="highscore.txt"):
        self.filename = filename
        self.high_score = 0
        self.load_high_score()

    def load_high_score(self):
        """Loads the high score from the file. If the file doesn't exist, sets high score to 0."""
        try:
            with open(self.filename, 'r') as f:
                score_str = f.read()
                if score_str.strip():
                    self.high_score = int(score_str)
                else:
                    self.high_score = 0
        except (FileNotFoundError, ValueError):
            self.high_score = 0
            print(f"High score file ('{self.filename}') not found or invalid. Starting with a high score of 0.")

    def save_high_score(self, new_score):
        """Saves the new score to the file if it's higher than the current high score."""
        if new_score > self.high_score:
            self.high_score = new_score
            try:
                with open(self.filename, 'w') as f:
                    f.write(str(self.high_score))
                print(f"New high score saved: {self.high_score}")
            except IOError as e:
                print(f"Error saving high score to '{self.filename}': {e}")