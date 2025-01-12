from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import uuid
import time
import subprocess
from subprocess import TimeoutExpired
from session import SessionState

from socratic_agent import *
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
#logging.basicConfig(level=logging.ERROR)


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'socraticalpaca'
Session(app)

N = 50
last_client_id = 0
session_states = {}


@app.route('/')
def index():
    global last_client_id
    last_client_id += 1
    session['client_id'] = last_client_id
    session_states[last_client_id] = SessionState(last_client_id)
    #return render_template('index.html')
    return render_template('index_debug.html')


@app.route('/active-message')
def active_message():

    global N, last_client_id, session_states

    client_id = int(session['client_id'])
    if client_id > last_client_id:
        print("current session id", client_id)
        print("last_client_id", last_client_id)
        last_client_id = client_id
        session_states[last_client_id] = SessionState(last_client_id)

    session_state = session_states[client_id]

    success = session_state.agent.interactions()
    if success:
        user_messages = session_state.pop_user_messages()
        deliberation_messages = session_state.pop_agent_dialog_messages()
        user_messages.extend(deliberation_messages)
        return jsonify(user_messages)
    else:
        breakpoint()

@app.route('/chat', methods=['POST'])
def chat():
    global session_states
    client_id = int(session['client_id'])
    session_state = session_states[client_id]

    user_input = request.form['user_input']
    success = session_state.agent.interactions(user_input)
    if success:
        user_messages = session_state.pop_user_messages()
        return jsonify(user_messages)

    return jsonify([])
    # if session_state.question is None:
    #     session_state.question = user_input
    #     session_state.socrates.set_question(session_state.question)
    #     session_state.theaetetus.set_question(session_state.question)
    #     session_state.plato.set_question(session_state.question)
    #     response = generate_response(user_input, mode="question")

    # if session_state.wait_tony:
    #     feedback = user_input
    #     session_state.socrates.add_feedback(session_state.all_questions_to_tony, feedback)
    #     session_state.theaetetus.add_feedback(session_state.all_questions_to_tony, feedback)
    #     session_state.plato.add_feedback(session_state.all_questions_to_tony, feedback)
    #     session_state.all_questions_to_tony = ""
    #     session_state.wait_tony = False
    #     response = generate_response(user_input, mode="feedback")

    return jsonify([{'role': 'system','response': response}])


# def generate_response(user_input, mode="question"):
#     if mode == "question":
#         return f"You just said: {user_input}\n\nA conversation among (Socrates, Theaetetus, and Plato) will begin shortly..."
#     elif mode == "feedback":
#         return f"Received your feedback: {user_input}"
#     return "Connecting..."


if __name__ == '__main__':
    app.run(port=8000, debug=True)
