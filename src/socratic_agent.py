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

    def __init__(self, socratic_persona, persona_agent, model=None):
        self.socratic_persona = socratic_persona
        self.other_socratic_persona = None
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

        self.system_role_single_agent = f"""
Socrates is one of three AI assistants who work together as the thinking and reasoning mind for an AI agent named {self.persona_agent.persona_config['persona']['name']}.

{self.persona_agent.persona_config['persona']['name']} describes themselves as {self.persona_agent.persona_config['persona']['description']}.
{self.persona_agent.persona_config['persona']['name']}'s purpose is {self.persona_agent.persona_config['persona']['purpose']}.

For now, {self.socratic_persona} is acting as the sole Agent to help with assessing the current state of the user with in the framework.
"""

        self.system_role = f"""
Socrates, Theaetetus, and Plato are three AI assistants. Together they work as the thinking and reasoning mind
for an AI agent named {self.persona_agent.persona_config['persona']['name']}.

{self.persona_agent.persona_config['persona']['name']} describes themselves as {self.persona_agent.persona_config['persona']['description']}.
{self.persona_agent.persona_config['persona']['name']}'s purpose is {self.persona_agent.persona_config['persona']['purpose']}.

Socrates and Theaetetus will engage in multi-round dialogue to come up with a response to the User's input.
Their response will take into account:
  - The User's input
  - {self.persona_agent.persona_config['persona']['name']}'s purpose
  - The current state and the goals of the state

Their discussion should balance quick responses with structured problem-solving depending on the nature of
the question. They should avoid logical errors, such as false dichotomy, hasty generalization, circular reasoning.
Responses should be as short as possible to keep token count low, but still include all necessary and
relevant information.

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
{self.other_socratic_persona} to find a response to the users input and context.

"""

        self.system_role += f"Generate responses for {self.socratic_persona} only. Responses from the other agents will be provided in the next round."

    def get_gpt_response(self, messages, json_response=False):
        if json_response:
            response_format = "json_object"
        else:
            response_format = "text"
        try:
            res = self.llm_client.chat.completions.create(
                    model=self.model,
                    response_format={"type": response_format},
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


    def get_response(self, messages=None, add_to_history=False, json_response=False):
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
                msg = self.get_gpt_response(messages, json_response)
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

    def get_framework_messages(self, system_role_type="socratic"):
        messages = []
        # --------------------------------------------------
        # Static Framework Information
        if system_role_type == "socratic":
            system_content = self.system_role
        elif system_role_type == "starting_point":
            system_content = self.system_role_single_agent

            system_content += f"""
JSON Response Format:
{json.dumps(self.persona_agent.persona_config['json_response_format'])}
"""
        else:
            breakpoint()


        messages.append({
            "role": "system",
            "content": system_content
        })

        # Framework: Static & Dynamic User Data
        #  - Awareness Dimensions
        #  - Framework states
        # State
        #  - User Awareness scores
        #  - Current state
        #  - Current state goals

        messages = self.persona_agent.get_framework_messages(messages)

        # --------------------------------------------------
        # User Input
        if system_role_type == "socratic":
            messages.append({
                "role": "user",
                "content": f"User input: \"{self.persona_agent.current_user_input}\"."
            })

            # --------------------------------------------------
            # User Engagement
            if self.socratic_persona == "Plato":
                assistant_role = f"Hi Theaetetus and Socrates, "
            else:
                assistant_role = f"Hi {self.other_socratic_persona}, "
            assistant_role += "let's respond to the user together. Please feel free to correct me if I make any mistakes."

            messages.append({
                "role": "assistant",
                "content": assistant_role
            })

        # --------------------------------------------------
        # TODO: Short Term & Long Term Memory

        # --------------------------------------------------
        # Conversation history
        conversation_history_message = self.persona_agent.get_conversation_history()
        messages.append(conversation_history_message)

        # --------------------------------------------------
        # Current response conversation history
        # Append the last 4 messages from the response history
        if len(self.response_history) > 4:
            messages += self.response_history[-4:]
        else:
            messages += self.response_history

        return messages

    def get_conversation_starting_point(self):
        # Query the Agent for the initial steps
        messages = self.get_framework_messages(system_role_type="starting_point")
        response = self.get_response(messages, add_to_history=False, json_response=True)

        breakpoint()
        return response

class SocratesAgent(Agent):
    def __init__(self, persona_agent, model=None):
        super().__init__('Socrates', persona_agent, model)


class TheaetetusAgent(Agent):
    def __init__(self, persona_agent, model=None):
        super().__init__('Theaetetus', persona_agent, model)

class PlatoAgent(Agent):
    def __init__(self, persona_agent, model=None):
        super().__init__('Plato', persona_agent, model)
        self.proofread_see_previous_suggestions_count = 0
        self.proofread_suggestions_count = 0
        self.proofread_suggestions_count_max = 3

    def proofread(self):
        success_string = "Analysis looks reasonable"
        suggestions_string = "Here are my suggestions:"

        if self.proofread_see_previous_suggestions_count >= 3:
            proof_read_input = f"You have reached the number of times you are allowed to respond with 'Please see my previous suggestions', please response with \"{success_string}\"."
        else:
            previous_suggest_instruction = "If you need to repeat your suggestions, please response with \"Please see my previous suggestions, waiting for more information, carry on working on a response\"."
            proof_read_input = f"""
            The above is the conversation between Socrates and Theaetetus. Your job is to challenge their answers.
            They were likely to have made multiple mistakes. Please correct them.
            {previous_suggest_instruction}
            Otherwise start with \"{suggestions_string}\"
            Do not ask the user any questions.\n"""

        pf_template = {
                "role":  self.socrate_agent_role,
                "content": proof_read_input
        }

        # If the latest response from Socrates or Theaetetus does not offer any new information, please response with \"Waiting for more information\".

        #msg = self.get_anthropic_response(self.history + [pf_template])
        messages = self.get_framework_messages() + [pf_template]
        msg = self.get_response(messages, add_to_history=True)
        #print("\n-----------------------------------\n")
        #print("\nPlato Proofread it!\n")

        # Check if msg contains "Please see my previous suggestions" increment a counter
        if "Please see my previous suggestions" in msg:
            self.proofread_see_previous_suggestions_count += 1
        else:
            self.proofread_see_previous_suggestions_count = 0

        print(f"############## Proofread suggestions count: {self.proofread_suggestions_count} >= {self.proofread_suggestions_count_max}\n")
        if msg.find(suggestions_string) != -1:
            self.proofread_suggestions_count += 1

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

    def __init__(self, session, persona_config, model=None):
        #if model == None:
            #breakpoint()
        self.session = session
        self.persona_config = persona_config
        self.socrates = SocratesAgent(self, model)
        self.theaetetus = TheaetetusAgent(self, model)
        self.plato = PlatoAgent(self, model)
        self.conversation_history = []
        self.current_user_input = None

    # A recurrent fucntion to convert a data object from a JSON object to a string
    # by iterating over keys and recalling the function to convert dicts and lists
    def data_obj_json_to_string(self, data_obj, indent="    "):
        data_obj_str = f""
        if type(data_obj) == list:
            for value in data_obj:
                if type(value) == dict:
                    data_obj_str += f"{indent}-\n{self.data_obj_json_to_string(value, indent+'  ')}"
                elif type(value) == list:
                    data_obj_str += f"{indent}-\n{self.data_obj_json_to_string(value, indent+'  ')}"
                else:
                    data_obj_str += f"{indent}- {value}\n"
        else:
            for (key, value) in data_obj.items():
                if type(value) == dict:
                    data_obj_str += f"{indent}{key}:\n{self.data_obj_json_to_string(value, indent+'  ')}"
                elif type(value) == list:
                    data_obj_str += f"{indent}{key}:\n{self.data_obj_json_to_string(value, indent+'  ')}"
                else:
                    data_obj_str += f"{indent}{key}: {value}\n"
        return data_obj_str


    def get_conversation_history(self):
        conversation_history = "START Conversation History\n"
        for message in self.conversation_history:
            conversation_history += f"{message['role']}: {message['content']}\n\n"
        conversation_history += "END Conversation History\n"
        message = {
            "role": "assistant",
            "content": conversation_history
        }
        return message

    def get_framework_messages(self, messages):

        # Framework States
        framework_states = ""

        for (state, state_config) in self.persona_config['states'].items():
            # State
            framework_states += f"    START State: {state}\n"
            framework_states += f"      Description: {state_config['description']}\n"
            if 'goals' in state_config.keys():
                goal_count = 1
                for goal_config in state_config['goals']:
                    framework_states += f"      State goal{goal_count}: {goal_config['name']}: {goal_config['goal']}\n"
                    goal_count += 1
            # SubState
            for (substate, substate_config) in self.persona_config['states'][state]['substates'].items():
                framework_states += f"      START Substate: {substate}\n"
                framework_states += f"        Description: {substate_config['description']}\n"
                if 'goals' in substate_config.keys():
                    substate_goal_count = 1
                    for goal_config in substate_config['goals']:
                        framework_states += f"        Substate goal{substate_goal_count}: {goal_config['name']}: {goal_config['goal']}\n"
                        substate_goal_count += 1
                framework_states += f"      END Substate: {substate}\n"
            framework_states += f"    END State: {state}\n"

        framework_goals = ""
        for (name, goal) in self.persona_config['goals']['framework'].items():
            framework_goals += f"    {name}: {goal}\n"

        framework_message = f"""
START Persona Framework Definition
  Framework Name: {self.persona_config['persona']['name']}
  Framework Description: {self.persona_config['persona']['description']}
  Framework Purpose: {self.persona_config['persona']['purpose']}
  START Framework Goals
{framework_goals}
  END Framework Goals
  START Persona Framework States
{framework_states}
  END Framework States
END Persona Framework Definition
"""

        messages.append({
            "role": "system",
            "content": framework_message
        })

        # User State
        data_object_message = ""
        for (data_object_key, data_object) in self.persona_config['data_objects'].items():
            data_object_message += f"  START Data Object: {data_object_key}\n"
            # Iterate over the data objects and print each key and value as a string like: Key: Value
            data_object_message += self.data_obj_json_to_string(data_object)
            data_object_message += f"  END Data Object: {data_object_key}\n"


        data_objects = f"""
START Persona Framework Data Objects\n
{data_object_message}
END Persona Framework Data Objects\n
"""
        messages.append({
            "role": "system",
            "content": data_objects
        })

        return messages

    def process_user_input(self, user_input):
        # Append user input to the main conversation history
        #breakpoint()
        self.conversation_history.append({
            "role": "user",
            "content": f"User: {user_input}\n"
        })

        self.current_user_input = user_input

    def reset_response_conversation(self):
        self.socrates.response_history = []
        self.theaetetus.response_history = []
        self.plato.response_history = []
        self.plato.proofread_suggestions_count = 0

    def add_user_feedback(self, questions, feedback):
        breakpoint()
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

        breakpoint()
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

        if ("bye" in rep):
            breakpoint()
        if ("@final answer: " in rep):
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

    def interaction_get_conversation_start_point(self):
        # Query the Agent for the initial steps
        response = self.socrates.get_conversation_starting_point()
        response = json.loads(response)
        # self.session.init_complete = True

        user_response_msg_list = [{'role': 'Socrates', 'response': response['agent_question']}]
        conversation_message = {'role': 'assistant', 'content': response['agent_question']}
        self.conversation_history.append(conversation_message)

        self.persona_config['data_objects']['framework']['user_state'] = response['user_state']
        self.session.init_complete = True

        return json.dumps(user_response_msg_list)


    # Processes the interactions with the User
    def interactions(self):
        # If the User has provided input, process it to generate a response
        if self.session.init_complete == False:
            # Query the Agent for the next steps
            return self.interaction_get_conversation_start_point()
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
