
from socratic_agent import SocraticAgent
from user import User
from cli import CLI
import random
from pprint import pprint

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
                'assessment': {
                    'description': "Used to assess the user's Self Awareness dimension and subdimension scores",
                    'goals': [
                        {
                            'name': 'goal1',
                            'goal': 'The user has evaluated a score for all dimensions and subdimensions',
                        },
                        {
                            'name': 'goal2',
                            'goal': 'The user has set one to three goals for how they would like to proceed with their self-awareness journey',
                        },
                    ],
                    'substates': {
                        'score_evaluation': {
                            'description': "Used to evaluate the user's Self Awareness dimension and subdimension scores.",
                            #'modules': "",
                            'goals': [
                                {
                                    'name': 'goal1',
                                    'goal': 'Ensure the user has a non-zero score in any dimension or subdimension by switching to this state and substate.',
                                },
                            ]
                        },
                        # Goal Setting
                        # 1. Dimension and Subdimension to focus on
                        # 2. Set a score goal for the dimension and subdimension
                        # 3. Set a time goal for the dimension and subdimension
                        # 4. Set an education goal for the dimension and subdimension
                        #    4.1 Set an amount of time spent in education goal for the dimension and subdimension
                        # 5. Set a practice goal for the dimension and subdimension
                        #    5.1 Determine one to three practices to focus on for the dimension and subdimension
                        #    5.2 Set an amount of time spent in practice goal for each practice
                        'goal_setting': {
                            'description': "Used to set goals for the user's Self Awareness dimension and subdimension scores",
                            'goals': [
                                {
                                    'name': 'goal1',
                                    'goal': 'If the user has not set ant goals, switch to this state and substate to set goals.',
                                },
                            ]
                        },
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
                'framework': {
                    'goal1': 'To increase each dimension score overtime until each dimension reaches a score of 15.',
                    'goal2': 'To continuously determine which dimensions and subdimensions to focus on based on the framework and user state, past conversations, and goals.',
                    'goal3': 'To continuously determine which state and substate to be in based on the context of the situtation.',
                },
            },
            'json_response_format': {
                'user_state': {
                    'state': '<calculate the current state based on the current context and place it here>',
                    'substate': '<calculate the current substate of the calculated state above, based on the current context and place it here>',
                },
                'dimension': f"<Place the name of the self-awareness dimension here that the user should focus on next here>",
                'subdimension': f"<Place the name of the self-awareness subdimension of the dimension above here>",
                'current_situation': f"<Place a description of the current situation here>",
                'next_steps': "<Place a description of where and what the agent feels the next action should be here>",
                'agent_question': f"<If the agent has a question for the User, it should be asked here>",
            },
            'data_objects': {
                'framework': {
                    'user_state': {
                        'state': '',
                        'substate': '',
                    },
                    'user_goals': [
                    ]
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
                        # 'dimensions': {
                        #     "Internal Self-Awareness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Emotional Awareness": {
                        #                 'description': "",
                        #                 'score': 0,
                        #             },
                        #             "Cognitive Awareness": {
                        #                 'description': "",
                        #                 "score": 0
                        #             },
                        #             "Physical Awareness (Interoception)": {
                        #                 'description': "",
                        #                 "score": 0
                        #             },
                        #             "Values and Beliefs Awareness": {
                        #                 'description': "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "External Self-Awareness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Social Awareness": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Empathy": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Feedback Integration": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Emotional Regulation": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Emotional Resilience": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Emotional Regulation Strategies": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Impulse Control": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Metacognition (Cognitive Reflection)": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Self-Reflection": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Bias Recognition": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Strategic Thinking": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Mindfulness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Present-Moment Awareness": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Non-Judgmental Observation": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Acceptance": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Behavioral Awareness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Action-Outcome Linkage": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Consistency with Values": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Habit Awareness": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Interpersonal Awareness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Communication Skills": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Relationship Dynamics": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Boundary Setting": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Cultural Awareness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Cultural Sensitivity": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Ethnocentrism Recognition": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Inclusivity Practices": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Physical Environment Awareness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Sensory Perception": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Spatial Awareness": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Environmental Influence": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     },
                        #     "Purpose and Meaning Awareness": {
                        #         'description': "",
                        #         'score': 0,
                        #         'subdimensions': {
                        #             "Goal Alignment": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Existential Reflection": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #             "Motivational Drivers": {
                        #                 "description": "",
                        #                 "score": 0
                        #             },
                        #         }
                        #     }
                        # }
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

        # TODO:
        #   - Next step is to work with json resposnes
        #   - Store state on disk for reuse
        #   - On Final Answer, process the answer to make choices on what to do next with JSON response
        #   - Introduce logic to analyze the json response to detect state changes to guide users
        #   - If user doesn't want to follow then stick to the current state for a while then reasses
        #   - Find a way to set some user goals (if needed)
        #   - Find a way to take a quiz to get initial scores

        #self.agent = SocraticAgent(self, agent_config)
        self.agent = SocraticAgent(self, persona_framework_config)

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
