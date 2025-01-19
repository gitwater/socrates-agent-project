# Import required libraries
import json
from datetime import datetime
import hashlib
import chromadb


class AgentMemory:
    def __init__(self, persona_config, agent):
        self.size_threshold = 100
        self.agent = agent
        self.vector_db_client = chromadb.PersistentClient(path=f"./db/vector/{persona_config['persona']['name'].lower()}.db")
        self.collection = self.vector_db_client.get_or_create_collection(
            "agent_memory",
            metadata={
                "description": "A collection of embeddings for user inputs and agent responses.",
                "created": str(datetime.now())
            }
        )


    def generate_embeddings(self, user_input, agent_response):
        # Generate embeddings for the user input and agent response
        embeddings = self.agent.get_response([{"role": "system", "content": user_input}, {"role": "system", "content": agent_response}], json_response=True)
        return embeddings

    def analyze_conversation(self, user_input, agent_response):
        prompt = f"""
Analyze the following user input and agent response. Extract the required metadata according to the JSON schema provided
 below. Ensure all fields are populated accurately, following the provided descriptions and predefined options.

User input: "{user_input}"
Agent response: "{agent_response}"

### Predefined Options

#### Semantic Tags:
Choose one or more tags that represent the main topics or intents of the conversation:
- information_request: Used when the user or agent seeks specific facts, knowledge, or clarification about a topic.
- problem_solving: Applied when the conversation focuses on identifying and resolving an issue or challenge.
- decision_making: For interactions involving evaluating options and making choices.
- emotional_expression: Tags conversations where feelings such as frustration, excitement, or sadness are expressed.
- self_reflection: Used when the user or agent reflects on personal experiences, thoughts, or emotions.
- feedback_exchange: Applied when giving or receiving constructive feedback about actions, ideas, or outcomes.
- planning: Tags discussions about organizing or preparing for future actions or tasks.
- learning: Used for conversations centered on acquiring new skills, knowledge, or insights.
- collaboration: For interactions that involve working together or coordinating efforts toward a shared goal.
- context_linking: Tags when the current conversation is explicitly related to previous discussions or experiences.
- future_projection: Used for imagining, predicting, or discussing future scenarios or possibilities.
- relationship_building: Applied when the interaction strengthens interpersonal rapport or establishes trust.
- task_management: Tags conversations focused on tracking, assigning, or completing tasks.
- motivation: Used when the conversation aims to inspire or encourage action toward goals.
- insight_generation: For interactions where new ideas, perspectives, or connections are uncovered.
- attention_focus: Tags when the conversation narrows attention to a specific aspect or priority.
- emotional_regulation: Applied when the interaction involves managing or balancing emotions constructively.
- exploration: For conversations that delve into new ideas, possibilities, or open-ended questions.

#### Emotional Tone:
Choose one tone that best reflects the emotional state of the user during the interaction:
- neutral: The conversation is calm, objective, or informational.
- frustrated: The user shows signs of annoyance, impatience, or dissatisfaction.
- angry: The user expresses anger, irritation, or hostility.
- hopeful: The user conveys optimism or anticipation of a positive outcome.
- happy: The user is pleased, satisfied, or showing appreciation.
- confused: The user is uncertain or seeking clarification.
- anxious: The user expresses worry, nervousness, or concern.
- grateful: The user conveys thanks or gratitude.
- upset: The user is emotionally distressed or disappointed.

#### Interaction Sequence:
Choose the sequence that best describes the flow of the conversation:
- user_input_first: The user is initiating a new conversation or asking a question.
- agent_response_first: The agent is initiating a new conversation or asking a question.

Use the above definitions to ensure the metadata generated in the json output accurately reflects the interaction.

JSON Response Format:
{{
  "semantic_tags": "A comma deliminated list of relevant topics or intents for the interaction. Select from the predefined options above."],
  "emotional_tone": "The overall emotional tone of the interaction. Select from the predefined options above.",
  "key_entities": "A comma deliminated list of names, dates, events, or specific entities mentioned in the interaction.",
  "interaction_summary": "A concise summary of the user input and agent response in 1-2 sentences, capturing the essence of the exchange.",
  "interaction_sequence": "Indicates the sequence of interaction in the conversation, specifying whether the user input or agent response initiated the exchange."
}}
"""

        messages = [
            {
                "role": "system",
                "content": prompt
            }
        ]
        response = self.agent.get_response(messages, add_to_history=False, json_response=True)
        return response

    def get_memory(self, user_input):
        # Get the embeddings for the user input
        if user_input == "":
            return ""
        user_embeddings = self.agent.get_embeddings(user_input)

        # Query the vector memory for the most similar user input
        results = self.collection.query(
            query_embeddings=[user_embeddings],
            #query_texts=[user_input],
            n_results=6,
            #include=["metadatas, documents"]
        )

        # Build Memory text
        memory_text = f"START Memory Context: {len(results['metadatas'])}\n"
        if len(results['metadatas']) > 0:
            #breakpoint()
            # Iterate over the number of items in ids
            for metadata in results['metadatas'][0]:
                memory_text += f"Semantic Tags: {metadata['semantic_tags']}\n"
                memory_text += f"Emotional Tone: {metadata['emotional_tone']}\n"
                memory_text += f"Interaction Summary: {metadata['interaction_summary']}\n"
        memory_text += "END Memory Context\n"
        return memory_text

    def remember_conversation(self, user_input, agent_response):
        # Metadata
        # Analyze the conversation to extract metadata
        metadata = self.analyze_conversation(user_input, agent_response)
        # Extract the metadata from the response
        metadata_dict = json.loads(metadata)

        # Embeddings
        user_embeddings = self.agent.get_embeddings(user_input)
        agent_embeddings = self.agent.get_embeddings(agent_response)

        documents=[user_input, agent_response]
        embeddings=[user_embeddings, agent_embeddings]
        metadatas = [
            { "role": "user", **metadata_dict },
            { "role": "agent", **metadata_dict }
        ]
        if metadata_dict["interaction_sequence"] == "agent_response_first":
            document = [agent_response, user_input]
            embeddings = [agent_embeddings, user_embeddings]
            metadatas = [
                { "role": "agent", **metadata_dict },
                { "role": "user", **metadata_dict }
            ]

        # IDs: Generate a unique id using a SHA256 hash for the user_input and agent_response
        # Do not use chroma
        ids = [hashlib.sha256(user_input.encode()).hexdigest(), hashlib.sha256(agent_response.encode()).hexdigest()]

        # Add to vector memory
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
            # ids are genearted automatically by ChromaDB
        )
