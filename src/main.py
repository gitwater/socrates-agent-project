
from socratic_agent import Agent
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
        #self.agent = Agent(self)
        self.agent = Agent(self, "gpt-4o")

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
