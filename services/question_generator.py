import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

class QuestionGenerator:
    def __init__(self):
        load_dotenv()
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_questions(self, topic, difficulty, num_questions=5):
        prompt = f"""Generate exactly {num_questions} multiple choice questions about {topic} at {difficulty} level.
        
        For each question, strictly follow this format (including exact labels and spacing):

        Q: [Question text here]
        Type: MCQ
        Options: A) [First option], B) [Second option], C) [Third option], D) [Fourth option]
        Correct: [A/B/C/D]

        Example:
        Q: What is Python's primary use case?
        Type: MCQ
        Options: A) Web development, B) Data science, C) General-purpose programming, D) Mobile development
        Correct: C

        Requirements:
        - Each question must be clear and concise
        - Options must be labeled exactly as A), B), C), D)
        - Correct answer must be just A, B, C, or D
        - Questions should be at {difficulty} level
        - Focus on {topic} concepts
        - Generate exactly {num_questions} questions
        """
        
        try:
            response = self.model.generate_content(prompt)
            questions = self._parse_questions(response.text)
            if not questions:
                # Retry once if parsing failed
                response = self.model.generate_content(prompt)
                questions = self._parse_questions(response.text)
            return questions
        except Exception as e:
            print(f"Error in generate_questions: {str(e)}")
            print("Raw response:", response.text if 'response' in locals() else "No response")
            raise

    def _parse_questions(self, response_text):
        questions = []
        
        # Split into question blocks
        question_blocks = re.split(r'\n\s*\n', response_text)
        
        for block in question_blocks:
            try:
                # Skip empty blocks
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                question = {}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Q:'):
                        question['question_text'] = line[2:].strip()
                    elif line.startswith('Type:'):
                        question['question_type'] = line[5:].strip()
                    elif line.startswith('Options:'):
                        # Extract options, removing A), B), etc.
                        options_text = line[8:].strip()
                        options = []
                        for opt in re.findall(r'[A-D]\)(.*?)(?=[A-D]\)|$)', options_text):
                            opt = opt.strip(', ')
                            if opt:
                                options.append(opt.strip())
                        question['options'] = options
                    elif line.startswith('Correct:'):
                        correct_letter = line[8:].strip().upper()
                        if correct_letter in ['A', 'B', 'C', 'D'] and 'options' in question:
                            letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
                            idx = letter_to_index[correct_letter]
                            if idx < len(question['options']):
                                question['correct_answer'] = question['options'][idx]
                
                # Validate question before adding
                if self._is_valid_question(question):
                    questions.append(question)
            
            except Exception as e:
                print(f"Error parsing question block: {str(e)}")
                print("Block:", block)
                continue
        
        if not questions:
            raise ValueError("No valid questions could be parsed. Please try again.")
        
        return questions

    def _is_valid_question(self, question):
        """Validate if a question has all required fields properly filled."""
        required_fields = ['question_text', 'question_type', 'options', 'correct_answer']
        
        # Check if all required fields exist and are not None or empty
        if not all(field in question and question[field] for field in required_fields):
            return False
        
        # For MCQ, ensure we have exactly 4 options
        if question['question_type'] == 'MCQ' and len(question['options']) != 4:
            return False
        
        # Ensure correct_answer is in options for MCQ
        if question['question_type'] == 'MCQ' and question['correct_answer'] not in question['options']:
            return False
        
        return True 
