# app.py
import os
import uuid
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# Now import the bot logic which depends on the loaded variables
# Replace with this
from bot_logic import BotLogic, logger, GOOGLE_MAPS_API_KEY
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Initialize the bot logic once when the application starts
bot_logic = BotLogic()
logger.info("BotLogic initialized for the web application.")

# Replace the function with this
@app.route('/')
def index():
    """Renders the main page. A unique user_id is generated for the session."""
    user_id = str(uuid.uuid4())
    # Pass the API key to the template so JavaScript can use it
    return render_template('index.html', user_id=user_id, GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)

@app.route('/ask', methods=['POST'])
def ask():
    """API endpoint to handle all user questions from the frontend."""
    data = request.get_json()
    user_id = data.get('user_id')
    user_input = data.get('question', '').strip()
    user_name = 'Visitor' # You can enhance this if you have user login

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    # The first message from the frontend will have an empty 'question'.
    # Our bot logic's process_user_input is already designed to handle this
    # by checking if the user_id is new and returning the welcome message.
    input_type = 'start_command' if user_input == "" else 'text'

    # Get the full response dictionary from the bot logic
    response_dict = bot_logic.process_user_input(
        user_id=user_id,
        input_type=input_type,
        data=user_input,
        user_name=user_name
    )

    # Return the entire dictionary (text, photos, buttons) to the frontend
    return jsonify(response_dict)

if __name__ == '__main__':
    # Use '0.0.0.0' to make it accessible on your network
    app.run(host='0.0.0.0', port=5000, debug=True)