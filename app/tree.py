# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import requests
import re
from pathlib import Path

TRAINING_DATA_FILE = Path("training_data.json")

if not TRAINING_DATA_FILE.exists():
    TRAINING_DATA_FILE.write_text("[]")


class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    data: Optional[Dict] = None

class DataPair(BaseModel):
    query: str
    node_id: str

class DecisionTreeNode:
    def __init__(self, node_data: dict):
        self.id = node_data['id']
        self.label = node_data['label']
        self.message = node_data['message']
        self.conditions = node_data.get('conditions', [])
        self.actions = node_data.get('actions', [])
        self.children = [DecisionTreeNode(child) for child in node_data.get('children', [])]

class ChatBot:
    def __init__(self):
        try:
            self.model = SentenceTransformer("C:\\Users\\Legion\\OneDrive\\Desktop\\data\\fine_tuned_model")
            print("Loaded fine-tuned model.")
        except Exception as e:
            print(f"Could not load fine-tuned model, loading default. Error: {e}")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tree = None
        self.webhooks = {}
        self.load_data()
    
    def load_data(self):
        # Load tree data
        with open('C:\\Users\\Legion\\OneDrive\\Desktop\\data\\venv\\app\\tree_data.json', 'r') as f:
            tree_data = json.load(f)
        self.tree = DecisionTreeNode(tree_data['treeStructure'])
        
        # Load webhook configurations
        with open('C:\\Users\\Legion\\OneDrive\\Desktop\\data\\venv\\app\\webhook_config.json', 'r') as f:
            webhook_data = json.load(f)
            self.webhooks = {hook['key']: hook for hook in webhook_data}
    

    ##here the data is  collected from function process_message() for the similarity check and to assign the closest node
    def find_closest_node(self, query: str, current_node=None, min_similarity=0.3):
        if current_node is None:
            current_node = self.tree
            
        # Get query embedding
        query_embedding = self.model.encode([query])[0]
        
        best_node = current_node
        best_similarity = -1
        
        # Check current node
        if current_node.conditions:
            condition_text = " ".join([cond['value'] for cond in current_node.conditions])
            node_embedding = self.model.encode([condition_text])[0]

            ##here for the similarity check we use cosine_similarity() because of :
            # 1)Focus on Orientation, Not Magnitude
            ## 2) Scale Invariance
            # 3) Computational Efficiency
            similarity = cosine_similarity([query_embedding], [node_embedding])[0][0]
            best_similarity = similarity
        
        # Check children
        for child in current_node.children:
            child_node, child_similarity = self.find_closest_node(query, child)
            if child_similarity > best_similarity:
                best_node = child_node
                best_similarity = child_similarity
        
        print(f" best node{best_node} best similarity{best_similarity}")
        return best_node, best_similarity
    
    import re
    def extract_parameters(self, query: str, node: DecisionTreeNode) -> dict:
        params = {}
        query = query.lower()
        print(f"params {query}")
        
        # Extract parameters based on node type
        if any(cond['value'] == 'weather' for cond in node.conditions):
            # print("weather")
            
            

            # Normalize the query first, keeping hyphens and apostrophes
            clean_query = re.sub(r"[^\w\s'-]", '', query.lower()).strip()
            clean_query = re.sub(r'\s+', ' ', clean_query)  # Collapse multiple spaces
            
            # Split into parts using all occurrences of 'weather'
            parts = re.split(r'\bweather\b', clean_query, flags=re.IGNORECASE)
            
            city = None
            prepositions = {'in', 'of', 'for', 'at', 'near', 'around'}
            
            # Check parts in reverse order to prioritize segments after the last 'weather'
            for part in reversed(parts):
                part = part.strip()
                if not part:
                    continue
                tokens = part.split()
                # Look for the first preposition to capture the city following it
                for i, token in enumerate(tokens):
                    if token in prepositions:
                        tokens = tokens[i+1:]
                        break  # Take remaining tokens after the first preposition
                if tokens:
                    city = ' '.join(tokens).title()
                    break  # Use the first valid city found
            
            if city:
                params['city'] = city

        #fetching the crypto data if the node is crypto
        elif any(cond['value'] == 'crypto' for cond in node.conditions):
            print("crypto")
            if "of" in query:
                params['crypto_symbol'] = query.split('of')[-1].strip().title()

            
        
        # Add news parameters extraction for fetching the news from the API's if the node is news
        if any(cond['value'] == 'news' for cond in node.conditions):
            print("news")
            
            # Preprocess query to remove common leading commands (e.g., "show me the", "display")
            command_pattern = re.compile(
                r'^\s*(?:show\s+me\s+the|show|display|give\s+me|tell\s+me)\s*', 
                re.IGNORECASE
            )
            stripped_query = command_pattern.sub('', query).strip()
            
            # Updated news_pattern to capture variations
            news_pattern = re.compile(
                r'(?:news|headlines)\s+(?:about|on|regarding|of)\s+([\w\s]+)|'  # "news about X"
                r'([\w\s]+)\s+(?:news|headlines)|'                              # "X news"
                r'(?:news|headlines)\s+([\w\s]+?)(?=\s*(?:in|from)|$)',         # "news X [in/from...]"
                re.IGNORECASE
            )
            
            # City pattern (unchanged)
            city_pattern = re.compile(r'\b(?:in|from)\s+([\w\s]+?)(?=\s|$)', re.IGNORECASE)
            
            # Extract keyword and city from the stripped query
            keyword_match = news_pattern.search(stripped_query)
            city_match = city_pattern.search(stripped_query)
            
            # Get keyword from the first valid group
            keyword = next((g.strip() for g in keyword_match.groups() if g), None) if keyword_match else None
            
            # Get city from city pattern
            city = city_match.group(1).strip() if city_match else None
            
            # Update parameters
            if keyword:
                params['keyword'] = keyword.title()
            if city:
                params['city'] = city.title()
            #the condition is for joke node
        elif any(cond['value'] == 'joke' for cond in node.conditions):
            print("Joke request detected")
            
            # Create pattern to match various joke request formats
            joke_pattern = re.compile(
                r'(?:joke|jokes)\s+(?:about|on|related to|of|for)\s+([\w\s]+)|'  # "joke about cats"
                r'([\w\s]+)\s+(?:joke|jokes)|'  # "funny joke" or "animal jokes"
                r'(?:tell me a?|share a?)\s+([\w\s]+)\s+joke',  # "tell me a programmer joke"
                re.IGNORECASE
            )
            
            # Search for patterns in the query
            match = joke_pattern.search(query)
            
            if match:
                # Extract first non-empty group (handles different pattern positions)
                keywords = next((g for g in match.groups() if g), None)
                if keywords:
                    # Clean and format the keywords
                    params['keywords'] = keywords.strip().title()
                        
                    
          
        return params

    
    async def execute_webhook(self, webhook_key: str, parameters: Dict) -> dict:
        if webhook_key not in self.webhooks:
            raise ValueError(f"Unknown webhook: {webhook_key}")
            
        webhook = self.webhooks[webhook_key]
        url = webhook['url']
        payload = webhook['payload'].copy()
        params = webhook.get('params', {}).copy()
        
        # Replace parameters in payload
        for key, value in parameters.items():
            for payload_key, payload_value in payload.items():
                if isinstance(payload_value, str):
                    payload[payload_key] = payload_value.replace(
                        f"{{{key}}}", str(value)
                    )
        for param_key, param_value in params.items():
                if isinstance(param_value, str):
                    params[param_key] = param_value.replace(
                        f"{{{key}}}", str(value)
                    )
        response = requests.get(
            url,
            # json=payload,
            params=params,
            headers=webhook['headers']
        )
        print(f"Payload ")

        
        return response.json()
    

    # Here the data is received from function chat_endpoint() and the similarity is checked with the data of dataset and
    #  node is assigned  with the function find_closest_node(message)
    #if similarity is more than 0.3 then the node is assigned else need to be repharse
    async def process_message(self, message: str) -> ChatResponse:
        # Find closest matching node
        node, similarity = self.find_closest_node(message)
        
        if similarity < 0.3:
            return ChatResponse(
                message="I'm not sure how to help with that. Could you please rephrase?"
            )
        
        # After the similarity check, Extract parameters is called and the message and the assigned node is passed to the extract parameter function 
        parameters = self.extract_parameters(message, node)
        
        # Execute webhooks if any
        webhook_responses = []
        for action in node.actions:
            if action['type'] == 'trigger_webhook':
                try:

                    webhook_key = action['data']['key']
                    response = await self.execute_webhook(webhook_key, parameters)
                    print(response)
                    webhook_responses.append(response)
                except Exception as e:
                    print(f"Webhook error: {str(e)}")
        
        # Format response message
        response_message = node.message
        for key, value in parameters.items():
            response_message = response_message.replace(f"{{{key}}}", str(value))
        
        return ChatResponse(
            message=response_message,
            data={'webhook_responses': webhook_responses} if webhook_responses else None
        )

# Create FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot
chatbot = ChatBot()

#Here the message is collected from the frontend on end-point "/chat" and a request is sent
# to function process_message() along withe the message

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = await chatbot.process_message(request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#the collect_data() get executed when the data is to be trained and from frontend the end point for it will be (/collect-data)
@app.post("/collect-data")
async def collect_data(data_pair: DataPair):
    try:
        # Read existing training data
        with TRAINING_DATA_FILE.open("r") as f:
            existing_data = json.load(f)
        
        # Append the new data pair
        existing_data.append(data_pair.dict())
        
        # Write the updated data back to the file
        with TRAINING_DATA_FILE.open("w") as f:
            json.dump(existing_data, f, indent=4)
        
        return {"status": "Data collected successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))