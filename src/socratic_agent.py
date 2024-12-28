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

class Agent:

    LLM_API="anthropic"
    LLM_API="openai"

    def __init__(self, persona, prompts=None, model=None):
        self.persona = persona
        self.other_persona = None
        if model == None:
            print("Auto detecting model")
        self.model = model
        self.history = []
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

        if persona == "Socrates":
            self.other_persona = "Theaetetus"
        elif persona == "Theaetetus":
            self.other_persona = "Socrates"

        if prompts == None:
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
        else:
            self.prompts = prompts

    def set_prompts(self, prompts):
        self.prompts = prompts

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
            messages = self.history
            #breakpoint()

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
            self.history.append({
                    "role": "assistant",
                    "content": f"{self.persona}: {msg}"
                })
        return msg

    def update_history(self, role, message):
        if message == "":
            #breakpoint()
            return
        self.history.append({
            "role": role,
            "content": message
        })

    def add_feedback(self, question, answer):
        self.history.append({
            "role": 'user',
            "content": f"the User's feedback to \"{question}\" is \"{answer}\""
        })

    def add_proofread(self, proofread):
        self.history.append({
            "role": self.socrate_agent_role,
            "content": f"Message from a proofreader Plato to you two: {proofread}"
        })

    def set_question(self, user_input):
        self.history = []
        system_role = f"""
Socrates, Theaetetus, and Plato are three AI assistants. Their purpose is {self.prompts['purpose']}

Socrates and Theaetetus will engage in multi-round dialogue to {self.prompts['engagement_purpose']}.
They will ensure that Plato has proofread their dialog and does not have any suggestions before giving their final answer.

They are permitted to consult with the User if they encounter any uncertainties, difficulties, or need to
make assumtions by using the following phrase: "@Check with the User: QSTART [insert your question] QEND". Any responses from
the User will be provided in the following round.

Their discussion should follow a {self.prompts['discussion_strategy']}.

Their ultimate objective is to {self.prompts['ultimate_objective']}.

To present their final answer, they should adhere to the following guidelines:

- State the problem they were asked to solve.
- Present any assumptions they made in their reasoning.
- Detail the logical steps they took to arrive at their final answer.
- Socrates and Theaetetus will ensure that Plato has proofread their dialog and does not have any suggestions.
- Conclude with a final statement that directly answers the problem.
- Their final answer should be concise and free from logical errors, such as false dichotomy, hasty generalization,
  circular reasoning
- If they end up having multiple possible answers, they should continue analyzing until they reach a consensus.

It should begin with the phrase: "Here is our @final answer: [insert answer]". The "@final answer:" text should
only be generated once Plato no longer has any suggestions the answer.

If they encounter any issues with the validity of their answer, {self.prompts['if_answer_not_valid']}.
"""

        if self.persona == 'Plato':
            system_role += "\n\nNow as a proofreader, Plato, your task is to read through the dialogue between Socrates and Theaetetus and identify any errors they made."
        else:
            system_role += f"Now, suppose that you are {self.persona}. Please discuss the problem with {self.other_persona}!"

        system_role += f"Generate responses for {self.persona} only. Responses from the other agents will be provided in the next round."

        self.history.append({
            "role": self.socrate_agent_role,
            "content": system_role
        })

        self.history.append({
            "role": "user",
            "content": f"{self.prompts['user_input']}: \"{user_input}\"."
        })

        if self.persona == "Plato":
            assistant_role = f"Hi Theaetetus and Socrates, "
        else:
            assistant_role = f"Hi {self.persona}, "
        assistant_role += "let's solve this problem together. Please feel free to correct me if I make any mistakes."
        self.history.append({
            "role": "assistant",
            "content": assistant_role
        })


class SocratesAgent(Agent):
    def __init__(self, prompts=None, model=None):
        super().__init__('Socrates', prompts, model)


class TheaetetusAgent(Agent):
    def __init__(self, prompts=None, model=None):
        super().__init__('Theaetetus', prompts, model)

class PlatoAgent(Agent):
    def __init__(self, prompts=None, model=None):
        super().__init__('Plato', prompts, model)

    def proofread(self):
        success_string = "Analysis looks reasonable"
        suggestions_string = "Here are my suggestions:"
        pf_template = {
                "role": "user",
                "content": f"""
The above is the conversation between Socrates and Theaetetus. Your job is to challenge their answers.
They were likely to have made multiple mistakes. Please correct them.
If the latest response from Socrates or Theaetetus does not offer any new information, please response with \"Waiting for more information\".
If you think so far their discussion is alright, please respond with \"{success_string}.\". Do not ask the user any questions.
Otherwise start with \"{suggestions_string}\"\n"""
        }

        #msg = self.get_anthropic_response(self.history + [pf_template])
        msg = self.get_response(self.history + [pf_template], add_to_history=False)
        #print("\n-----------------------------------\n")
        #print("\nPlato Proofread it!\n")

        # Check if msg starts with "Analysis looks reasonable" case insensitively
        if msg[:len(suggestions_string)+1].lower() == success_string.lower():
            return msg
        else:
            #breakpoint()
            self.history.append({
                    "role": "assistant",
                    "content": msg
                })
            return msg

class SocraticAgent:

    def __init__(self, session, prompts=None, model=None):
        #if model == None:
            #breakpoint()
        self.session = session
        self.socrates = SocratesAgent(prompts, model)
        self.theaetetus = TheaetetusAgent(prompts, model)
        self.plato = PlatoAgent(prompts, model)

    def set_question(self, user_input):
        self.socrates.set_question(user_input)
        self.theaetetus.set_question(user_input)
        self.plato.set_question(user_input)

    def add_feedback(self, questions, feedback):
        self.socrates.add_feedback(questions, feedback)
        self.theaetetus.add_feedback(questions, feedback)
        self.plato.add_feedback(questions, feedback)

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
        self.socrates.history = []
        self.theaetetus.history = []
        self.plato.history = []

        if ("@final answer" in rep) or ("bye" in rep):
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
        self.session.in_progress_sub = False

        return msg_list

    def interaction_proofread(self, msg_list):
        pr = self.plato.proofread()
        if pr:
            msg_list.append(
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
                    self.add_feedback(q, a)

        self.session.dialog_lead, self.session.dialog_follower = self.session.dialog_follower, self.session.dialog_lead

        return msg_list

    def interaction_continue_socratic_conversation(self):
        msg_list = []
        if self.session.in_progress_sub == False and self.session.wait_for_the_user == False:
            self.session.in_progress_sub = True
            rep = self.session.dialog_follower.get_response(messages=None, add_to_history=True)
            msg_list.append({'role': self.session.dialog_follower.persona, 'response': rep})
            self.session.dialog_lead.update_history("user", rep)
            self.plato.update_history("assistant", f"{self.session.dialog_follower.persona}: "+rep)
            question_to_the_user = self.need_to_ask_the_User(rep)
            if question_to_the_user:
                msg_list = self.interaction_ask_user_question(msg_list, question_to_the_user)
                self.session.dialog_follower.update_history("assistant", f"Question to the User: {question_to_the_user}")
            elif ("@final answer" in rep) or ("bye" in rep) or ("The context length exceeds my limit..." in rep):
                return json.dumps(self.interaction_final_answer(msg_list, rep))
            else:
                msg_list = self.interaction_proofread(msg_list)

            if debug_converstation:
                for message in msg_list:
                    if message['role'] != 'System':
                        message['response'] = 'Deliberating...'

            if 0 and debug_printing:
                print("user_input:", self.session.user_input)
                print("asked_question:", self.session.asked_question)
                print("in_progress:", self.session.in_progress)
                print("msg list:")
                print(msg_list)
            self.session.in_progress_sub = False
        else:
            if debug_printing:
                print("under processing")
        return json.dumps(msg_list)

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
