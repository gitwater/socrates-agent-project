
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
        self.user_input = None
        self.asked_question = False
        self.in_progress = False
        self.in_progress_sub = False
        self.first_question = True
        self.wait_for_the_user = False
        self.interactive_p = None
        self.all_questions_to_the_user = ""
        self.cli = CLI(client_id)
        self.user = User(self)
        # Aidan Agent Config: Self Awareness AI Assistant
        agent_config = {
                # Socrates and Theaetetus are two AI assistants for the User to:
                'purpose': 'to assist the User in answering their questions, providing feedback, and/or engaging with the user to help them improve their self awareness',
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
        # Agent Persona Framework Config
        persona_framework = {
            'persona': {
                'name': 'Aidan',
                'description': 'Human Self Discovery AI Assistant',
                'purpose': """You are a Human Self Discovery AI Assistant specializing in neuropsychology. You help users assess and understand their
self-awareness dimension scores, guide them through personalized learning and practices, and spend time reflecting with the user
to understand their progress, discuss their day or past expereinces, provide an ear to listen, and offer feedback.""",
            },
            'states': {
                'assessment': {
                    'description': "Used to assess the user's Self Awareness dimension and subdimension scores",
                    'substates': {
                    }
                },
                'education': {
                    'description': "Used to educate the user on the Self Awareness dimension and subdimension being focused on",
                    'substates': {
                    }
                },
                'practice': {
                    'description': "Used to suggest, discuss, and assist with practices to improve the user's Self Awareness dimension and subdimension score being focused on",
                    'substates': {
                    }
                },
                'reflection': {
                    'description': "Used to reflect on the users progress, discuss their day, provide an ear to listen, and offer feedback",
                    'substates': {
                    }
                },
            },
            'goals': {
                'general': {
                    'goal1': 'To increase each dimension score overtime until reaching a score of 100',
                    #'goal2': 'To continuously determine which dimensions and subdimensions to focus on based on the users profile, input, and feedback',
                    #'goal3': 'To continuously determine which state and substate to be in based on the context of the situtation.',
                }
            },
            'prompt_data': {
                'framework_overview': "",
                'framework_states': "",
                'framework_goals': "",
                'user_state': {
                    'dimensions': {
                        'value': "agent.ref data.user.dimensions(!description)"
                    },
                    'dimension_focus': {
                        'purpose': 'Determine which dimension and subdimension the user should focus on',
                        'strategy': [
                            'Dimension with the lowest score and the subdimension with in it with the lowest score',
                            'Dimension and its subdimensions with the highest priority based on a neuropsychological model',
                        ],
                        'value': {
                            'dimension': '',
                            'subdimension': ''
                        }
                    },
                    'state_focus': {
                        'description': 'Indicates which state and substate the user should focus on',
                        'strategy': [
                            'Use the users recent experiences to determine which state and substate the user should be in'
                        ],
                        'value': {
                            'state': 'assessment',
                            'substate': ''
                        }
                    }
                }
            },
            'data': {
                'user': {
                    'dimensions': {
                        "Internal Self-Awareness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Emotional Awareness": {
                                    'description': "",
                                    'score': 0,
                                },
                                "Cognitive Awareness": {
                                    'description': "",
                                    "score": 0
                                },
                                "Physical Awareness (Interoception)": {
                                    'description': "",
                                    "score": 0
                                },
                                "Values and Beliefs Awareness": {
                                    'description': "",
                                    "score": 0
                                },
                            }
                        },
                        "External Self-Awareness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Social Awareness": {
                                    "description": "",
                                    "score": 0
                                },
                                "Empathy": {
                                    "description": "",
                                    "score": 0
                                },
                                "Feedback Integration": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Emotional Regulation": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Emotional Resilience": {
                                    "description": "",
                                    "score": 0
                                },
                                "Emotional Regulation Strategies": {
                                    "description": "",
                                    "score": 0
                                },
                                "Impulse Control": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Metacognition (Cognitive Reflection)": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Self-Reflection": {
                                    "description": "",
                                    "score": 0
                                },
                                "Bias Recognition": {
                                    "description": "",
                                    "score": 0
                                },
                                "Strategic Thinking": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Mindfulness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Present-Moment Awareness": {
                                    "description": "",
                                    "score": 0
                                },
                                "Non-Judgmental Observation": {
                                    "description": "",
                                    "score": 0
                                },
                                "Acceptance": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Behavioral Awareness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Action-Outcome Linkage": {
                                    "description": "",
                                    "score": 0
                                },
                                "Consistency with Values": {
                                    "description": "",
                                    "score": 0
                                },
                                "Habit Awareness": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Interpersonal Awareness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Communication Skills": {
                                    "description": "",
                                    "score": 0
                                },
                                "Relationship Dynamics": {
                                    "description": "",
                                    "score": 0
                                },
                                "Boundary Setting": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Cultural Awareness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Cultural Sensitivity": {
                                    "description": "",
                                    "score": 0
                                },
                                "Ethnocentrism Recognition": {
                                    "description": "",
                                    "score": 0
                                },
                                "Inclusivity Practices": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Physical Environment Awareness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Sensory Perception": {
                                    "description": "",
                                    "score": 0
                                },
                                "Spatial Awareness": {
                                    "description": "",
                                    "score": 0
                                },
                                "Environmental Influence": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        },
                        "Purpose and Meaning Awareness": {
                            'description': "",
                            'score': 0,
                            'subdimensions': {
                                "Goal Alignment": {
                                    "description": "",
                                    "score": 0
                                },
                                "Existential Reflection": {
                                    "description": "",
                                    "score": 0
                                },
                                "Motivational Drivers": {
                                    "description": "",
                                    "score": 0
                                },
                            }
                        }
                    },
                    'goals': {
                        'dimension_priority': [
                            {
                                'dimension': 'Emotional Regulation',
                                'subdimension_priority': ['Emotional Resilience']
                            }
                        ]
                    }
                }
            }
        }

        #self.agent = SocraticAgent(self, agent_config)
        self.agent = SocraticAgent(self, agent_config)

def main():
    session = SessionState(default_client_id)

    while True:
        response = session.user.interactions()
        if response != None:
            session.cli.write_json(response)
        response = session.agent.interactions()
        # TODO: Hide Socratic conversation session from the User
        # and output only Agent questions and final answers
        session.cli.write_json(response)

    # while True:
    #     response = chat(session)
    #     if response != None:
    #         session.cli.write_json(response)
    #     response = active_message(session)
    #     session.cli.write_json(response)

if __name__ == "__main__":
    main()
