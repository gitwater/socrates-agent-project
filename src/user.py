import json

class User:
    def __init__(self, session):
        self.session = session

    def generate_response(self, user_input, mode="question"):
        if mode == "question":
            return f"You just said: {user_input}\n\nA conversation among (Socrates, Theaetetus, and Plato) will begin shortly..."
        elif mode == "feedback":
            return f"Received your feedback: {user_input}"
        return "Connecting..."

    def interactions(self):
        chat_response = None
        if self.session.question is None or self.session.wait_for_the_user:
            user_input = self.session.cli.read_input()
            if self.session.question is None:
                self.session.question = user_input
                self.session.agent.socrates.set_question(self.session.question)
                self.session.agent.theaetetus.set_question(self.session.question)
                self.session.agent.plato.set_question(self.session.question)
                response = self.generate_response(user_input, mode="question")

            if self.session.wait_for_the_user:
                feedback = user_input
                self.session.agent.socrates.add_feedback(self.session.all_questions_to_the_user, feedback)
                self.session.agent.theaetetus.add_feedback(self.session.all_questions_to_the_user, feedback)
                self.session.agent.plato.add_feedback(self.session.all_questions_to_the_user, feedback)
                self.session.all_questions_to_the_user = ""
                self.session.wait_for_the_user = False
                response = self.generate_response(user_input, mode="feedback")

            chat_response = json.dumps([{'role': 'System','response': response}])

        return chat_response