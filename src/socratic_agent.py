import openai
import os
import json
import re
import time
import anthropic
from pprint import pprint
from memory import AgentMemory
from datetime import datetime
import hashlib
from sql_database import SQLDatabase
from agent import Agent

debug_printing = False
debug_printing = True
debug_converstation = True
debug_converstation = False

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
        success_string = "Analysis looks reasonable. Socrates or Theatetus, please proceed with your final answer using the information you have, no more deliberating."
        suggestions_string = "Here are my suggestions:"

        if self.proofread_see_previous_suggestions_count >= self.proofread_suggestions_count_max or self.proofread_suggestions_count >= self.proofread_suggestions_count_max:
            #proof_read_input = f"You have reached the number of times you are allowed to respond with 'Please see my previous suggestions', please response with \"{success_string}\"."
            #proof_read_input = f"Socrates and Theaetetus have deliberated enough, please agree with their response with \"{success_string}\"."
            msg = f"{success_string}"
            # udpate history
            self.update_response_history("assistant", f"Plato: {msg}")
            return msg
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

        print(f"############## Proofread suggestions count: {self.proofread_suggestions_count} >= {self.proofread_suggestions_count_max}\n")
        print(f"############## Proofread previous suggestions count: {self.proofread_see_previous_suggestions_count} >= {self.proofread_suggestions_count_max}\n")
        if msg.find(suggestions_string) != -1:
            self.proofread_suggestions_count += 1

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
        self.current_user_input = None
        self.memory_system = AgentMemory(persona_config, self.socrates)

    def get_conversation_memory(self):
        user_input = ""
        if self.current_user_input != None:
            user_input = self.current_user_input
        memory = self.memory_system.get_memory(user_input)
        return memory


    def put_conversation_history(self, role, message):
        if role not in ['user', 'agent']:
            breakpoint()

        self.memory_system.store_utterance(role, message)
        # if role == 'user':
        #     user_input = message
        #     # Memory System: Add new memory
        #     conversation_history = self.db.get_conversation_history()
        #     if len(conversation_history) > 0:
        #         # Search backwards until the last 'assistant' message
        #         agent_response = ""
        #         start_index = -1
        #         for i in range(len(conversation_history)-1, -1, -1):
        #             if conversation_history[i]['role'] == 'agent':
        #                 if start_index == -1:
        #                     start_index = i
        #                 agent_response += conversation_history[i]['content']
        #             elif start_index != -1 or i == 0:
        #                 break
        #         if agent_response != "":
        #             self.memory_system.remember_conversation(user_input, agent_response)

        # self.db.put_conversation_history(role, message)

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
        conversation_history_list = self.db.get_conversation_history()
        conversation_history = "START Conversation History\n"
        for message in conversation_history_list:
            conversation_history += f"{message['created_at']}: {message['role']}: {message['content']}\n\n"
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
        self.current_user_input = user_input
        self.put_conversation_history('user', user_input)
        if self.session.in_progress == False:
            self.interaction_start_socratic_conversation()


    def reset_response_conversation(self):
        self.socrates.response_history = []
        self.theaetetus.response_history = []
        self.plato.response_history = []
        self.plato.proofread_suggestions_count = 0
        self.plato.proofread_see_previous_suggestions_count = 0

    # def add_user_feedback(self, questions, feedback):
    #     breakpoint()
    #     self.conversation_history.append({
    #         "role": "assistant",
    #         "content": f"{questions}\n"
    #     })
    #     self.conversation_history.append({
    #         "role": "user",
    #         "content": f"{feedback}\n"
    #     })
    #     self.socrates.add_user_feedback(questions, feedback)
    #     self.theaetetus.add_user_feedback(questions, feedback)
    #     self.plato.add_user_feedback(questions, feedback)

    def need_to_ask_the_User(self, text):

        pattern = r"@Check with the User: QSTART\s*(.*) QEND"
        matches = re.findall(pattern, text)

        if len(matches) == 0:
            return False

        breakpoint()

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

        self.session.send_agent_dialog_message('Socrates', f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any logical mistakes.")
        print(f"Starting Socratic Conversation")
        return True
        # return json.dumps([
        #     {'role': 'Socrates',
        #     'response': f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any logical mistakes.\n"}
        #     ])

    def interaction_ask_user_question(self, question_to_the_user):
        self.session.all_questions_to_the_user = " ".join(question_to_the_user)
        #msg_list.append(
        #    {'role': 'System',
        #    'response': f"Asking the User: {self.session.all_questions_to_the_user}"})
        self.session.send_user_message(self.session.all_questions_to_the_user)
        self.session.user_input = None
        self.session.asked_question = False
        self.session.in_progress = False
        self.session.in_progress_sub = False
        self.session.wait_for_the_user = False
        self.reset_response_conversation()
        #self.session.wait_for_the_user = True
        #return msg_list
        return True

    def interaction_final_answer(self, rep):
        self.session.user_input = None
        self.session.asked_question = False
        self.session.in_progress = False
        self.session.in_progress_sub = False
        self.session.first_question = False

        if ("@FAStart" in rep):
            final_answer_pattern = r"@FAStart\s*(.*?)\s*@FAEnd"
            final_answer_matches = re.findall(final_answer_pattern, rep, re.DOTALL)

            if len(final_answer_matches) > 0:
                final_answer = final_answer_matches[0]
                self.put_conversation_history('agent', final_answer)

            self.session.send_user_message(final_answer)

        elif "The context length exceeds my limit..." in rep:
            self.session.send_user_message("The dialog went too long, please try again.")
            #msg_list.append(
            #        {'role': 'System',
            #        'response': "The dialog went too long, please try again."})
            breakpoint()
        else:
            breakpoint()
        if debug_printing:
            print("user_input:", self.session.user_input)
            print("asked_question:", self.session.asked_question)
            print("in_progress:", self.session.in_progress)
            #print("msg list:")
            #print(msg_list)
            print("end conversation reset")

        self.reset_response_conversation()
        self.session.in_progress_sub = False

        return True

    def interaction_proofread(self):
        pr = self.plato.proofread()
        if pr:
            self.session.send_agent_dialog_message('Plato', pr)
            #user_resp_msg_list.append(
            #    {'role': 'Plato',
            #    'response': pr})
            self.socrates.add_proofread(pr)
            self.theaetetus.add_proofread(pr)
            # feedback = self.ask_the_User(pr)
            # if feedback:
            #     for fed in feedback:
            #         q, a = fed["question"], fed["answer"]
            #         if debug_printing:
            #             print(f"\033[1mThe User:\033[0m Received Question: {q}\n\n  Answer: {a}\n")
            #         self.add_user_feedback(q, a)

        self.session.dialog_lead, self.session.dialog_follower = self.session.dialog_follower, self.session.dialog_lead

        return True

    def interaction_continue_socratic_conversation(self):
        #user_response_msg_list = []
        print(f"Continuing Socratic Conversation: {self.session.in_progress_sub}: {self.session.wait_for_the_user}")
        if True == True: # and self.session.in_progress_sub == False:
            print(f"Continuing Socratic Conversation: deliberating...")
            self.session.in_progress_sub = True
            rep = self.session.dialog_follower.get_response(messages=None, add_to_history=True)
            self.session.send_agent_dialog_message(self.session.dialog_follower.socratic_persona, rep)
            #user_response_msg_list.append({'role': self.session.dialog_follower.socratic_persona, 'response': rep})
            self.session.dialog_lead.update_response_history("assistant", f"{self.session.dialog_follower.socratic_persona}: {rep}")
            self.plato.update_response_history("assistant", f"{self.session.dialog_follower.socratic_persona}: "+rep)
            # question_to_the_user = self.need_to_ask_the_User(rep)
            # if question_to_the_user:
            #     success = self.interaction_ask_user_question(question_to_the_user)
            #     if not success:
            #         breakpoint()
                #self.session.dialog_follower.update_response_history("assistant", f"{self.session.dialog_follower.socratic_persona}: Question to the User: {question_to_the_user}")
            # Sure fire way of detect "@FAStart" in the response
            if ("@FAStart" in rep):
                # or ("The context length exceeds my limit..." in rep):
                print(f"Socratic Conversation: Final answer detected")
                success = self.interaction_final_answer(rep)
                if success == False:
                    breakpoint()
            elif self.session.in_progress_sub == True and self.session.in_progress == True:
                print(f"Continuing Socratic Conversation: Proofreading")
                success = self.interaction_proofread()
                if not success:
                    breakpoint()
            else:
                breakpoint()

            # if debug_converstation:
            #     for message in user_response_msg_list:
            #         if message['role'] != 'System':
            #             message['response'] = 'Deliberating...'

            if debug_printing:
                print("user_input:", self.session.user_input)
                print("asked_question:", self.session.asked_question)
                print("in_progress:", self.session.in_progress)
                #print("msg list:")
                #print(user_response_msg_list)
        else:
            if debug_printing:
                print("Processing User Input")

        return True
        #return json.dumps(user_response_msg_list)

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

        self.session.send_user_message(response['agent_greeting'])
        self.session.send_user_message(response['current_context'])
        self.session.send_user_message(response['next_steps'])
        self.session.send_user_message(response['agent_question'])
        #user_response_msg_list = [{'role': 'Agent', 'response': response['agent_question']}]
        self.put_conversation_history('agent', response['agent_question'])

        self.persona_config['data_objects']['framework']['user_state'] = response['user_state']
        self.session.init_complete = True

        return True


    # Processes the interactions with the User
    def interactions(self, user_input=None):
        # If the User has provided input, process it to generate a response
        if user_input != None:
            self.process_user_input(user_input)
        elif self.session.init_complete == False:
            # Query the Agent for the next steps
            self.interaction_get_conversation_start_point()
        elif self.session.in_progress:
            # Continue the Socratic conversation to generate a response to the user's input
            while self.session.in_progress:
                self.interaction_continue_socratic_conversation()
        elif not self.session.asked_question:
            # If the user has not provided input, and the agent has not asked any questions
            # then ask the user for a question
            #print("waiting for next user input")
            return True
            breakpoint()
            return self.interaction_ask_for_more_questions()
        else:
            # If the user has not provided input, and the agent has already asked a question
            # Do nothing
            if debug_printing:
                print("user_input:", self.session.user_input)
                print("asked_question:", self.session.asked_question)
                print("in_progress:", self.session.in_progress)
                print("no question skip")
            return True

        return True