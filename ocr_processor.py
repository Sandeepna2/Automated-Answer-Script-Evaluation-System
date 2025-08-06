# import pytesseract
# import re
# import string
# import difflib

# class OCRProcessor:
#     def extract_text(self, image):
#         """
#         Extract raw text from an image using Tesseract OCR.
#         """
#         return pytesseract.image_to_string(image)

#     def extract_answers(self, image, question_patterns):
#         """
#         Extract student answers using question patterns.
#         Captures text between questions as answers.
#         """
#         text = self.extract_text(image)
#         lines = text.splitlines()

#         combined_pattern = '|'.join(question_patterns)
#         question_regex = re.compile(combined_pattern, re.IGNORECASE)
#         q_key_pattern = re.compile(r'(Q\d+)', re.IGNORECASE)

#         answers = {}
#         current_question = None
#         buffer = []

#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue

#             if question_regex.search(line):
#                 # Save previous answer
#                 if current_question and buffer:
#                     answers[current_question] = ' '.join(buffer).strip()
#                     buffer = []

#                 # Extract question key
#                 match = q_key_pattern.search(line)
#                 if match:
#                     current_question = match.group(1).upper()

#                     # Extract inline answer on same line (e.g. Q2: Answer here)
#                     parts = line.split(':', 1)
#                     if len(parts) > 1 and parts[1].strip():
#                         buffer.append(parts[1].strip())
#             elif current_question:
#                 buffer.append(line)

#         # Save final answer
#         if current_question and buffer:
#             answers[current_question] = ' '.join(buffer).strip()

#         return answers

#     def align_answers(self, student_answers, model_answers):
#         """
#         Align student answers to corresponding model answers.
#         """
#         aligned = {}
#         for key in model_answers:
#             aligned[key] = {
#                 'student_answer': student_answers.get(key, '').strip(),
#                 'model_answer': model_answers[key]
#             }
#         return aligned


import pytesseract
import cv2
import re
from PIL import Image

class OCRProcessor:
    def extract_text(self, image_path):
        """
        Extract raw text from an image using Tesseract OCR with preprocessing.
        """
        # Load image using OpenCV
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        # Apply binary thresholding for better OCR
        _, processed_image = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)

        # Save the processed image for debugging (optional)
        cv2.imwrite("processed_image.png", processed_image)

        # Perform OCR with optimized configuration
        text = pytesseract.image_to_string(Image.fromarray(processed_image), config="--psm 6")
        return text

    def extract_answers(self, image_path, question_patterns):
        """
        Extract answers from text using question patterns, stopping at the next question.
        """
        text = self.extract_text(image_path)
        lines = text.splitlines()

        combined_pattern = '|'.join(question_patterns)
        question_regex = re.compile(combined_pattern, re.IGNORECASE)
        q_key_pattern = re.compile(r'(Q\d)', re.IGNORECASE)

        answers = {}
        current_question = None
        buffer = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if question_regex.search(line):
                if current_question and buffer:
                    # Save previous question's answer
                    answers[current_question] = ' '.join(buffer).strip()
                    buffer = []

                match = q_key_pattern.search(line)
                if match:
                    current_question = match.group(1).upper()
            elif current_question:
                buffer.append(line)

        # Save last question's answer
        if current_question and buffer:
            answers[current_question] = ' '.join(buffer).strip()

        return answers

    def align_answers(self, student_answers, model_answers):
        """
        Align student answers to corresponding model answers.
        """
        aligned = {}
        for key in model_answers:
            aligned[key] = {
                'student_answer': student_answers.get(key, '').strip(),
                'model_answer': model_answers[key]
            }
        return aligned
