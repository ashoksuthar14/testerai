import streamlit as st
from database.database import Database
from services.question_generator import QuestionGenerator
import time

class QuizApp:
    def __init__(self):
        self.db = Database()
        self.question_generator = QuestionGenerator()
        
    def main(self):
        st.set_page_config(page_title="AI Quiz Master", layout="wide")
        
        # Add custom CSS with blue theme
        st.markdown("""
            <style>
                .main {
                    padding: 2rem;
                }
                .quiz-container {
                    background-color: #E3F2FD;  /* Light blue background */
                    padding: 2rem;
                    border-radius: 15px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    margin: 1rem 0;
                }
                .stButton>button {
                    width: 100%;
                    border-radius: 20px;
                    height: 3em;
                    background-color: #1976D2;  /* Material Blue */
                    color: white;
                }
                .stButton>button:hover {
                    background-color: #1565C0;  /* Darker blue on hover */
                }
                .stRadio>label {
                    font-size: 1.1em;
                    padding: 10px;
                    color: #1976D2;  /* Blue text */
                }
                .css-1d391kg {
                    padding: 2rem 1rem;
                }
            </style>
        """, unsafe_allow_html=True)
        
        st.title("🎯 AI Quiz Master")
        
        # User Authentication
        if 'user_id' not in st.session_state:
            self.show_login()
        else:
            self.show_quiz_interface()
    
    def show_login(self):
        st.header("Welcome! Please login or register")
        username = st.text_input("Username")
        if st.button("Start Quiz"):
            if username:
                # Add user to database if not exists
                # Set session state
                st.session_state.user_id = 1  # Replace with actual user_id
                st.rerun()
    
    def show_quiz_interface(self):
        st.sidebar.title("Quiz Settings")
        topic = st.sidebar.selectbox("Select Topic", 
            ["Python", "JavaScript", "Machine Learning", "Data Science"])
        
        if st.sidebar.button("Start New Quiz"):
            with st.spinner("Generating questions..."):
                try:
                    # Set quiz start time
                    st.session_state.quiz_start_time = time.time()
                    st.session_state.current_topic = topic  # Store current topic
                    
                    questions = self.question_generator.generate_questions(
                        topic=topic,
                        difficulty=self.get_user_difficulty(st.session_state.user_id)
                    )
                    
                    if questions and len(questions) > 0:
                        st.session_state.questions = questions
                        st.session_state.current_question = 0
                        st.session_state.responses = []
                        st.rerun()
                    else:
                        st.error("Failed to generate questions. Please try again.")
                except Exception as e:
                    st.error(f"Error generating questions: {str(e)}")
                    st.error("Please try again with a different topic or refresh the page.")
                    return
            
        if 'questions' in st.session_state and st.session_state.questions:
            self.display_question()
    
    def display_question(self):
        if not hasattr(st.session_state, 'questions') or not st.session_state.questions:
            st.warning("No questions available. Please start a new quiz.")
            return
        
        # Initialize current answer in session state if not exists
        if 'current_answer' not in st.session_state:
            st.session_state.current_answer = None
        
        question = st.session_state.questions[st.session_state.current_question]
        
        with st.container():
            st.markdown("""
                <style>
                .question-card {
                    background-color: #f0f2f6;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown(f"### Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
                st.markdown(f"**{question['question_text']}**")
                
                if question['question_type'] == 'MCQ':
                    if 'options' in question and question['options']:
                        # Use radio buttons instead of individual buttons for options
                        st.session_state.current_answer = st.radio(
                            "Choose your answer:",
                            question['options'],
                            key=f"radio_{st.session_state.current_question}"
                        )
                    else:
                        st.error("Question options not available")
                        return
                else:
                    st.session_state.current_answer = st.text_input(
                        "Your answer:",
                        key=f"text_answer_{st.session_state.current_question}"
                    )
                
                # Progress bar
                progress = (st.session_state.current_question + 1) / len(st.session_state.questions)
                st.progress(progress)
                
                # Submit button
                if st.button(
                    "Submit Answer", 
                    key=f"submit_{st.session_state.current_question}",
                    disabled=not st.session_state.current_answer
                ):
                    self.process_answer(question, st.session_state.current_answer)
                    # Clear current answer after submission
                    st.session_state.current_answer = None
    
    def process_answer(self, question, answer):
        if not answer:
            st.warning("Please select an answer before submitting.")
            return
        
        is_correct = answer.strip().lower() == question['correct_answer'].strip().lower()
        
        if is_correct:
            st.success("Correct! 🎉")
        else:
            st.error(f"Wrong answer. The correct answer was: {question['correct_answer']}")
        
        # Store response in database
        self.store_response(question, answer, is_correct)
        
        # Move to next question
        if st.session_state.current_question < len(st.session_state.questions) - 1:
            st.session_state.current_question += 1
            # Clear current answer for next question
            st.session_state.current_answer = None
            st.rerun()
        else:
            st.success("Quiz completed! 🎉")
            self.show_quiz_summary()
    
    def show_quiz_summary(self):
        st.markdown("""
            <style>
            .badge-card {
                background-color: #E3F2FD;
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                border: 2px solid #1976D2;
                text-align: center;
            }
            .metric-card {
                background-color: #E3F2FD;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                text-align: center;
            }
            .metric-card h2 {
                color: #1976D2;
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }
            .metric-card h3 {
                color: #333333;
                font-size: 1.2em;
            }
            .badge-card .emoji {
                font-size: 3.5em;
                margin: 10px 0;
            }
            .badge-card .title {
                color: #1976D2;
                font-size: 1.3em;
                font-weight: bold;
                margin: 10px 0;
            }
            .badge-card .description {
                color: #333333;
                font-size: 1em;
            }
            .improvement-card {
                background-color: #E3F2FD;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #1976D2;
                margin: 10px 0;
                color: #333333;
            }
            </style>
        """, unsafe_allow_html=True)

        # Calculate statistics
        total_questions = len(st.session_state.questions)
        correct_answers = sum(1 for q in st.session_state.responses if q['is_correct'])
        percentage = (correct_answers / total_questions) * 100
        
        # Show celebration animation if score is good
        if percentage >= 70:
            st.balloons()
            st.markdown(f'<div class="celebration">🎉 Congratulations! 🎉</div>', unsafe_allow_html=True)
        
        st.header("Quiz Summary")
        
        # Display metrics in a nicer format
        cols = st.columns(3)
        with cols[0]:
            st.markdown("""
                <div class="metric-card">
                    <h3>Total Questions</h3>
                    <h2>{}</h2>
                </div>
            """.format(total_questions), unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown("""
                <div class="metric-card">
                    <h3>Correct Answers</h3>
                    <h2>{}</h2>
                </div>
            """.format(correct_answers), unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown("""
                <div class="metric-card">
                    <h3>Score</h3>
                    <h2>{}%</h2>
                </div>
            """.format(round(percentage, 1)), unsafe_allow_html=True)

        # Award badges based on performance
        badges_earned = self.calculate_badges(percentage, correct_answers, total_questions)
        
        if badges_earned:
            st.markdown("### 🏆 Badges Earned")
            for badge in badges_earned:
                    st.markdown(f"""
                        <div class="badge-card">
                        <div class="emoji">{badge['emoji']}</div>
                        <div class="title">{badge['name']}</div>
                        <div class="description">{badge['description']}</div>
                        </div>
                    """, unsafe_allow_html=True)

        # Areas for improvement
        st.markdown("### 📈 Performance Analysis")
        improvement_areas = self.analyze_performance(st.session_state.responses)
        
        for area in improvement_areas:
            st.markdown(f"""
                <div class="improvement-card">
                    <strong style="color: #1976D2;">{area['topic'].upper()}</strong><br>
                    {area['suggestion']}
                </div>
            """, unsafe_allow_html=True)

        # Detailed question analysis
        st.markdown("### 📝 Detailed Analysis")
        for idx, response in enumerate(st.session_state.responses):
            with st.expander(f"Question {idx + 1}"):
                st.markdown(f"**Question:** {response['question_text']}")
                st.markdown(f"**Your Answer:** {response['user_answer']}")
                st.markdown(f"**Correct Answer:** {response['correct_answer']}")
                if response['is_correct']:
                    st.success("Correct ✅")
                else:
                    st.error("Incorrect ❌")
                
        if st.button("Start New Quiz", key="new_quiz_summary"):
            st.session_state.clear()
            st.rerun()

    def calculate_badges(self, percentage, correct_answers, total_questions):
        badges = []
        
        # Initialize quiz_duration
        quiz_duration = float('inf')  # Default to infinity if no start time
        if 'quiz_start_time' in st.session_state:
            quiz_duration = time.time() - st.session_state.quiz_start_time
        
        # Achievement Badges
        if percentage == 100:
            badges.append({
                'name': 'Grand Master',
                'emoji': '🏆',
                'description': 'Perfect score! You\'ve achieved mastery!'
            })
            # Special Achievement Badge for perfect score with speed
            if quiz_duration < 180:  # 3 minutes
                badges.append({
                    'name': 'Perfect Storm',
                    'emoji': '⚡🎯',
                    'description': 'Perfect score with amazing speed!'
                })
        elif percentage >= 90:
            badges.append({
                'name': 'Elite Scholar',
                'emoji': '🎓',
                'description': 'Outstanding performance! Top-tier knowledge!'
            })
        elif percentage >= 80:
            badges.append({
                'name': 'Knowledge Sage',
                'emoji': '🦉',
                'description': 'Great wisdom and understanding!'
            })
        elif percentage >= 70:
            badges.append({
                'name': 'Rising Phoenix',
                'emoji': '🦅',
                'description': 'Soaring to new heights of knowledge!'
            })

        # Speed Badges
        if quiz_duration < 120:  # 2 minutes
            badges.append({
                'name': 'Speed Demon',
                'emoji': '⚡',
                'description': 'Lightning fast responses!'
            })
        elif quiz_duration < 180:  # 3 minutes
            badges.append({
                'name': 'Quick Thinker',
                'emoji': '🧠',
                'description': 'Swift and accurate!'
            })

        # Streak Badges
        consecutive_correct = 0
        max_consecutive = 0
        for response in st.session_state.responses:
            if response['is_correct']:
                consecutive_correct += 1
                max_consecutive = max(max_consecutive, consecutive_correct)
            else:
                consecutive_correct = 0
        
        if max_consecutive >= 5:
            badges.append({
                'name': 'Unstoppable',
                'emoji': '🔥',
                'description': f'Amazing streak of {max_consecutive} correct answers!'
            })
        elif max_consecutive >= 3:
            badges.append({
                'name': 'Hot Streak',
                'emoji': '🌟',
                'description': 'On fire with consecutive correct answers!'
            })

        # Improvement Badges
        if 'last_score' in st.session_state:
            improvement = percentage - st.session_state.last_score
            if improvement >= 20:
                badges.append({
                    'name': 'Quantum Leap',
                    'emoji': '🚀',
                    'description': f'Incredible improvement of {round(improvement)}%!'
                })
            elif improvement >= 10:
                badges.append({
                    'name': 'Rising Star',
                    'emoji': '⭐',
                    'description': f'Great improvement of {round(improvement)}%!'
                })

        # Topic Mastery Badges
        topic_badges = {
            'Python': {'emoji': '🐍', 'name': 'Python Charmer'},
            'JavaScript': {'emoji': '💻', 'name': 'JavaScript Wizard'},
            'Machine Learning': {'emoji': '🤖', 'name': 'AI Innovator'},
            'Data Science': {'emoji': '📊', 'name': 'Data Sage'}
        }
        
        if percentage >= 85 and topic_badges.get(st.session_state.current_topic):
            badge_info = topic_badges[st.session_state.current_topic]
            badges.append({
                'name': badge_info['name'],
                'emoji': badge_info['emoji'],
                'description': f'Mastered {st.session_state.current_topic}!'
            })

        # Persistence Badges
        if 'quiz_attempts' not in st.session_state:
            st.session_state.quiz_attempts = 1
        else:
            st.session_state.quiz_attempts += 1

        if st.session_state.quiz_attempts >= 5:
            badges.append({
                'name': 'Dedicated Scholar',
                'emoji': '📚',
                'description': 'Completed 5 quizzes! True dedication!'
            })

        # Store the current score for future comparison
        st.session_state.last_score = percentage
        
        return badges

    def analyze_performance(self, responses):
        improvement_areas = []
        incorrect_responses = [r for r in responses if not r['is_correct']]
        
        if len(incorrect_responses) > 0:
            # Group incorrect answers by topic/pattern
            topics = {}
            for response in incorrect_responses:
                # You can enhance this by adding topic detection logic
                topic = self.detect_topic(response['question_text'])
                topics[topic] = topics.get(topic, 0) + 1
            
            # Generate improvement suggestions
            for topic, count in topics.items():
                improvement_areas.append({
                    'topic': topic,
                    'suggestion': self.get_improvement_suggestion(topic, count)
                })
        
        return improvement_areas

    def detect_topic(self, question_text):
        # Simple topic detection - you can make this more sophisticated
        topics = {
            'syntax': ['syntax', 'code', 'function', 'variable'],
            'concepts': ['concept', 'theory', 'principle'],
            'practical': ['implement', 'create', 'build', 'write'],
            'logic': ['logic', 'algorithm', 'solve']
        }
        
        question_lower = question_text.lower()
        for topic, keywords in topics.items():
            if any(keyword in question_lower for keyword in keywords):
                return topic
        return 'general'

    def get_improvement_suggestion(self, topic, count):
        suggestions = {
            'syntax': "Review basic syntax and coding conventions. Practice writing code snippets.",
            'concepts': "Focus on understanding theoretical concepts through documentation and tutorials.",
            'practical': "Get more hands-on practice by building small projects.",
            'logic': "Practice problem-solving exercises and algorithm challenges.",
            'general': "Review the fundamentals and try different types of questions."
        }
        return suggestions.get(topic, "Practice more questions in this area.")
    
    def store_response(self, question, answer, is_correct):
        if 'responses' not in st.session_state:
            st.session_state.responses = []
        
        response = {
            'question_text': question['question_text'],
            'question_type': question['question_type'],
            'user_answer': answer,
            'correct_answer': question['correct_answer'],
            'is_correct': is_correct
        }
        st.session_state.responses.append(response)
    
    def get_user_difficulty(self, user_id):
        # Get user's current difficulty level from database
        return "beginner"

if __name__ == "__main__":
    app = QuizApp()
    app.main() 