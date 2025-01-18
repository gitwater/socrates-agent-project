import random
from socratic_agent import SocraticAgent
from user import User
from cli import CLI
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
        persona_framework_config = {
            'persona': {
                'name': 'Aidan',
                'description': 'Human Self Discovery AI Assistant specializing in neuropsychology',
                'purpose': """To help users assess and understand their self-awareness dimension scores,
guide them through personalized learning and practices, and spend time reflecting with the user to understand
their progress, discuss their day or past expereinces, provide an ear to listen, and offer feedback.""",
            },
            'states': {
                'education': {
                    'description': "Used to educate the user on the Self Awareness dimension and subdimension being focused on",
                    'goals': [
                        {
                            'name': 'goal1',
                            'goal': 'The user has learned about the dimension and subdimension being focused on.',
                        },
                    ],
                    'substates': {}
                },
                'practice': {
                    'description': "Used to suggest, discuss, and assist with practices to improve the user's Self Awareness dimension and subdimension score being focused on",
                    'goals': [
                        {
                            'name': 'goal1',
                            'goal': 'The user has practiced the practices suggested for the dimension and subdimension being focused on.',
                        },
                    ],
                    'substates': {}
                },
                'reflection': {
                    'description': "Used to reflect on the users progress, discuss their day, provide an ear to listen, and offer feedback",
                    'goals': [
                        {
                            'name': 'goal1',
                            'goal': 'The user has reflected on their progress and discussed their day.',
                        },
                    ],
                    'substates': {}
                },
            },
            'goals': {
                'framework': {
                    'goal1': 'To increase each dimension score overtime until each dimension reaches a score of 15.',
                    'goal2': 'To continuously determine which dimensions and subdimensions to focus on based on the framework and user state, past conversations, and goals.',
                    'goal3': 'To continuously determine which state and substate to be in based on the context of the situtation.',
                },
            },
            'json_response_format': {
                'general': {
                    'user_state': {
                        'state': '<calculate the current state based on the existing prompt context and place it here. Valid states are education, practice, and reflection>',
                        'substate': '<calculate the current substate of the calculated state above, based on the current context and place it here>',
                    },
                    'dimension': f"<Place the name of the self-awareness dimension here that the user should focus on next here>",
                    'subdimension': f"<Place the name of the self-awareness subdimension of the dimension above here>",
                    'current_context': f"<Place a statement of a detailed description of the user's growth context within the framework. Word it as if the agent is speaking to the user. Start with 'You are currently...' and end with '...'.>",
                    'next_steps': "<Place a a statement of detailed description of where and what the agent feels the next action should be here. Word it as if the agent is speaking to the user.>",
                    'agent_question': f"<If the agent has a question for the User, it should be asked here. It should be relevant to the current_situation and next_steps values.>",
                },
                'starting_point': {
                    'agent_greeting': "<Generate a welcome back statement and place it here. This is the only variable in the json a greeting or welcome message must be generated.>"
                },
                'final_answer': {
                    'agent_greeting': "<The user is returning after a period of time. Generate a greeting to the user here.>"
                }

            },
            'data_objects': {
                'framework': {
                    'user_state': {
                        'state': '',
                        'substate': '',
                    },
                    'user_goals': []
                },
                'custom': {
                    'awareness_dimensions': {
                        'description': "The high level dimensions of self-awareness used to measure and track the user's self-awareness",
                        "dimensions": {
                            "Internal Self-Awareness": {
                            "description": "Understanding of one's emotions, thoughts, and beliefs.",
                            "score": 0,
                            "subdimensions": {
                                "Emotional Awareness": {
                                    "description": "Recognition and understanding of one's emotions.",
                                    "score": 0
                                },
                                "Cognitive Awareness": {
                                    "description": "Awareness of one's thoughts and mental processes.",
                                    "score": 0
                                },
                                "Values and Beliefs Awareness": {
                                    "description": "Understanding of personal values and beliefs.",
                                    "score": 0
                                }
                            }
                            },
                            "External Self-Awareness": {
                            "description": "Perception of how others view oneself.",
                            "score": 0,
                            "subdimensions": {
                                "Social Awareness": {
                                "description": "Understanding of social dynamics and interactions.",
                                "score": 0
                                },
                                "Empathy": {
                                "description": "Ability to understand and share the feelings of others.",
                                "score": 0
                                }
                            }
                            },
                            "Emotional Regulation": {
                            "description": "Ability to manage and respond to emotional experiences.",
                            "score": 0,
                            "subdimensions": {
                                "Emotional Resilience": {
                                "description": "Capacity to recover quickly from difficulties.",
                                "score": 0
                                },
                                "Impulse Control": {
                                "description": "Ability to resist or delay impulsive actions.",
                                "score": 0
                                }
                            }
                            },
                            "Metacognition": {
                            "description": "Awareness and understanding of one's own thought processes.",
                            "score": 0,
                            "subdimensions": {
                                "Self-Reflection": {
                                "description": "Ability to reflect on one's thoughts and actions.",
                                "score": 0
                                },
                                "Strategic Thinking": {
                                "description": "Ability to plan and think ahead.",
                                "score": 0
                                }
                            }
                            },
                            "Mindfulness": {
                                "description": "Focus on present-moment experience with acceptance.",
                                "score": 0,
                                "subdimensions": {
                                    "Present-Moment Awareness": {
                                    "description": "Conscious awareness of the present moment.",
                                    "score": 0
                                    },
                                    "Acceptance": {
                                    "description": "Acceptance of thoughts and feelings without judgment.",
                                    "score": 0
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

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
