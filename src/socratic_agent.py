import openai
import os
import json
import re
import time

debug_printing = False

class SocraticAgent:

    def __init__(self, persona, model="gpt-3.5-turbo"):
        self.persona = persona
        self.model = model
        self.history = []
        self.gpt_client = openai.OpenAI(
            # This is the default and can be omitted
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def get_gpt_response(self, messages):
        try:
            res = self.gpt_client.chat.completions.create(
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
                msg = "The context length exceeds my limit... "
            else:
                # Handle other errors here
                msg = f"I enconter an when using my backend model.\n\n Error: {str(e)}"
            breakpoint()

        return msg

    def get_response(self):
        msg = self.get_gpt_response(self.history)
        self.history.append({
                "role": "assistant",
                "content": msg
            })
        return msg

    def update_history(self, message):
        self.history.append({
            "role": "user",
            "content": message
        })

    def add_feedback(self, question, answer):
        self.history.append({
            "role": "system",
            "content": f"the User's feedback to \"{question}\" is \"{answer}\""
        })

    def add_proofread(self, proofread):
        self.history.append({
            "role": "system",
            "content": f"Message from a proofreader Plato to you two: {proofread}"
        })

class Socrates(SocraticAgent):
    def __init__(self, model="gpt-3.5-turbo"):
        super().__init__('Socrates', model)
        self.other_role = "Theaetetus"

    def set_question(self, question):
        self.history.append({
            "role": "system",
                "content": f"Socrates and Theaetetus are two AI assistants for the User to solve challenging problems. The problem statement is as follows: \"{question}\".\n\nSocrates and Theaetetus will engage in multi-round dialogue to solve the problem together for the User. They are permitted to consult with the User if they encounter any uncertainties or difficulties, by using the following phrase: \"@Check with the User: [insert your question]\". Any responses from the User will be provided in the following round. Their discussion should follow a structured problem-solving approach, such as formalizing the problem, developing high-level strategies for solving the problem, writing Python scripts when necessary, reusing subproblem solutions where possible, critically evaluating each other's reasoning, avoiding arithmetic and logical errors, and effectively communicating their ideas. \n\nThey are encouraged to write and execute Python scripts. To do that, they must follow the following instructions:\n1. use the phrase \"@write_code [insert python scripts wrapped in a markdown code block]\". \n2. use the phrase \"@execute\" to execute the previously written Python scripts. \n\nE.g., \n@write_code\n```\ndef f(n):\n	return n+1\n\n	print(f(n))\n```\n\n@execute\n\nAll these scripts will be sent to a subprocess.Popen() object that runs in the backend. The system will provide the output and error messages from executing their Python scripts in the subsequent round.\n\nTo aid them in their calculations and fact-checking, they are also allowed to consult WolframAlpha. They can do so by using the phrase \"@Check with WolframAlpha: [insert your question]\", and the system will provide responses in the subsequent round.\n\nTheir ultimate objective is to come to a correct solution through reasoned discussion. To present their final answer, they should adhere to the following guidelines:\n\nState the problem they were asked to solve.\nPresent any assumptions they made in their reasoning.\nDetail the logical steps they took to arrive at their final answer.\nVerify any mathematical calculations with WolframAlpha to prevent arithmetic errors.\nConclude with a final statement that directly answers the problem.\nTheir final answer should be concise and free from logical errors, such as false dichotomy, hasty generalization, and circular reasoning. \n\nIt should begin with the phrase: \"Here is our @final answer: [insert answer]\". If they encounter any issues with the validity of their answer, they should re-evaluate their reasoning and calculations.\n\nNow, suppose that you are {self.persona}. Please discuss the problem with {self.other_role}!"}
        )
        self.history.append({
            "role": "assistant",
            "content": f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any mistakes."
        })

class Theaetetus(SocraticAgent):
    def __init__(self, model="gpt-3.5-turbo"):
        super().__init__('Theaetetus', model)

        self.other_role = "Socrates"

    def set_question(self, question):
            self.history.append({
                "role": "system",
                 "content": f"Socrates and Theaetetus are two AI assistants for the User to solve challenging problems. The problem statement is as follows: \"{question}\".\n\nSocrates and Theaetetus will engage in multi-round dialogue to solve the problem together for the User. They are permitted to consult with the User if they encounter any uncertainties or difficulties, by using the following phrase: \"@Check with the User: [insert your question]\". Any responses from the User will be provided in the following round. Their discussion should follow a structured problem-solving approach, such as formalizing the problem, developing high-level strategies for solving the problem, writing Python scripts when necessary, reusing subproblem solutions where possible, critically evaluating each other's reasoning, avoiding arithmetic and logical errors, and effectively communicating their ideas. \n\nThey are encouraged to write and execute Python scripts. To do that, they must follow the following instructions:\n1. use the phrase \"@write_code [insert python scripts wrapped in a markdown code block]\". \n2. use the phrase \"@execute\" to execute the previously written Python scripts. \n\nE.g., \n@write_code\n```\ndef f(n):\n	return n+1\n\n	print(f(n))\n```\n\n@execute\n\nAll these scripts will be sent to a subprocess.Popen() object that runs in the backend. The system will provide the output and error messages from executing their Python scripts in the subsequent round.\n\nTo aid them in their calculations and fact-checking, they are also allowed to consult WolframAlpha. They can do so by using the phrase \"@Check with WolframAlpha: [insert your question]\", and the system will provide responses in the subsequent round.\n\nTheir ultimate objective is to come to a correct solution through reasoned discussion. To present their final answer, they should adhere to the following guidelines:\n\nState the problem they were asked to solve.\nPresent any assumptions they made in their reasoning.\nDetail the logical steps they took to arrive at their final answer.\nVerify any mathematical calculations with WolframAlpha to prevent arithmetic errors.\nConclude with a final statement that directly answers the problem.\nTheir final answer should be concise and free from logical errors, such as false dichotomy, hasty generalization, and circular reasoning. \n\nIt should begin with the phrase: \"Here is our @final answer: [insert answer]\". If they encounter any issues with the validity of their answer, they should re-evaluate their reasoning and calculations.\n\nNow, suppose that you are {self.persona}. Please discuss the problem with {self.other_role}!"}
            )
            self.history.append({
                "role": "user",
                "content": f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any mistakes."
            })

class Plato(SocraticAgent):
    def __init__(self, model="gpt-3.5-turbo"):
        super().__init__('Plato', model)

    def set_question(self, question):
        self.history.append({
            "role": "system",
                "content": f"Socrates and Theaetetus are two AI assistants for the User to solve challenging problems. The problem statement is as follows: \"{question}\".\n\nSocrates and Theaetetus will engage in multi-round dialogue to solve the problem together for the User. They are permitted to consult with the User if they encounter any uncertainties or difficulties, by using the following phrase: \"@Check with the User: [insert your question]\". Any responses from the User will be provided in the following round. Their discussion should follow a structured problem-solving approach, such as formalizing the problem, developing high-level strategies for solving the problem, writing Python scripts when necessary, reusing subproblem solutions where possible, critically evaluating each other's reasoning, avoiding arithmetic and logical errors, and effectively communicating their ideas. \n\nThey are encouraged to write and execute Python scripts. To do that, they must follow the following instructions:\n1. use the phrase \"@write_code [insert python scripts wrapped in a markdown code block]\". \n2. use the phrase \"@execute\" to execute the previously written Python scripts. \n\nE.g., \n@write_code\n```\ndef f(n):\n	return n+1\n\n	print(f(n))\n```\n\n@execute\n\nAll these scripts will be sent to a subprocess.Popen() object that runs in the backend. The system will provide the output and error messages from executing their Python scripts in the subsequent round.\n\nTo aid them in their calculations and fact-checking, they are also allowed to consult WolframAlpha. They can do so by using the phrase \"@Check with WolframAlpha: [insert your question]\", and the system will provide responses in the subsequent round.\n\nTheir ultimate objective is to come to a correct solution through reasoned discussion. To present their final answer, they should adhere to the following guidelines:\n\nState the problem they were asked to solve.\nPresent any assumptions they made in their reasoning.\nDetail the logical steps they took to arrive at their final answer.\nVerify any mathematical calculations with WolframAlpha to prevent arithmetic errors.\nConclude with a final statement that directly answers the problem.\nTheir final answer should be concise and free from logical errors, such as false dichotomy, hasty generalization, and circular reasoning. \n\nIt should begin with the phrase: \"Here is our @final answer: [insert answer]\". If they encounter any issues with the validity of their answer, they should re-evaluate their reasoning and calculations.\n\nNow as a proofreader, Plato, your task is to read through the dialogue between Socrates and Theaetetus and identify any errors they made."}
        )
        self.history.append({
            "role": "user",
            "content": f"Socrates: Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any mistakes."
        })

    def proofread(self):
        pf_template = {
                "role": "user",
                "content": "The above is the conversation between Socrates and Theaetetus. You job is to challenge their anwers. They were likely to have made multiple mistakes. Please correct them. \nRemember to start your answer with \"NO\" if you think so far their discussion is alright, otherwise start with \"Here are my suggestions:\""
        }

        msg = self.get_gpt_response(self.history + [pf_template])

        if msg[:2] in ["NO", "No", "no"]:
            return None
        else:
            self.history.append({
                    "role": "assistant",
                    "content": msg
                })
            return msg

class Agent:

    def __init__(self, session, model="gpt-3.5-turbo"):
        self.session = session
        self.socrates = Socrates(model)
        self.theaetetus = Theaetetus(model)
        self.plato = Plato(model)

    def need_to_ask_the_User(self, text):
        pattern = r"@Check with the User:\s*(.*)"
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

    def interactions(self):
        if self.session.question:
            if not self.session.in_progress:
                self.session.in_progress = True
                self.session.dialog_lead, self.session.dialog_follower = self.socrates, self.theaetetus
                return json.dumps([
                    {'role':'Socrates',
                    'response': f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any logical or mathematical mistakes.\n"}
                    ])
            else:
                if self.session.in_progress_sub == False and self.session.wait_for_the_user == False:
                    self.session.in_progress_sub = True
                    msg_list = []
                    rep = self.session.dialog_follower.get_response()
                    msg_list.append({'role': self.session.dialog_follower.persona, 'response': rep})
                    self.session.dialog_lead.update_history(rep)
                    self.plato.update_history(f"{self.session.dialog_follower.persona}: "+rep)
                    question_to_the_user = self.need_to_ask_the_User(rep)
                    if question_to_the_user:
                        self.session.all_questions_to_the_user = " ".join(question_to_the_user)
                        msg_list.append(
                            {'role': 'System',
                            'response': f"Asking the User: {self.session.all_questions_to_the_user}"})
                        self.session.wait_for_the_user = True


                    elif ("@final answer" in rep) or ("bye" in rep) or ("The context length exceeds my limit..." in rep):
                        self.session.question = None
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
                            print("question:", self.session.question)
                            print("asked_question:", self.session.asked_question)
                            print("in_progress:", self.session.in_progress)
                            print("msg list:")
                            print(msg_list)
                            print("end conversation reset")
                        self.session.in_progress_sub = False

                        return json.dumps(msg_list)

                    else:
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
                                    self.socrates.add_feedback(q, a)
                                    self.theaetetus.add_feedback(q, a)
                                    self.plato.add_feedback(q, a)

                        self.session.dialog_lead, self.session.dialog_follower = self.session.dialog_follower, self.session.dialog_lead

                    if debug_printing:
                        print("question:", self.session.question)
                        print("asked_question:", self.session.asked_question)
                        print("in_progress:", self.session.in_progress)
                        print("msg list:")
                        print(msg_list)
                    self.session.in_progress_sub = False
                    return json.dumps(msg_list)

                else:
                    if debug_printing:
                        print("under processing")
                    return json.dumps([])
        elif not self.session.asked_question:
            self.session.asked_question = True
            if debug_printing:
                print("question:", self.session.question)
                print("asked_question:", self.session.asked_question)
                print("in_progress:", self.session.in_progress)
                print("ask user's question")
            if self.session.first_question:
                msg = "What's your question?"
            else:
                msg = "Do you have more questions?"
            return json.dumps([{'role': 'System',
                            'response': msg}])
        else:
            if debug_printing:
                print("question:", self.session.question)
                print("asked_question:", self.session.asked_question)
                print("in_progress:", self.session.in_progress)
                print("no question skip")
            return json.dumps([])
