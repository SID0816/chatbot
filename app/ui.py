import streamlit as st
import requests

# Define the FastAPI backend URL
BACKEND_URL = "http://127.0.0.1:8000/chat"

# Streamlit App Title
st.title("Welcome To Chatbot where you can know about WEATHER, JOKES & NEWS")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Function to send a message to the FastAPI backend
def send_message(message):
    try:
        response = requests.post(
            BACKEND_URL,
            json={"message": message}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.text}")
            return {"message": "Sorry, something went wrong."}
    except Exception as e:
        st.error(f"Exception: {str(e)}")
        return {"message": f"Error: {str(e)}"}

# Function to display jokes
def display_joke(response_data):
    try:
        # Check if 'webhook_responses' exists and contains jokes
        if "data" in response_data and "webhook_responses" in response_data["data"]:
            for response in response_data["data"]["webhook_responses"]:
                if "jokes" in response and isinstance(response["jokes"], list) and len(response["jokes"]) > 0:
                    for joke in response["jokes"]:
                        joke_text = joke.get("joke", "No joke available.")
                        st.markdown(f"> {joke_text}")
                        st.markdown("---")  # Separator for readability
                    return  # Exit after displaying the first valid joke
        # Fallback if no jokes are found
        st.write("Sorry, no jokes are available at the moment.")
    except Exception as e:
        st.error(f"Error parsing joke data: {str(e)}")
        st.write("Sorry, no jokes are available at the moment.")

# Function to display weather
def display_weather(response_data):
    try:
        if "data" in response_data and "webhook_responses" in response_data["data"]:
            weather_data = response_data["data"]["webhook_responses"][0]
            if "main" in weather_data and "weather" in weather_data:
                temp = weather_data["main"].get("temp", "N/A")
                temp_min = weather_data["main"].get("temp_min", "N/A")
                temp_max = weather_data["main"].get("temp_max", "N/A")
                description = weather_data["weather"][0].get("description", "N/A").capitalize()
                humidity = weather_data["main"].get("humidity", "N/A")
                wind_speed = weather_data["wind"].get("speed", "N/A")

                st.markdown(f"**Temperature:** {temp}°K")
                st.markdown(f"**Min Temperature:** {temp_min}°K")
                st.markdown(f"**Max Temperature:** {temp_max}°K")
                st.markdown(f"**Description:** {description}")
                st.markdown(f"**Humidity:** {humidity}%")
                st.markdown(f"**Wind Speed:** {wind_speed} m/s")
                return
        st.write("Sorry, no weather data is available at the moment.")
    except Exception as e:
        st.error(f"Error parsing weather data: {str(e)}")
        st.write("Sorry, no weather data is available at the moment.")

# Function to display news
def display_news(response_data):
    try:
        if "data" in response_data and "webhook_responses" in response_data["data"]:
            articles = response_data["data"]["webhook_responses"][0].get("articles", [])
            if articles:
                st.write("📰 Top 3 News Articles:")
                for article in articles[:3]:  # Limit to top 3 articles
                    title = article.get("title", "No Title Available")
                    description = article.get("description", "No Description Available")
                    url = article.get("url", "#")
                    source_name = article.get("source", {}).get("name", "Unknown Source")

                    st.markdown(f"#### [{title}]({url})")
                    st.caption(f"Source: {source_name}")
                    st.write(description)
                    st.markdown("---")  # Separator for readability
                return
        st.write("Sorry, no news articles are available at the moment.")
    except Exception as e:
        st.error(f"Error parsing news data: {str(e)}")
        st.write("Sorry, no news articles are available at the moment.")

# Display chat history
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(chat["user"])
    with st.chat_message("assistant"):
        # Format bot response based on content
        if "weather" in chat["bot"].lower():
            st.write("🌤️ Weather Information:")
            display_weather(chat["bot_data"])
        elif "joke" in chat["bot"].lower():
            st.write("😄 Here's a joke for you:")
            display_joke(chat["bot_data"])
        elif "news" in chat["bot"].lower():
            display_news(chat["bot_data"])

# Quick action buttons
st.subheader("Quick Actions")
if st.button("Check Weather of Bhaktapur"):
    user_input = "What's the weather in Bhaktapur"
    st.session_state.chat_history.append({"user": user_input, "bot": "", "bot_data": {}})
    bot_response = send_message(user_input)
    st.session_state.chat_history[-1]["bot"] = bot_response.get("message", "No response from bot.")
    st.session_state.chat_history[-1]["bot_data"] = bot_response
    st.rerun()

if st.button("Get a Technical Joke"):
    user_input = "Tell me an IT joke."
    st.session_state.chat_history.append({"user": user_input, "bot": "", "bot_data": {}})
    bot_response = send_message(user_input)
    st.session_state.chat_history[-1]["bot"] = bot_response.get("message", "No response from bot.")
    st.session_state.chat_history[-1]["bot_data"] = bot_response
    st.rerun()

if st.button("News about Kathmandu"):
    user_input = "News about Kathmandu"
    st.session_state.chat_history.append({"user": user_input, "bot": "", "bot_data": {}})
    bot_response = send_message(user_input)
    st.session_state.chat_history[-1]["bot"] = bot_response.get("message", "No response from bot.")
    st.session_state.chat_history[-1]["bot_data"] = bot_response
    st.rerun()

# User input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"user": user_input, "bot": "", "bot_data": {}})

    # Send the message to the backend
    bot_response = send_message(user_input)

    # Update the chat history with the bot's response
    st.session_state.chat_history[-1]["bot"] = bot_response.get("message", "No response from bot.")
    st.session_state.chat_history[-1]["bot_data"] = bot_response

    # Rerun the app to refresh the chat display
    st.rerun()