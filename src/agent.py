# import required libraries
import json
import openai
import anthropic

debug_token_printing = True

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
            self.model = 'gpt-4o-mini'
            #self.model = 'gpt-3.5-turbo'
            #self.model = 'gpt-4o'
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

If they want to ask the user questions to further understand the context, they should ask the question as
part of their final answer. The user's response will be provided in the next round.

To ensure that their response is correct Plato will proofread their dialog and provide feedback to them.
Socrates and Theaetetus will ensure that Plato has proofread their dialog to esure he does not have any suggestions
before giving their final answer.

If they end up having multiple possible answers, they should continue analyzing until they reach a consensus.

When Socrates is ready to present the final answer, he should do so using the text @FAStart [insert answer] @FAEnd .
The final answer should only be generated once Plato no longer has any suggestions the answer. The answer must be
worded from the perspective of the agent speaking to the user. The final answer should flow with the Conversation
History so that it feels like the conversation has continuity of context.
"""
#If they encounter any issues with the validity of their answer, they should re-evaluate their reasoning and calculations.
#"""

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
            print(f"!!! ERROR: {msg}: Retrying!!")
            breakpoint()
            return ""

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

    def get_embeddings(self, input_text):
        if Agent.LLM_API == "anthropic":
            embeddings = self.llm_client.embeddings.create(
                model=self.model,
                input_text=input_text
            )
        elif Agent.LLM_API == "openai":
            embeddings = self.llm_client.embeddings.create(
                model='text-embedding-ada-002',
                #model='text-embedding-3-small',
                #model='text-embedding-3-large'
                input=input_text,
                encoding_format="float"
            )
        else:
            print("LLM API not set")
            breakpoint()

        return embeddings.data[0].embedding

    def get_response(self, messages=None, add_to_history=False, json_response=False):
        if messages == None:
            # Insert Framework messages
            # System profile
            #
            messages = self.get_framework_messages()
            # Iterate over messages and appent to a local file
            with open("messages.json", "+a") as f:
                f.write("----------------------------------------\n")
                f.write(f"Agent: {self.socratic_persona}\n")
                json.dump(messages, f, indent=4)

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
                breakpoint()

        # Print the number of tokens in the messages and the response
        # A token is 4 bytes
        if debug_token_printing:
            print(f"\n>>>>>>>>> {self.socrate_agent_role}: Get Response: Input Tokens: {len(''.join([m['content'] for m in messages]))/4}: Output Tokens: {len(msg)/4}\n")

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

    # def add_user_feedback(self, question, answer):
    #     self.response_history.append({
    #         "role": 'user',
    #         "content": f"the User's feedback to \"{question}\" is \"{answer}\""
    #     })

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
        else:
            if system_role_type not in ["socratic", "final_answer", "starting_point"]:
                breakpoint()
            system_content = self.system_role_single_agent
            json_format_dict = self.persona_agent.persona_config['json_response_format']['general']
            merged_json_format_dict = {**json_format_dict, **self.persona_agent.persona_config['json_response_format'][system_role_type]}
            system_content += f"""
JSON Response Format:
{json.dumps(merged_json_format_dict)}

Please ensure that all variables in the JSON response format have valid values.
"""

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
        for message in messages:
            if type(message) == str and len(message) == 0:
                breakpoint()

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
        memory_context = self.persona_agent.get_conversation_memory()
        if len(memory_context) > 0:
            memory_message = {
                "role": "assistant",
                "content": memory_context
            }
            messages.append(memory_message)

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

        return response
