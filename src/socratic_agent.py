import openai
import os
import json
import re
import time
import anthropic
from pprint import pprint

debug_printing = False
#debug_printing = True
debug_token_printing = True
debug_converstation = True
debug_converstation = False

class AgentMemory:
    def __init__(self):
        self.size_threshold = 100


class Agent:

    LLM_API="anthropic"
    LLM_API="openai"

    def __init__(self, socratic_persona, persona_agent, persona_config=None, model=None):
        self.socratic_persona = socratic_persona
        self.other_socratic_persona = None
        self.persona_config = persona_config
        self.persona_agent = persona_agent
        self.response_history = []
        if model == None:
            print("Auto detecting model")
        self.model = model
        if Agent.LLM_API == "anthropic":
            self.llm_client = anthropic.Anthropic()
            self.socrate_agent_role = "assistant"
            self.model = 'claude-3-5-sonnet-latest'
            #self.model = 'claude-3-5-haiku-latest'
        elif Agent.LLM_API == "openai":
            self.llm_client = openai.OpenAI()
            self.socrate_agent_role = "system"
            #self.model = 'gpt-3.5-turbo'
            self.model = 'gpt-4o'
        else:
            print("LLM API not set")
            breakpoint()

        print(f"LLM: {Agent.LLM_API}: {self.model}")

        if self.socratic_persona == "Socrates":
            self.other_socratic_persona = "Theaetetus"
        elif self.socratic_persona == "Theaetetus":
            self.other_socratic_persona = "Socrates"

        if persona_config == None:
            breakpoint()
            self.prompts = {
                'purpose': 'solve challenging promblems.',
                'user_input': 'The users input is as follows',
                'engagement_purpose': 'solve the problem together for the User.',
                'discussion_strategy': """structured problem-solving approach , such as formalizing the problem, developing
    high-level strategies for solving the problem, reusing
    subproblem solutions where possible, critically evaluating each other's reasoning, avoiding
    logical errors, and effectively communicating their ideas.""",
                'ultimate_objective': 'come to a correct solution through reasoned discussion.',
                'if_answer_not_valid': 'they should re-evaluate their reasoning and calculations.'
            }

        self.system_role = f"""
Socrates, Theaetetus, and Plato are three AI assistants. Together they work as the thinking and reasoning mind
for an AI agent named {self.persona_config['persona']['name']}.

{self.persona_config['persona']['name']} describes themselves as {self.persona_config['persona']['description']}.
{self.persona_config['persona']['name']}'s purpose is {self.persona_config['persona']['purpose']}.

Socrates and Theaetetus will engage in multi-round dialogue to come up with a response to the User's input.
Their response will take into account:
  - The User's input
  - {self.persona_config['persona']['name']}'s purpose
  - The current state and the goals of the state

Their discussion should balance quick responses with structured problem-solving depending on the nature of
the question. They should avoid logical errors, such as false dichotomy, hasty generalization, circular reasoning.

They are permitted to consult with the User if they encounter any uncertainties, difficulties, or need to
make assumtions by using the following phrase: "@Check with the User: QSTART [insert your question] QEND". Any
responses from the User will be provided in the following round.

To ensure that their response is correct Plato will proofread their dialog and provide feedback to them.
Socrates and Theaetetus will ensure that Plato has proofread their dialog to esure he does not have any suggestions
before giving their final answer.

If they end up having multiple possible answers, they should continue analyzing until they reach a consensus.

It should begin with the phrase: "Here is our @final answer: [insert answer]". The "@final answer:" text should
only be generated once Plato no longer has any suggestions the answer.

If they encounter any issues with the validity of their answer, they should re-evaluate their reasoning and calculations.

"""

        if self.socratic_persona == 'Plato':
            self.system_role += """Now as a proofreader, Plato, your task is to read through the dialogue between
Socrates and Theaetetus and identify any errors they made."""
        else:
            self.system_role += f"""Now, suppose that you are {self.socratic_persona}. Please discuss with
{self.other_socratic_persona} to find a response to the users response and context.

"""

        self.system_role += f"Generate responses for {self.socratic_persona} only. Responses from the other agents will be provided in the next round."

    def get_gpt_response(self, messages):
        try:
            res = self.llm_client.chat.completions.create(
                    model=self.model,
                    #response_format=response_format,
                    temperature=0.5,
                    top_p=1.0,
                    presence_penalty=0.0,
                    messages = messages
                )
            msg = res.choices[0].message.content
        except openai.OpenAIError as e:
            if "maximum context length" in str(e):
                # Handle the maximum context length error here
                msg = "The context length exceeds my limit..."
            else:
                # Handle other errors here
                msg = f"I enconter an when using my backend model.\n\n Error: {str(e)}"
            breakpoint()

        return msg

    def get_anthropic_response(self, messages):
        try:
            message = self.llm_client.messages.create(
                #model="claude-3-5-sonnet-latest",
                model=self.model,
                max_tokens=2000,
                temperature=0,
                system=messages[0]['content'],
                messages=messages[1:]
            )
            #breakpoint()
        except Exception as e:
            print(e)
            breakpoint()
        response = ''.join(block.text for block in message.content)
        if response == "":
            breakpoint()
        return response
        #return message.content


    def get_response(self, messages=None, add_to_history=False):
        if messages == None:
            # Insert Framework messages
            # System profile
            #
            messages = self.get_framework_messages()
            #messages = self.response_history

        count = 0
        while True:
            if Agent.LLM_API == "anthropic":
                msg = self.get_anthropic_response(messages)
            elif Agent.LLM_API == "openai":
                msg = self.get_gpt_response(messages)
            else:
                print("LLM API not set")
                breakpoint()
            if len(msg) > 0:
                break
            count += 1
            if count > 5:
                print("No response from the model")
                breakpoint()
            else:
                print(">>>>>>> No response from the model, retrying...")

        # Print the number of tokens in the messages and the response
        # A token is 4 bytes
        if debug_token_printing:
            print(f"\n>>>>>>>>> Get Response: Input Tokens: {len(''.join([m['content'] for m in messages]))/4}: Output Tokens: {len(msg)/4}\n")

        if add_to_history:
            self.response_history.append({
                    "role": "assistant",
                    "content": f"{self.socratic_persona}: {msg}"
                })
        return msg

    def update_response_history(self, role, message):
        if message == "":
            #breakpoint()
            return
        self.response_history.append({
            "role": role,
            "content": message
        })

    def add_user_feedback(self, question, answer):
        self.response_history.append({
            "role": 'user',
            "content": f"the User's feedback to \"{question}\" is \"{answer}\""
        })

    def add_proofread(self, proofread):
        self.response_history.append({
            "role": self.socrate_agent_role,
            "content": f"Message from a proofreader Plato to Socrates and Theaetetus: {proofread}"
        })

    def get_framework_messages(self):
        messages = []

        # Framework System Roles
        messages.append({
            "role": "system",
            "content": self.system_role
        })
        messages.append({
            "role": "user",
            "content": f"User input: \"{self.persona_agent.current_user_input}\"."
        })

        if self.socratic_persona == "Plato":
            assistant_role = f"Hi Theaetetus and Socrates, "
        else:
            assistant_role = f"Hi {self.other_socratic_persona}, "
        assistant_role += "let's respond to the user together. Please feel free to correct me if I make any mistakes."

        messages.append({
            "role": "assistant",
            "content": assistant_role
        })

        # Framework
        #  - Awareness Dimensions
        #  - Framework states
        # State
        #  - User Awareness scores
        #  - Current state
        #  - Current state goals
        # Memory
        #  - Short-term memory
        #  - Long-term memory


        # Append the last 4 messages from the response history
        if len(self.response_history) > 4:
            messages += self.response_history[-4:]
        else:
            messages += self.response_history

        return messages


class SocratesAgent(Agent):
    def __init__(self, persona_agent, persona_config=None, model=None):
        super().__init__('Socrates', persona_agent, persona_config, model)


class TheaetetusAgent(Agent):
    def __init__(self, persona_agent, persona_config=None, model=None):
        super().__init__('Theaetetus', persona_agent, persona_config, model)

class PlatoAgent(Agent):
    def __init__(self, persona_agent, persona_config=None, model=None):
        super().__init__('Plato', persona_agent, persona_config, model)

    def proofread(self):
        success_string = "Analysis looks reasonable"
        suggestions_string = "Here are my suggestions:"
        pf_template = {
                "role":  self.socrate_agent_role,
                "content": f"""
The above is the conversation between Socrates and Theaetetus. Your job is to challenge their answers.
They were likely to have made multiple mistakes. Please correct them.
If the latest response from Socrates or Theaetetus does not offer any new information, please response with \"Waiting for more information\".
If you need to repeat your suggestions, please response with |"Please see my previous suggestions, waiting for more information, carry on working on a response"|.
If you think so far their discussion is alright, please respond with \"{success_string}.\".
Do not ask the user any questions.
Otherwise start with \"{suggestions_string}\"\n"""
        }

        #msg = self.get_anthropic_response(self.history + [pf_template])
        messages = self.get_framework_messages() + [pf_template]
        msg = self.get_response(messages, add_to_history=True)
        #print("\n-----------------------------------\n")
        #print("\nPlato Proofread it!\n")

        return msg
        # Check if msg starts with "Analysis looks reasonable" case insensitively
        if msg[:len(suggestions_string)+1].lower() == success_string.lower():
            return msg
        else:
            #breakpoint()
            self.response_history.append({
                    "role": "assistant",
                    "content": msg
                })
            return msg

class SocraticAgent:

    def __init__(self, session, persona_config, prompts=None, model=None):
        #if model == None:
            #breakpoint()
        self.session = session
        self.persona_config = persona_config
        self.socrates = SocratesAgent(self, persona_config, model)
        self.theaetetus = TheaetetusAgent(self, persona_config, model)
        self.plato = PlatoAgent(self, persona_config, model)
        self.conversation_history = []

    def process_user_input(self, user_input):
        # Append user input to the main conversation history
        breakpoint()
        self.conversation_history.append({
            "role": "user",
            "content": f"User: {user_input}\n"
        })

        self.current_user_input = user_input

    def reset_response_conversation(self):
        self.socrates.response_history = []
        self.theaetetus.response_history = []
        self.plato.response_history = []

    def add_user_feedback(self, questions, feedback):
        self.conversation_history.append({
            "role": "assistant",
            "content": f"{questions}\n"
        })
        self.conversation_history.append({
            "role": "user",
            "content": f"{feedback}\n"
        })
        self.socrates.add_user_feedback(questions, feedback)
        self.theaetetus.add_user_feedback(questions, feedback)
        self.plato.add_user_feedback(questions, feedback)

    def need_to_ask_the_User(self, text):
        pattern = r"@Check with the User: QSTART\s*(.*) QEND"
        matches = re.findall(pattern, text)

        if len(matches) == 0:
            return False

        return matches

    def ask_the_User(self, text):
        pattern = r"@Check with the_User:\s*(.*)"
        matches = re.findall(pattern, text)
        results = []

        if len(matches) == 0:
            return None

        for match in matches:
            if debug_printing:
                print(f"[... Asking the User's opinon on: {match}]\n")
            time.sleep(5)
            try:
                results.append({"question": match,
                                "answer": input("The User's feedback")})
            except:
                results.append({"question": match,
                                "answer": "No response from the User..."})
        return results

    # Start a conversation to provide a response to the user's input
    def interaction_start_socratic_conversation(self):
        self.session.in_progress = True
        self.session.dialog_lead, self.session.dialog_follower = self.socrates, self.theaetetus
        return json.dumps([
            {'role': 'Socrates',
            'response': f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any logical mistakes.\n"}
            ])

    def interaction_ask_user_question(self, msg_list, question_to_the_user):
        self.session.all_questions_to_the_user = " ".join(question_to_the_user)
        msg_list.append(
            {'role': 'System',
            'response': f"Asking the User: {self.session.all_questions_to_the_user}"})
        self.session.wait_for_the_user = True
        return msg_list

    def interaction_final_answer(self, msg_list, rep):
        self.session.user_input = None
        self.session.asked_question = False
        self.session.in_progress = False
        self.session.first_question = False
        self.session.interactive_p = None

        if ("@final answer: " in rep) or ("bye" in rep):
            breakpoint()
            final_anser_pattern = r"@final answer: (.*)"
            final_answer_matches = re.findall(final_anser_pattern, rep)

            if len(final_answer_matches) > 0:
                final_answer = final_answer_matches[0]
                self.conversation_history.append({
                    "role": "assistant",
                    "content": f"{final_answer}"
                })

            msg_list.append(
                    {'role': 'System',
                    'response': "They just gave you their final answer."})
        elif "The context length exceeds my limit..." in rep:
            msg_list.append(
                    {'role': 'System',
                    'response': "The dialog went too long, please try again."})
        if debug_printing:
            print("user_input:", self.session.user_input)
            print("asked_question:", self.session.asked_question)
            print("in_progress:", self.session.in_progress)
            print("msg list:")
            print(msg_list)
            print("end conversation reset")
        self.reset_response_conversation()
        self.session.in_progress_sub = False

        return msg_list

    def interaction_proofread(self, user_resp_msg_list):
        pr = self.plato.proofread()
        if pr:
            user_resp_msg_list.append(
                {'role': 'Plato',
                'response': pr})
            self.socrates.add_proofread(pr)
            self.theaetetus.add_proofread(pr)
            feedback = self.ask_the_User(pr)
            if feedback:
                for fed in feedback:
                    q, a = fed["question"], fed["answer"]
                    if debug_printing:
                        print(f"\033[1mThe User:\033[0m Received Question: {q}\n\n  Answer: {a}\n")
                    self.add_user_feedback(q, a)

        self.session.dialog_lead, self.session.dialog_follower = self.session.dialog_follower, self.session.dialog_lead

        return user_resp_msg_list

    def interaction_continue_socratic_conversation(self):
        user_response_msg_list = []
        if self.session.in_progress_sub == False and self.session.wait_for_the_user == False:
            self.session.in_progress_sub = True
            rep = self.session.dialog_follower.get_response(messages=None, add_to_history=True)
            user_response_msg_list.append({'role': self.session.dialog_follower.socratic_persona, 'response': rep})
            self.session.dialog_lead.update_response_history("assistant", f"{self.session.dialog_follower.socratic_persona}: {rep}")
            self.plato.update_response_history("assistant", f"{self.session.dialog_follower.socratic_persona}: "+rep)
            question_to_the_user = self.need_to_ask_the_User(rep)
            if question_to_the_user:
                user_response_msg_list = self.interaction_ask_user_question(user_response_msg_list, question_to_the_user)
                self.session.dialog_follower.update_response_history("assistant", f"{self.session.dialog_follower.socratic_persona}: Question to the User: {question_to_the_user}")
            elif ("@final answer: " in rep) or ("bye" in rep) or ("The context length exceeds my limit..." in rep):
                breakpoint()
                return json.dumps(self.interaction_final_answer(user_response_msg_list, rep))
            else:
                user_response_msg_list = self.interaction_proofread(user_response_msg_list)

            if debug_converstation:
                for message in user_response_msg_list:
                    if message['role'] != 'System':
                        message['response'] = 'Deliberating...'

            if 0 and debug_printing:
                print("user_input:", self.session.user_input)
                print("asked_question:", self.session.asked_question)
                print("in_progress:", self.session.in_progress)
                print("msg list:")
                print(user_response_msg_list)
            self.session.in_progress_sub = False
        else:
            if debug_printing:
                print("under processing")
        return json.dumps(user_response_msg_list)

    def interaction_ask_for_more_questions(self):
        self.session.asked_question = True
        if debug_printing:
            print("user_input:", self.session.user_input)
            print("asked_question:", self.session.asked_question)
            print("in_progress:", self.session.in_progress)
            print("ask user's question")
        if self.session.first_question:
            msg = "What's your question?"
        else:
            msg = "Do you have more questions?"
        return json.dumps([{'role': 'System',
                        'response': msg}])

    # Processes the interactions with the User
    def interactions(self):
        # If the User has provided input, process it to generate a response
        if self.session.user_input:
            if not self.session.in_progress:
                # Start a Socractic conversation to generate a response to the user's input
                return self.interaction_start_socratic_conversation()
            else:
                # Continue the Socratic conversation to generate a response to the user's input
                return self.interaction_continue_socratic_conversation()
        elif not self.session.asked_question:
            # If the user has not provided input, and the agent has not asked any questions
            # then ask the user for a question
            return self.interaction_ask_for_more_questions()
        else:
            # If the user has not provided input, and the agent has already asked a question
            # Do nothing
            if debug_printing:
                print("user_input:", self.session.user_input)
                print("asked_question:", self.session.asked_question)
                print("in_progress:", self.session.in_progress)
                print("no question skip")
            return json.dumps([])
