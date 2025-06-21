# bot_logic.py
# -*- coding: utf-8 -*-

import os
import logging
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict
from urllib.parse import quote_plus

load_dotenv()

# --- NEW: Define the base directory of the script ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Configuration (loaded from environment) ---
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_SHEET_LOCAL_INFO_NAME = os.getenv("GOOGLE_SHEET_LOCAL_INFO_NAME", "Tiruchendur_Local_Info")
GOOGLE_SHEET_PARKING_LOTS_INFO_NAME = os.getenv("GOOGLE_SHEET_PARKING_LOTS_INFO", "Tiruchendur_Parking_Lots_Info")
GOOGLE_SHEET_PARKING_STATUS_LIVE_NAME = os.getenv("GOOGLE_SHEET_PARKING_STATUS_LIVE", "Tiruchendur_Parking_Status_Live")

# --- MODIFIED: Use the BASE_DIR to create an absolute path ---
credentials_filename = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
GOOGLE_SHEETS_CREDENTIALS_FILE = os.path.join(BASE_DIR, credentials_filename)

# Centralized logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- All Constants and Menu Texts ---
### --- MODIFIED SECTION: Added Feedback Link Constant --- ###
GOOGLE_FORM_FEEDBACK_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSempmuc0_3KkCX3JK3wCZTod51Zw3o8ZkG78kQpcMTmVTGsPg/viewform?usp=header"

### --- MODIFIED SECTION: Reordered Menu and Added Feedback Text --- ###
MENU_TEXTS = {
    "en": {
        "welcome_tiruchendur": "Vanakkam {user_name}! I'm your Tiruchendur Assistant. 😊",
        "select_language_prompt": "Please select your preferred language.",
        "invalid_language_selection": "Invalid selection. Please click one of the buttons.",
        "language_selected": "You have selected {language_name}.",
        "main_menu_prompt": "Tiruchendur Main Menu - Type the number for your choice:",
        "option_parking_availability": "1. 🅿️ Live Parking Availability",
        "option_temple_info": "2. Murugan Temple Info",
        "option_help_centres": "3. 'May I Help You?' Centres",
        "option_first_aid": "4. First Aid Stations",
        "option_temp_bus_stands": "5. Temporary Bus Stands",
        "option_toilets_temple": "6. Toilets Near Temple",
        "option_annadhanam": "7. Annadhanam Details",
        "option_emergency_contacts": "8. Emergency Helpline Numbers",
        "option_nearby_facilities": "9. Search Nearby (ATM, Hotel etc.)",
        "option_change_language": "10. Change Language",
        "option_feedback": "11. Feedback",
        "option_end_conversation_text": "\nType 'X' to End Conversation.",
        "feedback_response": "Thank you for helping us improve! 🙏\nPlease share your valuable feedback using the link below:\n\n<a href=\"{feedback_link}\" target=\"_blank\">Open Feedback Form</a>",
        "invalid_menu_option": "Invalid option. Please type a number from the menu or 'X' to end.",
        "temple_info_menu_prompt": "Murugan Temple Information - Type the number:",
        "temple_timings_menu_item": "1. Nada Open/Close & Pooja Times",
        "temple_dress_code_menu_item": "2. Dress Code",
        "temple_seva_tickets_menu_item": "3. Seva & Ticket Details",
        "option_go_back_text": "0. Go Back to Main Menu",
        "freestyle_query_prompt": "Okay, what would you like to search for nearby (e.g., 'ATM', 'hotels', 'restaurants')?",
        "emergency_contacts_info": "Tiruchendur Emergency Contacts:\nPolice: 100\nFire: 101\nAmbulance: 108\nTemple Office: [Insert Number]",
        "local_info_title_format": "--- {category_name} in Tiruchendur ---",
        "local_info_item_format": "\n➡️ {ItemName}\n📍 Location: {LocationLink}\n📝 Notes: {Notes}",
        "local_info_item_format_bus": "\n➡️ {ItemName}\n🛣️ Route: {RouteInfo}\n📍 Location: {LocationLink}\n🕒 Active: {ActiveDuring}\n📝 Notes: {Notes}",
        "local_info_item_format_parking": "\n🅿️ {ItemName}\n🛣️ Access from: {RouteDirection}\n📍 Location: {LocationLink}\n🕒 Operation: {OperationDuring}\n📝 Notes: {Notes}",
        "local_info_item_format_annadhanam": "\n🍚 Annadhanam at: {ItemName}\n🗺️ Map: {MapsLink}\n🕒 Timings: {Timings}\n📞 Contact: {ContactInfo}\n📝 Notes: {Notes}",
        "no_local_info_found": "No information currently available for {category_name} in Tiruchendur.",
        "fetching_data_error": "Sorry, I couldn't fetch the latest information.",
        "parking_route_prompt": "Which route are you primarily arriving from for parking?\n(Type the number or name)\n1. Tirunelveli Route\n2. Thoothukudi Route\n3. Nagercoil Route\n4. Other/Already in Tiruchendur",
        "parking_for_route_title": "--- Parking Options for {RouteName} Route ---",
        "parking_info_title": "--- Tiruchendur Parking Availability ---",
        "no_parking_available": "Sorry, no suitable parking spots are currently available or all are nearly full.",
        "parking_lot_details_format": "\n🅿️ {ParkingName}\n🗺️ Directions: {MapsLink}\n📍 Approx. {Distance:.1f} km away\n📦 Availability: {Availability}/{TotalCapacity} slots ({PercentageFull:.0f}% full)",
        "overall_parking_map_link_text": "\n\n<a href=\"{overall_map_url}\" data-embed=\"true\">🗺️ View All Parking Lots for the {RouteName} Route</a>",
        "temple_timings_details": "Tiruchendur Murugan Temple General Timings:\nTimings can vary on festival days. It's best to check locally.",
        "temple_dress_code_details": "Dress Code: Traditional Indian attire is recommended. Men: Dhoti/Pants. Women: Saree/Salwar Kameez.",
        "goodbye_message": "Nandri! Vanakkam!",
        "nearest_place_intro": "📍 Here are results for {place_type_display_name} in the Tiruchendur area:",
        "place_details_maps": "\n{name}\nAddress: {address}\n🗺️ {maps_url}"
    },
    "ta": {
        "welcome_tiruchendur": "வணக்கம் {user_name}! நான் உங்கள் திருச்செந்தூர் வழிகாட்டி. 😊",
        "select_language_prompt": "விரும்பிய மொழியைத் தேர்ந்தெடுக்கவும்.",
        "invalid_language_selection": "தவறான தேர்வு. பொத்தான்களில் ஒன்றைக் கிளிக் செய்யவும்.",
        "language_selected": "நீங்கள் {language_name} மொழியைத் தேர்ந்தெடுத்துள்ளீர்கள்.",
        "main_menu_prompt": "திருச்செந்தூர் முதன்மை பட்டியல் - உங்கள் தேர்விற்கு எண்ணை உள்ளிடவும்:",
        "option_parking_availability": "1. 🅿️ நேரடி வாகன நிறுத்தம்",
        "option_temple_info": "2. முருகன் கோவில் தகவல்கள்",
        "option_help_centres": "3. 'உங்களுக்கு உதவலாமா?' மையங்கள்",
        "option_first_aid": "4. முதலுதவி நிலையங்கள்",
        "option_temp_bus_stands": "5. தற்காலிக பேருந்து நிலையங்கள்",
        "option_toilets_temple": "6. கோவிலுக்கு அருகிலுள்ள கழிப்பறைகள்",
        "option_annadhanam": "7. அன்னதானம் விவரங்கள்",
        "option_emergency_contacts": "8. அவசர உதவி எண்கள்",
        "option_nearby_facilities": "9. அருகில் தேடவும் (ஏடிஎம், ஹோட்டல் போன்றவை)",
        "option_change_language": "10. மொழி மாற்றவும்",
        "option_feedback": "11. பின்னூட்டம் (Feedback)",
        "option_end_conversation_text": "\nஉரையாடலை முடிக்க 'X' என தட்டச்சு செய்யவும்.",
        "feedback_response": "எங்கள் சேவையை மேம்படுத்த உதவியதற்கு நன்றி! 🙏\nகீழே உள்ள இணைப்பைப் பயன்படுத்தி உங்கள் மதிப்புமிக்க கருத்தைப் பகிரவும்:\n\n<a href=\"{feedback_link}\" target=\"_blank\">பின்னூட்டப் படிவத்தைத் திறக்கவும்</a>",
        "invalid_menu_option": "தவறான விருப்பம். மெனுவிலிருந்து ஒரு எண்ணை உள்ளிடவும் அல்லது 'X' என தட்டச்சு செய்யவும்.",
        "temple_info_menu_prompt": "முருகன் கோவில் தகவல்கள் - எண்ணை உள்ளிடவும்:",
        "temple_timings_menu_item": "1. நடை திறப்பு/சாத்துதல் & பூஜை நேரங்கள்",
        "temple_dress_code_menu_item": "2. ஆடை கட்டுப்பாடு",
        "temple_seva_tickets_menu_item": "3. சேவை & டிக்கெட் விவரங்கள்",
        "option_go_back_text": "0. முதன்மை பட்டியலுக்குத் திரும்பவும்",
        "freestyle_query_prompt": "சரி, நீங்கள் அருகில் எதைத் தேட விரும்புகிறீர்கள் (எ.கா., 'ஏடிஎம்', 'ஹோட்டல்கள்', 'உணவகங்கள்')?",
        "emergency_contacts_info": "திருச்செந்தூர் அவசர தொடர்புகள்:\nகாவல்: 100\nதீயணைப்பு: 101\nஆம்புலன்ஸ்: 108\nகோவில் அலுவலகம்: [எண்ணை உள்ளிடவும்]",
        "local_info_title_format": "--- திருச்செந்தூரில் {category_name} ---",
        "local_info_item_format": "\n➡️ {ItemName}\n📍 இடம்: {LocationLink}\n📝 குறிப்புகள்: {Notes}",
        "local_info_item_format_bus": "\n➡️ {ItemName}\n🛣️ வழித்தடம்: {RouteInfo}\n📍 இடம்: {LocationLink}\n🕒 நேரம்: {ActiveDuring}\n📝 குறிப்புகள்: {Notes}",
        "local_info_item_format_parking": "\n🅿️ {ItemName}\n🛣️ அணுகும் வழி: {RouteDirection}\n📍 இடம்: {LocationLink}\n🕒 நேரம்: {OperationDuring}\n📝 குறிப்புகள்: {Notes}",
        "local_info_item_format_annadhanam": "\n🍚 அன்னதானம்: {ItemName}\n🗺️ வரைபடம்: {MapsLink}\n🕒 நேரம்: {Timings}\n📞 தொடர்பு: {ContactInfo}\n📝 குறிப்புகள்: {Notes}",
        "no_local_info_found": "திருச்செந்தூரில் {category_name} பற்றிய தகவல்கள் தற்போது கிடைக்கவில்லை.",
        "fetching_data_error": "மன்னிக்கவும், சமீபத்திய தகவலைப் பெற முடியவில்லை.",
        "parking_route_prompt": "வாகன நிறுத்தத்திற்கு நீங்கள் எந்த வழியிலிருந்து வருகிறீர்கள்?\n(எண் அல்லது பெயரை உள்ளிடவும்)\n1. திருநெல்வேலி சாலை\n2. தூத்துக்குடி சாலை\n3. நாகர்கோவில் சாலை\n4. மற்றவை/ஏற்கனவே திருச்செந்தூரில்",
        "parking_for_route_title": "--- {RouteName} சாலைக்கான வாகன நிறுத்துமிடங்கள் ---",
        "parking_info_title": "--- திருச்செந்தூர் வாகன நிறுத்தம் ---",
        "no_parking_available": "மன்னிக்கவும், பொருத்தமான வாகன நிறுத்துமிடங்கள் எதுவும் கிடைக்கவில்லை அல்லது அனைத்தும் gần நிரம்பியுள்ளன.",
        "parking_lot_details_format": "\n🅿️ {ParkingName}\n🗺️ வழிகள்: {MapsLink}\n📍 சுமார் {Distance:.1f} கி.மீ. தொலைவில்\n📦 இடமிருப்பு: {Availability}/{TotalCapacity} ({PercentageFull:.0f}% நிரம்பியுள்ளது)",
        "overall_parking_map_link_text": "\n\n<a href=\"{overall_map_url}\" data-embed=\"true\">🗺️ {RouteName} வழிக்கான அனைத்து வாகன நிறுத்துமிடங்களையும் காண்க</a>",
        "temple_timings_details": "திருச்செந்தூர் முருகன் கோவில் பொது நேரங்கள்:\nபண்டிகை நாட்களில் நேரங்கள் மாறுபடலாம். உள்ளூரில் சரிபார்ப்பது நல்லது.",
        "temple_dress_code_details": "ஆடை கட்டுப்பாடு: பாரம்பரிய உடை பரிந்துரைக்கப்படுகிறது. ஆண்கள்: வேட்டி/பேண்ட். பெண்கள்: புடவை/சல்வார் கமீஸ்.",
        "goodbye_message": "நன்றி! வணக்கம்!",
        "nearest_place_intro": "📍 திருச்செந்தூர் பகுதியில் {place_type_display_name} தேடல் முடிவுகள்:",
        "place_details_maps": "\n{name}\nமுகவரி: {address}\n🗺️ {maps_url}"
    }
}
SUPPORTED_LANGUAGES = { "en": {"name": "English"}, "ta": {"name": "தமிழ் (Tamil)"} }
SHEET_HELP_CENTRES, SHEET_FIRST_AID, SHEET_TEMP_BUS_STANDS, SHEET_TOILETS, SHEET_DESIGNATED_PARKING_STATIC, SHEET_ANNADHANAM = "Help_Centres", "First_Aid_Stations", "Temp_Bus_Stands", "Toilets_Near_Temple", "Designated_Public_Parking", "Annadhanam_Details"

OVERALL_ROUTE_MY_MAPS = {
    "thoothukudi": "1RTKvzXANpeJXI5wsW28WGclXkO2T7kw",
    "tirunelveli": "1cROpQnVd_Jk7B6KPDyhreS98ek1GDrQ",
    "nagercoil": "17GYGNfx6r8bO7ORC7QfYgQHyF1gT2_4"
}

class BotLogic:
    def __init__(self):
        logger.info("Initializing BotLogic...")
        self.user_states = {}
        self.TIRUCHENDUR_COORDS = (8.4967, 78.1245)
        self.LOCAL_INFO_CACHE, self.LAST_LOCAL_INFO_FETCH_TIME = {}, {}
        self.PARKING_LOTS_INFO_CACHE, self.LAST_PARKING_LOTS_INFO_FETCH_TIME = [], 0
        self.PARKING_LIVE_STATUS_CACHE, self.LAST_PARKING_LIVE_STATUS_FETCH_TIME = {}, 0
        self.LIVE_DATA_CACHE_DURATION, self.LOCAL_INFO_CACHE_DURATION, self.STATIC_DATA_CACHE_DURATION = 120, 600, 1800
        self.PARKING_FULL_THRESHOLD_PERCENT = 70.0
        self._preload_data()

    def _preload_data(self):
        if not GOOGLE_MAPS_API_KEY:
            logger.warning("CRITICAL: GOOGLE_MAPS_API_KEY not found. Map features will fail.")
        if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
            logger.warning(f"'{GOOGLE_SHEETS_CREDENTIALS_FILE}' not found. Google Sheets features will be disabled.")
            return
            
        logger.info("Pre-loading all data from Google Sheets at startup...")
        all_sheets_to_fetch = [SHEET_HELP_CENTRES, SHEET_FIRST_AID, SHEET_TEMP_BUS_STANDS, SHEET_TOILETS, SHEET_DESIGNATED_PARKING_STATIC, SHEET_ANNADHANAM]
        for sheet in all_sheets_to_fetch:
            self.fetch_local_info_from_sheet(sheet, force_refresh=True)
        self.fetch_parking_lots_info(force_refresh=True)
        self.fetch_parking_live_status(force_refresh=True)
        logger.info("Pre-loading complete.")

    def _get_response_structure(self, text="", photos=None, buttons=None):
        return {"text": text, "photos": photos or [], "buttons": buttons or []}

    def process_user_input(self, user_id: str, input_type: str, data: Any, user_name: str = "User") -> Dict:
        if input_type == 'start_command' or user_id not in self.user_states:
            self.user_states[user_id] = {"lang": "en", "menu_level": "language_select"}
            return self._change_language(user_id, is_initial=True, user_name=user_name)
        
        state = self.user_states[user_id]
        
        if state.get("menu_level") == "language_select":
            lang_choice = str(data).strip().lower()
            if lang_choice in SUPPORTED_LANGUAGES:
                state['lang'], state['menu_level'] = lang_choice, 'main_menu'
                welcome_text = self.get_text(user_id, "language_selected", language_name=SUPPORTED_LANGUAGES[lang_choice]['name'])
                return self._get_response_structure(f"{welcome_text}\n\n{self._get_menu_text('main_menu', user_id)}")
            else:
                return self._change_language(user_id, user_name=user_name)

        text_input = str(data).strip()
        if text_input.lower() == 'x':
            lang = state.get("lang", "en")
            del self.user_states[user_id]
            return self._get_response_structure(self.get_text(lang, "goodbye_message"))

        handler = getattr(self, f"_handle_{state.get('menu_level', 'main_menu')}", self._handle_invalid_state)
        return handler(user_id, text_input)

    def _handle_invalid_state(self, user_id, text_input):
        self.user_states[user_id]["menu_level"] = "main_menu"
        return self._get_response_structure(f"{self.get_text(user_id, 'invalid_menu_option')}\n\n{self._get_menu_text('main_menu', user_id)}")

    ### --- MODIFIED SECTION: Updated menu actions and numbering --- ###
    def _handle_main_menu(self, user_id, choice):
        # Handle language change which is now option 10
        if choice == "10":
            return self._change_language(user_id)
            
        # New menu mapping
        menu_actions = {
            "1": ("parking_awaiting_route", None),
            "2": ("temple_info_menu", None),
            "3": (None, lambda: self._get_formatted_sheet_data(user_id, SHEET_HELP_CENTRES)),
            "4": (None, lambda: self._get_formatted_sheet_data(user_id, SHEET_FIRST_AID)),
            "5": (None, lambda: self._get_formatted_sheet_data(user_id, SHEET_TEMP_BUS_STANDS)),
            "6": (None, lambda: self._get_formatted_sheet_data(user_id, SHEET_TOILETS)),
            "7": (None, lambda: self._get_formatted_sheet_data(user_id, SHEET_ANNADHANAM)),
            "8": (None, lambda: self.get_text(user_id, "emergency_contacts_info")),
            "9": ("nearby_search", None),
            "11": (None, lambda: self.get_text(user_id, "feedback_response", feedback_link=GOOGLE_FORM_FEEDBACK_LINK)),
        }
        new_level, action = menu_actions.get(choice, (None, None))

        if new_level:
            self.user_states[user_id]["menu_level"] = new_level
            
            if new_level == "temple_info_menu":
                response_text = self._get_menu_text(new_level, user_id)
            else:
                prompt_map = {
                    "parking_awaiting_route": "parking_route_prompt", 
                    "nearby_search": "freestyle_query_prompt"
                }
                response_text = self.get_text(user_id, prompt_map[new_level])
            
            return self._get_response_structure(response_text)
        
        elif action:
            result = action()
            return self._get_response_structure(f"{result}\n\n{self._get_menu_text('main_menu', user_id)}")
        
        return self._handle_invalid_state(user_id, choice)

    def _handle_temple_info_menu(self, user_id, choice):
        if choice == "0": 
            self.user_states[user_id]["menu_level"] = "main_menu"
            return self._get_response_structure(self._get_menu_text("main_menu", user_id))
        
        text_key = {"1": "temple_timings_details", "2": "temple_dress_code_details"}.get(choice, "invalid_menu_option")
        text = self.get_text(user_id, text_key)
        return self._get_response_structure(f"{text}\n\n{self._get_menu_text('temple_info_menu', user_id)}")

    def _handle_parking_awaiting_route(self, user_id, text_input):
        self.user_states[user_id]["menu_level"] = "main_menu"
        choice = text_input.lower()
        route_pref = "any"
        if "1" in choice or "tirunelveli" in choice: route_pref = "tirunelveli"
        elif "2" in choice or "thoothukudi" in choice: route_pref = "thoothukudi"
        elif "3" in choice or "nagercoil" in choice: route_pref = "nagercoil"
        parking_reply = self.find_available_parking(user_id=user_id, route_preference=route_pref)
        return self._get_response_structure(f"{parking_reply}\n\n{self._get_menu_text('main_menu', user_id)}")

    def _handle_nearby_search(self, user_id, text_input):
        self.user_states[user_id]["menu_level"] = "main_menu"
        search_reply = self.find_nearby_place(text_input, user_id=user_id)
        return self._get_response_structure(f"{search_reply}\n\n{self._get_menu_text('main_menu', user_id)}")

    def _change_language(self, user_id, is_initial=False, user_name="User"):
        self.user_states[user_id]['menu_level'] = 'language_select'
        text = (self.get_text("en", "welcome_tiruchendur", user_name=user_name) + "\n") if is_initial else ""
        text += self.get_text("en", "select_language_prompt")
        buttons = [{"text": d["name"], "payload": c} for c, d in SUPPORTED_LANGUAGES.items()]
        return self._get_response_structure(text=text, buttons=buttons)

    def get_text(self, lang_code, key, **kwargs):
        lang = lang_code if lang_code in SUPPORTED_LANGUAGES else self.user_states.get(lang_code, {}).get("lang", "en")
        template_string = MENU_TEXTS.get(lang, MENU_TEXTS["en"]).get(key, f"<{key}_MISSING>")
        if kwargs:
            try: return template_string.format(**kwargs)
            except KeyError as e:
                logger.error(f"Formatting failed for key '{key}'. Missing placeholder: {e}")
                return f"Error: Data for '{e}' is missing."
        return template_string

    ### --- MODIFIED SECTION: Updated menu key list --- ###
    def _get_menu_text(self, menu_type, user_id):
        keys = {
            "main_menu": [
                "main_menu_prompt", 
                "option_parking_availability",
                "option_temple_info", 
                "option_help_centres", 
                "option_first_aid", 
                "option_temp_bus_stands", 
                "option_toilets_temple", 
                "option_annadhanam",
                "option_emergency_contacts", 
                "option_nearby_facilities", 
                "option_change_language", 
                "option_feedback",
                "option_end_conversation_text"
            ], 
            "temple_info_menu": [
                "temple_info_menu_prompt", 
                "temple_timings_menu_item", 
                "temple_dress_code_menu_item", 
                "option_go_back_text"
            ]
        }.get(menu_type, [])
        return "\n".join([self.get_text(user_id, k) for k in keys])

    def get_gspread_client(self):
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive.readonly']
            creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=scopes)
            client = gspread.authorize(creds)
            logger.info("gspread client authorized successfully.")
            return client
        except FileNotFoundError:
            logger.error(f"Credentials file '{GOOGLE_SHEETS_CREDENTIALS_FILE}' not found.")
        except Exception as e:
            logger.error(f"Gspread auth error: {e}", exc_info=True)
        return None

    def fetch_sheet_data(self, cache, last_fetch_time_attr, cache_duration, sheet_name, worksheet_name, force_refresh=False):
        last_fetch_time = getattr(self, last_fetch_time_attr, 0)
        if (not force_refresh) and (time.time() - last_fetch_time < cache_duration) and cache:
            return cache
        logger.info(f"Fetching fresh data for {sheet_name}/{worksheet_name}. Reason: {'Forced refresh' if force_refresh else 'Cache expired'}.")
        client = self.get_gspread_client()
        if not client: 
            logger.error("Gspread client is not available. Cannot fetch data.")
            return cache or []
        try:
            records = client.open(sheet_name).worksheet(worksheet_name).get_all_records()
            setattr(self, last_fetch_time_attr, time.time())
            logger.info(f"Successfully fetched {len(records)} records from {sheet_name}/{worksheet_name}.")
            return records
        except Exception as e:
            logger.error(f"Error fetching from {sheet_name}/{worksheet_name}: {e}", exc_info=True)
        return cache or []

    def fetch_local_info_from_sheet(self, worksheet_name: str, force_refresh: bool = False):
        last_fetch_attr = f"LAST_LOCAL_INFO_FETCH_TIME_{worksheet_name}"
        if not hasattr(self, last_fetch_attr): setattr(self, last_fetch_attr, 0)
        self.LOCAL_INFO_CACHE[worksheet_name] = self.fetch_sheet_data(
            self.LOCAL_INFO_CACHE.get(worksheet_name), last_fetch_attr, self.LOCAL_INFO_CACHE_DURATION, 
            GOOGLE_SHEET_LOCAL_INFO_NAME, worksheet_name, force_refresh=force_refresh
        )

    def fetch_parking_lots_info(self, force_refresh: bool = False):
        self.PARKING_LOTS_INFO_CACHE = self.fetch_sheet_data(
            self.PARKING_LOTS_INFO_CACHE, "LAST_PARKING_LOTS_INFO_FETCH_TIME", self.STATIC_DATA_CACHE_DURATION,
            GOOGLE_SHEET_PARKING_LOTS_INFO_NAME, "Sheet1", force_refresh=force_refresh
        )

    def fetch_parking_live_status(self, force_refresh: bool = False):
        records = self.fetch_sheet_data(
            list(self.PARKING_LIVE_STATUS_CACHE.values()), "LAST_PARKING_LIVE_STATUS_FETCH_TIME", self.LIVE_DATA_CACHE_DURATION,
            GOOGLE_SHEET_PARKING_STATUS_LIVE_NAME, "Sheet1", force_refresh=force_refresh
        )
        self.PARKING_LIVE_STATUS_CACHE = {str(r['ParkingLotID']): r for r in records if 'ParkingLotID' in r}

    def _generate_embed_link(self, query: str = "", mode: str = "place", origin: str = "", destination: str = "", my_map_id: str = "") -> str:
        if my_map_id:
            return f"https://www.google.com/maps/d/embed?mid={my_map_id}"
        if not GOOGLE_MAPS_API_KEY: return ""
        base_url = "https://www.google.com/maps/embed/v1/"
        if mode == "place": url = f"{base_url}place?key={GOOGLE_MAPS_API_KEY}&q={quote_plus(query)}"
        elif mode == "directions": url = f"{base_url}directions?key={GOOGLE_MAPS_API_KEY}&origin={origin}&destination={destination}"
        elif mode == "search": url = f"{base_url}search?key={GOOGLE_MAPS_API_KEY}&q={quote_plus(query)}"
        else: return ""
        return url

    def _get_formatted_sheet_data(self, user_id: str, worksheet_name: str) -> str:
        self.fetch_local_info_from_sheet(worksheet_name, force_refresh=True)
        data_items = self.LOCAL_INFO_CACHE.get(worksheet_name, [])
        lang = self.user_states[user_id].get("lang", "en")
        
        # Note: 'option_designated_parking' key is no longer in use in the menu, but the functionality remains here.
        format_map = {
            SHEET_HELP_CENTRES: ("option_help_centres", "local_info_item_format", "View Map"),
            SHEET_FIRST_AID: ("option_first_aid", "local_info_item_format", "View Map"),
            SHEET_TEMP_BUS_STANDS: ("option_temp_bus_stands", "local_info_item_format_bus", "View Map"),
            SHEET_TOILETS: ("option_toilets_temple", "local_info_item_format", "View Map"),
            SHEET_DESIGNATED_PARKING_STATIC: ("Designated Public Parking", "local_info_item_format_parking", "View Location"),
            SHEET_ANNADHANAM: ("option_annadhanam", "local_info_item_format_annadhanam", "View Map"),
        }
        category_key, item_format_key, link_text = format_map.get(worksheet_name, ("", "", ""))
        if not category_key: return "Error: Unknown data category."
        
        # Get the category name, handling the special case for the unused parking option
        if worksheet_name == SHEET_DESIGNATED_PARKING_STATIC:
             category_name = category_key # Use the hardcoded string
        else:
             category_name = self.get_text(user_id, category_key).split('. ', 1)[-1]

        if not data_items:
            logger.warning(f"No data for {worksheet_name}. Check sheet content/permissions.")
            return self.get_text(user_id, "no_local_info_found", category_name=category_name)
        
        title = self.get_text(user_id, "local_info_title_format", category_name=category_name)
        reply_parts = [title]
        item_template = self.get_text(user_id, item_format_key)
        
        for item in data_items:
            format_kwargs = defaultdict(lambda: 'N/A', item)
            item_name = item.get(f'Name_{lang}', item.get('Name_en', 'N/A'))
            format_kwargs['ItemName'] = item_name
            for key_en in list(item.keys()):
                if key_en.endswith('_en'):
                    format_kwargs[key_en[:-3].capitalize()] = item.get(f"{key_en[:-3]}_{lang}", item.get(key_en, 'N/A'))

            embed_url = self._generate_embed_link(f"{item_name}, Tiruchendur")
            link_html = f'<a href="{embed_url}" data-embed="true">{link_text}</a>' if embed_url else "Map not available"
            format_kwargs["LocationLink"] = link_html
            format_kwargs["MapsLink"] = link_html
            reply_parts.append(item_template.format_map(format_kwargs))
        return "".join(reply_parts)
        
    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371; dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
        a = sin(dLat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def find_available_parking(self, user_id: str, route_preference: Optional[str] = None) -> str:
        self.fetch_parking_lots_info(force_refresh=True)
        self.fetch_parking_live_status(force_refresh=True)
        
        current_lang = self.user_states[user_id].get("lang", "en")
        applicable_lots = [
            lot for lot in self.PARKING_LOTS_INFO_CACHE 
            if (not route_preference or route_preference == "any" or 
                route_preference.lower() in str(lot.get("Route_en", "any")).lower())
        ]

        if not applicable_lots:
            logger.warning(f"No parking lots found in sheet for route preference: {route_preference}")
            return self.get_text(user_id, "no_parking_available")

        processed_lots = []
        for lot in applicable_lots:
            try:
                lat = float(lot.get('Latitude'))
                lon = float(lot.get('Longitude'))
                capacity = int(lot.get('TotalCapacity', 0))
            except (ValueError, TypeError):
                logger.warning(f"Skipping lot due to invalid Lat/Lon/Capacity: {lot.get('Parking_name_en')}")
                continue
            if capacity <= 0: continue

            status = self.PARKING_LIVE_STATUS_CACHE.get(str(lot.get('ParkingLotID')), {})
            available = int(status.get('CurrentAvailability', -1))
            if available == -1: 
                available = capacity - max(0, int(status.get('CurrentIn', 0)) - int(status.get('CurrentOut', 0)))
            
            percentage_full = ((capacity - available) / capacity * 100) if capacity > 0 else 100

            if available > 0 and percentage_full < self.PARKING_FULL_THRESHOLD_PERCENT:
                lot_data = lot.copy()
                lot_data.update({
                    "Availability": available, "PercentageFull": percentage_full,
                    "Distance": self.haversine(self.TIRUCHENDUR_COORDS[0], self.TIRUCHENDUR_COORDS[1], lat, lon),
                    "Latitude": lat, "Longitude": lon, "TotalCapacity": capacity
                })
                processed_lots.append(lot_data)

        if not processed_lots: 
            logger.info(f"All lots for route {route_preference} are full or unavailable.")
            return self.get_text(user_id, "no_parking_available")

        sorted_lots = sorted(processed_lots, key=lambda x: (int(x.get('Priority', 99)), x['Distance']))
        
        title = self.get_text(user_id, "parking_for_route_title" if route_preference and route_preference != "any" else "parking_info_title", RouteName=route_preference.capitalize())
        
        details_list = []
        for lot in sorted_lots[:3]:
            # Use the special placeholder for the origin
            embed_url = self._generate_embed_link(mode="directions", origin="CURRENT_LOCATION", destination=f"{lot['Latitude']},{lot['Longitude']}")
            maps_link = f'<a href="{embed_url}" data-embed="true">Get Directions</a>' if embed_url else "Directions unavailable"
            
            details_list.append(self.get_text(user_id, "parking_lot_details_format", 
                ParkingName=lot.get(f"Parking_name_{current_lang}", lot.get("Parking_name_en")), 
                Distance=lot['Distance'], Availability=lot['Availability'], 
                TotalCapacity=lot['TotalCapacity'], PercentageFull=lot['PercentageFull'],
                MapsLink=maps_link))
        
        final_response = f"{title}\n" + "\n".join(details_list)

        if route_preference and route_preference in OVERALL_ROUTE_MY_MAPS:
            my_map_id = OVERALL_ROUTE_MY_MAPS[route_preference]
            overall_map_embed_url = self._generate_embed_link(my_map_id=my_map_id)
            
            final_response += self.get_text(user_id, "overall_parking_map_link_text",
                overall_map_url=overall_map_embed_url,
                RouteName=route_preference.capitalize()
            )

        return final_response

    def find_nearby_place(self, search_query: str, user_id=None) -> str:
        place_type_display_name = search_query.replace('_', ' ').title()
        embed_url = self._generate_embed_link(f"{search_query} in Tiruchendur", mode="search")
        maps_url_html = f'<a href="{embed_url}" data-embed="true">View on Map</a>' if embed_url else "Map not available"
        
        return (f'{self.get_text(user_id, "nearest_place_intro", place_type_display_name=place_type_display_name)}'
                f'{self.get_text(user_id, "place_details_maps", name=f"Results for {place_type_display_name}", address="Click the link below to see locations on the map.", maps_url=maps_url_html)}')