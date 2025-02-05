Multi-Purpose Chatbot
A versatile chatbot application that provides real-time information about weather, news, and jokes using natural language processing and multiple API integrations.
Features

Weather Information: Get current weather conditions for any city
News Updates: Fetch latest news articles based on keywords or topics
Jokes: Access a variety of jokes based on different categories
Interactive UI: Built with Streamlit for a seamless user experience

And then for technical stack we use:
Technical Stack

Backend: FastAPI
Frontend: Streamlit
NLP: Sentence Transformers (all-MiniLM-L6-v2)
APIs Integration:
OpenWeatherMap API for weather data (its a free api which is used for fetching the weather data )
NewsAPI for news articles(it is for fetching  news and its a free api) 
HumorAPI for jokes(The HumorAPI provide the free API which is used for fetching the joke according to the type of joke but this API has limit of 10 joke a day)

The Project structure for this project is:


Project Structure
  chatbot/
├── app/
│   ├── __pycache__/
│   ├── tree.py            # Main backend logic
│   ├── tree_data.json     # Decision tree structure
│   ├── webhook_config.json # API configurations
│   └── ui.py              # Streamlit frontend
├── training_data.json     # Training data for NLP
└── README.md

Setup ,Installation and Dependencies for the project: 
1) pip install fastapi uvicorn streamlit sentence-transformers scikit-learn requests
2)Set up API keys in webhook_config.json:
    OpenWeatherMap API key
    NewsAPI key
    HumorAPI key

For starting  the backend server:
uvicorn app.tree:app --reload --host 0.0.0.0 --port 8000
For starting the streamlit frontend server:
streamlit run app/ui.py

How It Works

Natural Language Processing:
Uses sentence transformers to understand user intent
Matches user queries to the most relevant service using cosine similarity
Minimum similarity threshold of 0.3 for valid matches


Decision Tree:
Structured response system based on user intent
Handles multiple types of queries (weather, news, jokes)
Parameter extraction for specific queries


API Integration:
Webhook system for external API calls(auto fetching is not available)
Configurable endpoints and parameters
Error handling and response formatting


Usage Examples

Weather Query:
"What's the weather in Bhaktapur?"
"weather kathmandu"
"weather of london"
"temperature of brazil"


News Query:
"Show me news about Kathmandu"
"headlines about brazil"
"news nepal"
"nepal news"

Joke Query:
"Tell me an IT joke"
"child joke"
"tell me a funny joke"


Future Improvements

Add more API integrations for other opertaion and chats too
Implement user authentication for individual user
Add conversation history persistence for traing the data
Implement more interactive UI elements for user friendly
Add support for multiple languages 
