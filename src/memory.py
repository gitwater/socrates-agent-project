# Import required libraries
import json
from datetime import datetime
import hashlib
import chromadb
from sql_database import SQLDatabase



# Short buffer of the most recent conversational messages
class MemoryShortTerm:
    def __init__(self, sql_db):
        self.sql_db = sql_db

    def process_utterance(self, speaker, utterance):
        self.sql_db.store_utterance(speaker, utterance)

    def retreive_utterances(self, num_entries=10):
        return self.sql_db.retreive_utterances(num_entries)

    def get_memory(self):
        utterances = self.retreive_utterances()
        memory_context = f"""
START Short Term Memory Context:
"""
        for utterance in utterances:
            memory_context += f"{utterance['created_at']}: {utterance['speaker']}: {utterance['utterance']}\n"
        memory_context += f"""
END Short Term Memory Context
"""
        return memory_context

# Episodic and Semantic Memory
class MemoryLongTerm:
    def __init__(self, name, memory_system, sql_db):
        self.sql_db = sql_db
        self.vector_db_client = chromadb.PersistentClient(path=f"./db/vector/{name}.db")
        self.episodic_collection = self.vector_db_client.get_or_create_collection(
            "long_term_episodic_memory",
            metadata={
                "description": "Contains summaries on conversation topics relating to personal experiences.",
                "created": str(datetime.now())
            }
        )
        self.semantic_collection = self.vector_db_client.get_or_create_collection(
            "long_term_episodic_memory",
            metadata={
                "description": "Contains summaries on conversation topics relating to factual, conceptual knowledge.",
                "created": str(datetime.now())
            }
        )
        # How many utterances that have been processed before checking for a new topic boundary
        self.ltm_boundary_check_threshold = 10
        ltm_state = self.sql_db.retreive_ltm_state()
        if ltm_state is None:
            self.sql_db.store_ltm_state(0, 1)

    def detect_topic_boundaries(self):
        ltm_state = self.sql_db.retreive_ltm_state()

        breakpoint()
        if ltm_state["boundary_check_counter"] < self.ltm_boundary_check_threshold:
            return

        # Analyze the conversation to detect topic boundaries by loading the last
        # N utterances from the database
        utterance_list = self.sql_db.retreive_utterances(self.ltm_boundary_check_threshold*ltm_state["boundary_check_counter"])
        breakpoint()
        # Analyze the conversation to detect topic boundaries
        # If detected analyze the conversation to extract metadata for episodic and semantic memory
        prompt = f"""
System/Developer Prompt:

You are a conversation analyst that identifies changes in topic.
You will receive a list of utterances in chronological order.
Each utterance includes:
- "utterance_id"
- "speaker" (e.g. user or agent)
- "text"

Your task:
1. Detect where (if at all) the conversation shifts from one topic to another.
2. Output these topic segments as an array of objects. Each object should include:
   - "topic_name": A brief label of the topic being discussed.
   - "start_utterance_id": The ID of the first utterance that introduces this topic.
   - "end_utterance_id": The ID of the last utterance before the topic shifts again (or the end of the conversation).
   - Only incldue topics that have distinct boundaries, meaning a detected topic is the one precedeing the last topic. There must be at least two topics detected.
   - Optional metadata, e.g.:
     - "confidence_score" (0 to 1) indicating how confident you are in the topic change.
     - "reason_for_boundary" (a short explanation for why you believe this boundary exists).

3. Output the final result as valid JSON. Use the following structure:

{{

    "topic_segments": [
        {{
            "topic_name": "...",
            "start_utterance_id": "...",
            "end_utterance_id": "...",
            "confidence_score": ...,
            "reason_for_boundary": "..."
        }},
        ...
    ]
}}
4. Do not include additional commentary outside the JSON.

Below is the conversation:
{json.dumps(utterance_list)}
"""
        messages = [
            {
                "role": "system",
                "content": prompt
            }
        ]
        response = self.memory_system.agent.get_response(messages, add_to_history=False, json_response=True)
        # If no topic boundaries are detected, increase the boundary_group_counter and reset bounadary_check_counter
        if response["topic_segments"] == []:
            self.sql_db.store_ltm_state(0, ltm_state["boundary_group_counter"]+1)
            return


        # Store the topic boundaries in the database
        for topic_segment in response["topic_segments"]:
            self.sql_db.store_topic_boundary(topic_segment["topic_name"], topic_segment["start_utterance_id"], topic_segment["end_utterance_id"])

        # Analyze topic conversation
        prompt = f"""System/Developer Prompt:

You are an expert analyst who compresses and summarizes entire topic conversations into a single JSON object that captures both episodic and semantic information. The conversation you receive is a set of utterances (speaker + text) that belong to one topic (already segmented). Your output must be short and token-efficient, yet contain enough detail to be useful for memory-based lookups.

### Instructions:

1. **Analyze the conversation** as a whole. Do NOT produce an array entry for each utterance.

2. **Combine Episodic and Semantic Context** into a single, succinct analysis:
   - Episodic Context (i.e., who said what, key moments, time or sequence references).
   - Semantic Context (i.e., main themes, entities, sentiment, short summary).

3. **Include Partial or Selective Quotes** from the conversation:
   - Only the **most relevant or representative** excerpts, to preserve context.
   - Keep total length short. Avoid copying the entire conversation verbatim.

4. **Output Format**: Return exactly one JSON object with at least these fields:

{
    "topic_id": "...", // The ID or label of this topic
    "episodic_summary": "...", // High-level recounting of key events (chronological or logical flow)
    "semantic_summary": "...", // Main ideas, themes, or discussion points
    "selected_quotes": [ // minimal set of short quotes (1-2 sentences each) that provide context
        "...", "..."
    ],
    "named_entities": [ ... ], // People, places, organizations mentioned
    "overall_sentiment": "...", // e.g. "positive", "negative", or "neutral"
    "topics_covered": [ ... ], // Additional subtopics or categories, if relevant
    "confidence_notes": "..." // (optional) notes on reliability or limitations
}

5. **Write Valid JSON** without extra commentary, explanations, or disclaimers.
   Do not generate an array of utterances; compress everything into a single, consolidated response.

6. **Token Efficiency**:
- Use concise language.
- Omit details that are not truly important.

7. **Conversation (for analysis)**:
{json.dumps(utterance_list)}

### End Prompt.

"""
        # Detect the Episodic and Semantic contexts from the conversation
        # Create Embeddings for the Epidosid and Semantic contexts
        # Store in the respective collections
        breakpoint()

    def process_utterance(self, speaker, utterance):
        # Detect Topic Boundaries
        # If detected analyze the conversation to extract metadata for episodic and semantic memory
        #    - Analysis should produce a synopis or summary, but retain enough original conversation text
        #      to provide context for the summary
        #    - Extract metadata for the episodic and semantic memory
        pass

# Synthesizes or abstracts from other memory stores to form a higher-level
# “sense” or “gut feeling” about the conversation or user
class MemoryIntuition:
    pass

# Tracks user’s personality (traits, preferences, emotional states) as well as
# the agent’s own stylistic or persona-driven attributes
class MemoryPersonality:
    pass

# Store user’s explicit goals or tasks the agent must address, as well as
# agent’s current objectives.
class MemoryTasks:
    pass


class MemorySemanticRetrieval:
    def __init__(self, name):
        self.vector_db_client = chromadb.PersistentClient(path=f"./db/vector/{name}.db")
        self._collection = self.vector_db_client.get_or_create_collection(
            "agent_memory",
            metadata={
                "description": "A collection of embeddings for user inputs and agent responses.",
                "created": str(datetime.now())
            }
        )
        self.topic_collection = self.vector_db_client.get_or_create_collection(
            "agent_memory",
            metadata={
                "description": "A collection of embeddings for user inputs and agent responses.",
                "created": str(datetime.now())
            }
        )

    def store_memory(self, user_input, agent_response):
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

    # def generate_embeddings(self, user_input, agent_response):
    #     # Generate embeddings for the user input and agent response
    #     embeddings = self.agent.get_response([{"role": "system", "content": user_input}, {"role": "system", "content": agent_response}], json_response=True)
    #     return embeddings

class MemoryRelationshipRetrieval:
    def __init__(self):
        pass

class MemoryKeyValueRetrieval:
    def __init__(self):
        pass

class MemoryKeywordRetrieval:
    def __init__(self):
        pass

# Agent Memory System
# Stores information about the user input and agent response intuitively using
# Semantic, Relationship, KeyValue, and Keyword retrieval methods
#
# The agent system uses the AgentMemory by sending it every user input and agent
# response and the AgentMemory class will analyze and determine the best methods
# for storing the information for future recall.
#
# The Agent system does not need to know the details of how the memory is stored.
# The Agent system will simply call store_memory and retrieve_memory methods.
#
# Retreived memory must be placed into the agent's context when generating a
# a response.
class AgentMemory:
    def __init__(self, persona_config, agent):
        persona_name = persona_config['persona']['name'].lower()
        self.size_threshold = 100
        self.agent = agent
        #self.semantic_memory = MemorySemanticRetrieval(persona_name)
        self.sql_database = SQLDatabase(persona_config)
        self.short_term_memory = MemoryShortTerm(self.sql_database)
        self.long_term_memory = MemoryLongTerm(persona_name, self, self.sql_database)
        #self.intuitive_memory = MemoryIntuition(persona_name, self.sql_database)
        #self.personality_memory = MemoryPersonality(self.sql_database)


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
        memory_context = ""

        memory_context += self.short_term_memory.get_memory()
        return memory_context
        breakpoint()
        memory_context += self.long_term_memory.get_memory(user_input)

        # user_embeddings = self.agent.get_embeddings(user_input)

        # # Query the vector memory for the most similar user input
        # results = self.collection.query(
        #     query_embeddings=[user_embeddings],
        #     #query_texts=[user_input],
        #     n_results=6,
        #     #include=["metadatas, documents"]
        # )

        # # Build Memory text
        # memory_text = f"START Memory Context: {len(results['metadatas'])}\n"
        # if len(results['metadatas']) > 0:
        #     #breakpoint()
        #     # Iterate over the number of items in ids
        #     for metadata in results['metadatas'][0]:
        #         memory_text += f"Semantic Tags: {metadata['semantic_tags']}\n"
        #         memory_text += f"Emotional Tone: {metadata['emotional_tone']}\n"
        #         memory_text += f"Interaction Summary: {metadata['interaction_summary']}\n"
        # memory_text += "END Memory Context\n"
        # return memory_text
        return memory_context

    def store_utterance(self, speaker, utterance):
        self.short_term_memory.process_utterance(speaker, utterance)
        #self.long_term_memory.process_utterance(speaker, utterance)
        #self.intuitive_memory.process_utterance(speaker, utterance)
        #self.personality_memory.process_utterance(speaker, utterance)

    def remember_conversation(self, user_input, agent_response):
        self.semantic_memory.store_memory(user_input, agent_response)

