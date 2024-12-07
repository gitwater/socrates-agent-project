
import json
import re
from socratic_agent import Socrates, Theaetetus, Plato
import readline
import textwrap
import time
from cli import CLI

session_states = {}
default_client_id = 1
last_client_id = default_client_id

debug_printing = False

class SessionState:
    def __init__(self, client_id):
        self.client_id = client_id
        self.socrates = Socrates()
        self.theaetetus = Theaetetus()
        self.plato = Plato()
        self.dialog_lead = None
        self.dialog_follower = None
        self.question = None
        self.asked_question = False
        self.in_progress = False
        self.in_progress_sub = False
        self.first_question = True
        self.wait_the_user = False
        self.interactive_p = None
        self.all_questions_to_the_user = ""
        self.cli = CLI(client_id)

def need_to_ask_the_User(text):
    pattern = r"@Check with the User:\s*(.*)"
    matches = re.findall(pattern, text)

    if len(matches) == 0:
        return False

    return matches

def ask_the_User(text):
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

def active_message(session):
    global N, last_client_id, session_states

    #client_id = int(session['client_id'])
    # if client_id > last_client_id:
    #     print("current session id", client_id)
    #     print("last_client_id", last_client_id)
    #     last_client_id = client_id
    #     session_states[last_client_id] = SessionState(last_client_id)

    # session_state = session_states[client_id]
    session_state = session

    if session_state.question:
        if not session_state.in_progress:
            session_state.in_progress = True
            session_state.dialog_lead, session_state.dialog_follower = session_state.socrates, session_state.theaetetus
            return json.dumps([
                {'role':'Socrates',
                'response': f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any logical or mathematical mistakes.\n"}
                ])
        else:
            if session_state.in_progress_sub == False and session_state.wait_the_user == False:
                session_state.in_progress_sub = True
                msg_list = []
                rep = session_state.dialog_follower.get_response()
                msg_list.append({'role': session_state.dialog_follower.persona, 'response': rep})
                session_state.dialog_lead.update_history(rep)
                session_state.plato.update_history(f"{session_state.dialog_follower.persona}: "+rep)
                question_to_the_user = need_to_ask_the_User(rep)
                if question_to_the_user:
                    session_state.all_questions_to_the_user = " ".join(question_to_the_user)
                    msg_list.append(
                        {'role': 'System',
                         'response': f"Asking the User: {session_state.all_questions_to_the_user}"})
                    session_state.wait_the_user = True


                elif ("@final answer" in rep) or ("bye" in rep) or ("The context length exceeds my limit..." in rep):
                    session_state.question = None
                    session_state.asked_question = False
                    session_state.in_progress = False
                    session_state.first_question = False
                    session_state.interactive_p = None
                    session_state.socrates.history = []
                    session_state.theaetetus.history = []
                    session_state.plato.history = []

                    if ("@final answer" in rep) or ("bye" in rep):
                        msg_list.append(
                                {'role': 'System',
                                 'response': "They just gave you their final answer."})
                    elif "The context length exceeds my limit..." in rep:
                        msg_list.append(
                                {'role': 'System',
                                 'response': "The dialog went too long, please try again."})
                    if debug_printing:
                        print("question:", session_state.question)
                        print("asked_question:", session_state.asked_question)
                        print("in_progress:", session_state.in_progress)
                        print("msg list:")
                        print(msg_list)
                        print("end conversation reset")
                    session_state.in_progress_sub = False

                    return json.dumps(msg_list)

                else:
                    pr = session_state.plato.proofread()
                    if pr:
                        msg_list.append(
                            {'role': 'Plato',
                            'response': pr})
                        session_state.socrates.add_proofread(pr)
                        session_state.theaetetus.add_proofread(pr)
                        feedback = ask_the_User(pr)
                        if feedback:
                            for fed in feedback:
                                q, a = fed["question"], fed["answer"]
                                if debug_printing:
                                    print(f"\033[1mThe User:\033[0m Received Question: {q}\n\n  Answer: {a}\n")
                                session_state.socrates.add_feedback(q, a)
                                session_state.theaetetus.add_feedback(q, a)
                                session_state.plato.add_feedback(q, a)

                    session_state.dialog_lead, session_state.dialog_follower = session_state.dialog_follower, session_state.dialog_lead

                if debug_printing:
                    print("question:", session_state.question)
                    print("asked_question:", session_state.asked_question)
                    print("in_progress:", session_state.in_progress)
                    print("msg list:")
                    print(msg_list)
                session_state.in_progress_sub = False
                return json.dumps(msg_list)

            else:
                if debug_printing:
                    print("under processing")
                return json.dumps([])
    elif not session_state.asked_question:
        session_state.asked_question = True
        if debug_printing:
            print("question:", session_state.question)
            print("asked_question:", session_state.asked_question)
            print("in_progress:", session_state.in_progress)
            print("ask user's question")
        if session_state.first_question:
            msg = "What's your question?"
        else:
            msg = "Do you have more questions?"
        return json.dumps([{'role': 'System',
                         'response': msg}])
    else:
        if debug_printing:
            print("question:", session_state.question)
            print("asked_question:", session_state.asked_question)
            print("in_progress:", session_state.in_progress)
            print("no question skip")
        return json.dumps([])


def chat(session):
    global session_states
    session_state = session
    chat_response = None

    if session_state.question is None or session_state.wait_the_user:
        user_input = session_state.cli.read_input()
        if session_state.question is None:
            session_state.question = user_input
            session_state.socrates.set_question(session_state.question)
            session_state.theaetetus.set_question(session_state.question)
            session_state.plato.set_question(session_state.question)
            response = generate_response(user_input, mode="question")

        if session_state.wait_the_user:
            feedback = user_input
            session_state.socrates.add_feedback(session_state.all_questions_to_the_user, feedback)
            session_state.theaetetus.add_feedback(session_state.all_questions_to_the_user, feedback)
            session_state.plato.add_feedback(session_state.all_questions_to_the_user, feedback)
            session_state.all_questions_to_the_user = ""
            session_state.wait_the_user = False
            response = generate_response(user_input, mode="feedback")

        chat_response = json.dumps([{'role': 'System','response': response}])

    return chat_response

def generate_response(user_input, mode="question"):
    if mode == "question":
        return f"You just said: {user_input}\n\nA conversation among (Socrates, Theaetetus, and Plato) will begin shortly..."
    elif mode == "feedback":
        return f"Received your feedback: {user_input}"
    return "Connecting..."

def main():
    session = SessionState(default_client_id)

    while True:
        response = chat(session)
        if response != None:
            session.cli.write_json(response)
        response = active_message(session)
        session.cli.write_json(response)

if __name__ == "__main__":
    main()
