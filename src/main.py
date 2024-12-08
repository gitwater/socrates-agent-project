
from socratic_agent import SocraticAgent
from user import User
from cli import CLI

session_states = {}
default_client_id = 1

class SessionState:
    def __init__(self, client_id):
        self.client_id = client_id
        self.dialog_lead = None
        self.dialog_follower = None
        self.question = None
        self.asked_question = False
        self.in_progress = False
        self.in_progress_sub = False
        self.first_question = True
        self.wait_for_the_user = False
        self.interactive_p = None
        self.all_questions_to_the_user = ""
        self.cli = CLI(client_id)
        self.user = User(self)
        # Aidan Agent Config
        agent_config = {
                # Socrates and Theaetetus are two AI assistants for the User to:
                'purpose': 'that will assist the User in answering their questions, providing feedback, and/or engaging with the user to help them improve their self awareness',
                'user_input': 'The users input is as follows',
                # Socrates and Theaetetus will engage in multi-round dialogue to:
                'engagement_purpose': 'analyze the Users current state and input to provide the best answer, feedback, and/or engagement for the User.',
                # Their discussion should follow a:
                'discussion_strategy': """structured problem-solving approach, such as formalizing the problem, developing
high-level strategies for solving the problem, reusing subproblem solutions where possible, critically evaluating
each other's reasoning, avoiding logical errors, and effectively communicating their ideas.""",
                # Their ultimate objective is to:
                'ultimate_objective': 'come to the next best response through reasoned discussion.',
                # If they encounter any issues with the validity of their answer, :
                'if_answer_not_valid': 'they should re-evaluate their reasoning and calculations.'
            }
        #self.agent = SocraticAgent(self, agent_config)
        self.agent = SocraticAgent(self, agent_config, "gpt-4o")

def main():
    session = SessionState(default_client_id)

    while True:
        response = session.user.interactions()
        if response != None:
            session.cli.write_json(response)
        response = session.agent.interactions()
        session.cli.write_json(response)

    # while True:
    #     response = chat(session)
    #     if response != None:
    #         session.cli.write_json(response)
    #     response = active_message(session)
    #     session.cli.write_json(response)

if __name__ == "__main__":
    main()
