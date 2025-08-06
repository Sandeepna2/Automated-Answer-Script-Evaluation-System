
import sys
import cv2
import pytesseract
import re
import difflib
import numpy as np

# === REQUIRED: Set Tesseract path ===


pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Admin\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


class OCRProcessor: 
    def extract_text(self, image):
        """
        Extract raw text from a preprocessed image using Tesseract OCR.
        """
        processed_image = self.preprocess_image(image)
        custom_config = r'--oem 3 --psm 6'
        return pytesseract.image_to_string(processed_image, config=custom_config)

    def preprocess_image(self, img):
        """
        Preprocessing steps:
        - Grayscale
        - Resize for clarity
        - Noise reduction
        - Adaptive thresholding
        - Sharpening
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (0, 0), fx=3, fy=3, interpolation=cv2.INTER_LINEAR)

        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 12
        )

        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(binary, -1, kernel)

        return sharpened

    def extract_answers(self, text, question_patterns):
        """
        Extract student answers using regex patterns for question labels.
        """
        answers = {}
        lines = text.splitlines()
        current_question = None
        buffer = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern in question_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if current_question and buffer:
                        answers[current_question] = ' '.join(buffer).strip()
                        buffer = []

                    current_question = match.group(1)
                    buffer = [line.replace(current_question, "").strip()]
                    break
            else:
                if current_question:
                    buffer.append(line)

        if current_question and buffer:
            answers[current_question] = ' '.join(buffer).strip()

        return answers


def score_answer(student_answer, keywords, total_marks=5):
    """
    Compare a student's answer to the expected keywords and return a score.
    """
    student_answer = student_answer.lower().strip()
    matched = 0
    seen = set()

    for kw in keywords:
        if kw.lower() in student_answer:
            matched += 1
            seen.add(kw)

    for kw in keywords:
        if kw in seen:
            continue
        ratio = difflib.SequenceMatcher(None, kw.lower(), student_answer).ratio()
        if ratio > 0.7:
            matched += 0.5

    return round((matched / len(keywords)) * total_marks, 2) if keywords else 0


# ========== MAIN LOGIC ==========
image_path = 'sample_exam_image.jpg'
# image_path = 'student_answer.jpg'

image = cv2.imread(image_path)

if image is None:
    print(f"Error: Unable to load image from path: {image_path}")
    sys.exit(1)

question_patterns = [
    r'(Q1)[:.\s]?(.*)',
    r'(Q2)[:.\s]?(.*)',
    r'(Q3)[:.\s]?(.*)'
]

model_answers = {
    'Q1': 'Gravity attracts things to the ground.',
    'Q2': 'Plants use light for growing.',
    'Q3': 'Paris is the capital city in France.'
    
    
    
}

keywords_map = {
    'Q1': ['gravity', 'force', 'pulls', 'objects'],
    'Q2': ['photosynthesis', 'plants', 'sunlight', 'food', 'process'],
    'Q3': ['capital', 'france', 'paris']
    
    # 'Q1': ['computer', 'electronic', 'device', 'processes', 'stores', 'data', 'instructions'],
    #  'Q2': ['CPU', 'RAM', 'storage', 'hard drives', 'SSDs', 'input devices', 'output devices'],
    #  'Q3': ['CPU', 'Central Processing Unit', 'instructions', 'processing', 'data']
}

ocr = OCRProcessor()
text = ocr.extract_text(image)

print("=== OCR Raw Text ===")
print(text)
print("====================\n")

student_answers = ocr.extract_answers(text, question_patterns)

print("=== Extracted Student Answers ===")
for key, val in student_answers.items():
    print(f"{key}: {val}\n")

aligned = {q: {'student_answer': student_answers.get(q, ''), 'model_answer': model_answers[q]} for q in model_answers}

print("\n=== Final Aligned Answers ===")
for question, data in aligned.items():
    print(f"{question}:")
    print(f"  Student Answer: {data['student_answer']}")
    print(f"  Model Answer:   {data['model_answer']}\n")

print("=== Scoring ===")
for question, data in aligned.items():
    student_ans = data['student_answer']
    keywords = keywords_map.get(question, [])
    if student_ans:
        score = score_answer(student_ans, keywords)
        print(f"{question}: {score}/5 marks")
    else:
        print(f"{question}: 0/5 marks (No answer extracted)")
