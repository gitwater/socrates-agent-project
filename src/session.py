import random
from socratic_agent import SocraticAgent
from user import User
from cli import CLI
import persona_configs
from pprint import pprint


class SessionState:
    def __init__(self, client_id):
        self.client_id = client_id
        self.dialog_lead = None
        self.dialog_follower = None
        self.user_input = None
        self.asked_question = False
        self.in_progress = False
        self.in_progress_sub = False
        self.first_question = True
        self.wait_for_the_user = False
        self.interactive_p = None
        self.all_questions_to_the_user = ""
        #self.cli = CLI(client_id)
        #self.user = User(self)
        self.agent_msgs = []
        self.agent_dialog_msgs = []
        # Init will assess the current state of the User to decide where to start
        self.init_complete = False
        # Aidan Agent Config: Self Awareness AI Assistant
        # Agent Persona Framework Config
        #persona = "aidan"
        #persona = "luca"
        persona = "sage"
        #persona = "sage"

        if persona == "sage":
            persona_framework_config = persona_configs.social_interaction_assistant_config
        elif persona == "aria":
            persona_framework_config = persona_configs.agent_engineering_config
        elif persona == "luca":
            persona_framework_config = persona_configs.language_assistant_config
        elif persona == "aidan":
            persona_framework_config = persona_configs.self_awareness_config
            # Populate scores with fake data for now
            for dimension_key in persona_framework_config['data_objects']['custom']['awareness_dimensions']['dimensions']:
                dimension = persona_framework_config['data_objects']['custom']['awareness_dimensions']['dimensions'][dimension_key]
                # Randomize the score between 1-5
                total = 0
                for subdimension_key in dimension['subdimensions']:
                    subdimension = dimension['subdimensions'][subdimension_key]
                    subdimension['score'] = random.randint(1, 5)
                    total += subdimension['score']
                dimension['score'] = total


        #self.agent = SocraticAgent(self, agent_config)
        self.agent = SocraticAgent(self, persona_framework_config)

    def send_user_message(self, message):
        agent_msg = {'role': 'Agent', 'response': message}
        self.agent_msgs.append(agent_msg)

    def pop_user_messages(self):
        messages = self.agent_msgs
        self.agent_msgs = []
        return messages

    def send_agent_dialog_message(self, agent_role, message):
        agent_msg = {'role': 'debug-agent', 'response': f"{agent_role}: {message}"}
        self.agent_dialog_msgs.append(agent_msg)

    def pop_agent_dialog_messages(self):
        messages = self.agent_dialog_msgs
        self.agent_dialog_msgs = []
        return messages
