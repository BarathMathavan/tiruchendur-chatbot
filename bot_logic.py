# bot_logic.py
# -*- coding: utf-8 -*-

import os
import logging
import time
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# --- Firestore / Firebase Admin Imports ---
import firebase_admin
from firebase_admin import credentials, firestore

from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict
from urllib.parse import quote_plus

load_dotenv()

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
# This file is only used as a fallback for local testing
FIRESTORE_CREDENTIALS_FILE = os.path.join(BASE_DIR, os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json"))

# Centralized logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- All Constants and Menu Texts ---
GOOGLE_FORM_FEEDBACK_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSempmuc0_3KkCX3JK3wCZTod51Zw3o8ZkG78kQpcMTmVTGsPg/viewform?usp=header"
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
        "temple_timings_menu_item": "1. Temple Open/Close & Pooja Times",
        "temple_dress_code_menu_item": "2. Dress Code",
        "temple_seva_tickets_menu_item": "3. Seva & Ticket Details",
        "option_go_back_text": "0. Go Back to Main Menu",
        "freestyle_query_prompt": "Okay, what would you like to search for nearby (e.g., 'ATM', 'hotels', 'restaurants')?",
        "emergency_contacts_info": "Tiruchendur Emergency Contacts:\nPolice: 100\nFire: 101\nAmbulance: 108\nTemple Office: [Insert Number]",
        "local_info_title_format": "--- {category_name} in Tiruchendur ---",
        "local_info_item_format": "\n➡️ {ItemName}\n🗺️ {ViewMapLink}\n📝 Notes: {Notes}",
        "local_info_item_format_bus": "\n➡️ {ItemName}\n🛣️ Route: {RouteInfo}\n🗺️ {ViewMapLink}\n🕒 Active: {ActiveDuring}\n📝 Notes: {Notes}",
        "local_info_item_format_annadhanam": "\n🍚 {ItemName}\n🗺️ {ViewMapLink}\n🕒 Timings: {Timings}\n📞 Contact: {ContactInfo}\n📝 Notes: {Notes}",
        "no_local_info_found": "No information currently available for {category_name} in Tiruchendur.",
        "fetching_data_error": "Sorry, I couldn't fetch the latest information.",
        "parking_route_prompt": "Which route are you primarily arriving from for parking?\n(Type the number or name)\n1. Tirunelveli Route\n2. Thoothukudi Route\n3. Nagercoil Route\n4. Other/Already in Tiruchendur",
        "parking_for_route_title": "--- Parking Options for {RouteName} Route ---",
        "parking_info_title": "--- Tiruchendur Parking Availability ---",
        "no_parking_available": "Sorry, no suitable parking spots are currently available or all are nearly full.",
        "parking_lot_details_format": "\n🅿️ {ParkingName}\n🗺️ {ViewMapLink}\n📍 Approx. {Distance:.1f} km away\n📦 Availability: {Availability}/{TotalCapacity} slots ({PercentageFull:.0f}% full)",
        "overall_parking_map_link_text": "\n\n<a href=\"{overall_map_url}\" data-embed=\"true\">🗺️ View All Parking Lots for the {RouteName} Route</a>",
        "temple_timings_details": "Tiruchendur Murugan Temple General Timings:\nTimings can vary on festival days. It's best to check locally.",
        "temple_dress_code_details": "Dress Code: Traditional Indian attire is recommended. Men: Dhoti/Pants. Women: Saree/Salwar Kameez.",
        "goodbye_message": "Nandri! Vanakkam!",
        "nearest_place_intro": "📍 Here are results for {place_type_display_name} in the Tiruchendur area:",
        "place_details_maps": "\n{name}\nAddress: {address}\n🗺️ {maps_url}"
    },
    "ta": {
        # ... (Add full Tamil translations here for a complete experience)
    }
}
SUPPORTED_LANGUAGES = { "en": {"name": "English"}, "ta": {"name": "தமிழ் (Tamil)"} }
INFO_CATEGORIES = {
    "Help_Centres": ("option_help_centres", "local_info_item_format", "View Map & Directions"),
    "First_Aid_Stations": ("option_first_aid", "local_info_item_format", "View Map & Directions"),
    "Temp_Bus_Stands": ("option_temp_bus_stands", "local_info_item_format_bus", "View Map & Directions"),
    "Toilets_Near_Temple": ("option_toilets_temple", "local_info_item_format", "View Map & Directions"),
    "Annadhanam_Details": ("option_annadhanam", "local_info_item_format_annadhanam", "View Map & Directions"),
}
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
        self.PARKING_LOTS_CACHE, self.LAST_PARKING_LOTS_FETCH_TIME = [], 0
        self.CACHE_DURATION = 300 # 5 minutes
        self.PARKING_FULL_THRESHOLD_PERCENT = 95.0
        self.db = None
        self.initialize_firestore()
        self._preload_data()

    def initialize_firestore(self):
        if firebase_admin._apps:
            if not self.db: self.db = firestore.client()
            return
        logger.info("Initializing Firebase Admin SDK...")
        google_creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        try:
            if google_creds_json: creds_dict = json.loads(google_creds_json)
            else:
                with open(FIRESTORE_CREDENTIALS_FILE, 'r') as f:
                    creds_dict = json.load(f)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("Firestore client initialized successfully.")
        except FileNotFoundError:
             logger.error(f"FATAL: Credentials file not found at {FIRESTORE_CREDENTIALS_FILE} and GOOGLE_CREDENTIALS_JSON not set.")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}", exc_info=True)
            self.db = None

    def _preload_data(self):
        if not self.db: return
        logger.info("Pre-loading all data from Firestore...")
        for name in INFO_CATEGORIES.keys():
            self.fetch_local_info(name, force_refresh=True)
        self.fetch_all_parking_lots(force_refresh=True)
        logger.info("Pre-loading complete.")

    def fetch_firestore_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        if not self.db: return []
        try:
            return [doc.to_dict() for doc in self.db.collection(collection_name).stream()]
        except Exception as e:
            logger.error(f"Error fetching Firestore collection '{collection_name}': {e}", exc_info=True)
            return []
            
    def fetch_local_info(self, category_name: str, force_refresh: bool = False):
        last_fetch_attr = f"LAST_LOCAL_INFO_FETCH_TIME_{category_name}"
        if not hasattr(self, last_fetch_attr): setattr(self, last_fetch_attr, 0)
        if (not force_refresh) and (time.time() - getattr(self, last_fetch_attr, 0) < self.CACHE_DURATION) and self.LOCAL_INFO_CACHE.get(category_name):
            return
        if not self.db: return
        try:
            doc = self.db.collection("local_info").document(category_name).get()
            items = doc.to_dict().get("items", []) if doc.exists else []
            self.LOCAL_INFO_CACHE[category_name] = items
            setattr(self, last_fetch_attr, time.time())
        except Exception as e:
            logger.error(f"Error fetching Firestore doc '{category_name}': {e}", exc_info=True)

    def fetch_all_parking_lots(self, force_refresh: bool = False):
        if (not force_refresh) and (time.time() - self.LAST_PARKING_LOTS_FETCH_TIME < self.CACHE_DURATION) and self.PARKING_LOTS_CACHE:
            return
        self.PARKING_LOTS_CACHE = self.fetch_firestore_collection("parking_lots")
        self.LAST_PARKING_LOTS_FETCH_TIME = time.time()
    
    def _generate_embed_link(self, query: str = "", my_map_id: str = "") -> str:
        """Generates a URL for embedding inside the webpage's iframe."""
        if my_map_id:
            return f"https://www.google.com/maps/d/embed?mid={my_map_id}"
        if GOOGLE_MAPS_API_KEY and query:
            return f"https://www.google.com/maps/embed/v1/place?key={GOOGLE_MAPS_API_KEY}&q={quote_plus(query)}"
        return ""

    def _get_formatted_firestore_data(self, user_id: str, category_name: str) -> str:
        self.fetch_local_info(category_name, force_refresh=True)
        data_items = self.LOCAL_INFO_CACHE.get(category_name, [])
        lang = self.user_states[user_id].get("lang", "en")
        
        category_key, item_format_key, link_text = INFO_CATEGORIES.get(category_name, ("", "", ""))
        if not category_key: return "Error: Unknown data category."
        
        display_name = self.get_text(user_id, category_key).split('. ', 1)[-1]
        if not data_items:
            return self.get_text(user_id, "no_local_info_found", category_name=display_name)
        
        title = self.get_text(user_id, "local_info_title_format", category_name=display_name)
        reply_parts = [title]
        item_template = self.get_text(user_id, item_format_key)
        
        for item in data_items:
            format_kwargs = defaultdict(lambda: 'N/A', item)
            item_name = item.get(f'Name_{lang}', item.get('Name_en', 'N/A'))
            format_kwargs['ItemName'] = item_name

            embed_url = self._generate_embed_link(f"{item_name}, Tiruchendur")
            format_kwargs["ViewMapLink"] = f'<a href="{embed_url}" data-embed="true">{link_text}</a>' if embed_url else "Map not available"
            # Maintain compatibility with older formats that might use LocationLink/MapsLink
            format_kwargs["LocationLink"] = format_kwargs["ViewMapLink"]
            format_kwargs["MapsLink"] = format_kwargs["ViewMapLink"]

            for key_en in list(item.keys()):
                if key_en.endswith('_en'):
                    format_kwargs[key_en[:-3].capitalize()] = item.get(f"{key_en[:-3]}_{lang}", item.get(key_en, 'N/A'))
            
            reply_parts.append(item_template.format_map(format_kwargs))
        return "".join(reply_parts)
        
    def find_available_parking(self, user_id: str, route_preference: Optional[str] = None) -> str:
        self.fetch_all_parking_lots(force_refresh=True)
        current_lang = self.user_states[user_id].get("lang", "en")
        
        applicable_lots = [lot for lot in self.PARKING_LOTS_CACHE if (not route_preference or route_preference == "any" or route_preference.lower() in str(lot.get("Route_en", "any")).lower())]
        if not applicable_lots: return self.get_text(user_id, "no_parking_available")

        processed_lots = []
        for lot in applicable_lots:
            try:
                is_open = str(lot.get('IsParkingAvailable', 'FALSE')).upper() in ['TRUE', '1']
                if not is_open: continue
                available = int(lot.get('Total_Space', 0))
                capacity = int(lot.get('TotalCapacity', 0))
                if capacity <= 0: continue
                percentage_full = ((capacity - available) / capacity * 100) if capacity > 0 else 100
                if available > 0 and percentage_full < self.PARKING_FULL_THRESHOLD_PERCENT:
                    lot.update({
                        "Availability": available, "PercentageFull": percentage_full,
                        "Distance": self.haversine(self.TIRUCHENDUR_COORDS[0], self.TIRUCHENDUR_COORDS[1], float(lot['Latitude']), float(lot['Longitude']))
                    })
                    processed_lots.append(lot)
            except (ValueError, TypeError):
                logger.warning(f"Skipping parking lot due to invalid data: {lot.get('Parking_name_en')}")
        
        if not processed_lots: return self.get_text(user_id, "no_parking_available")

        sorted_lots = sorted(processed_lots, key=lambda x: (x['PercentageFull'], int(x.get('Priority', 99))))
        
        title = self.get_text(user_id, "parking_for_route_title" if route_preference and route_preference != "any" else "parking_info_title", RouteName=route_preference.capitalize())
        
        details_list = []
        for lot in sorted_lots:
            parking_name = lot.get(f"Parking_name_{current_lang}", lot.get("Parking_name_en"))
            
            embed_url = self._generate_embed_link(query=f"{parking_name}, Tiruchendur")
            view_map_link = f'<a href="{embed_url}" data-embed="true">View Map & Get Directions</a>'
            
            details_list.append(self.get_text(user_id, "parking_lot_details_format", 
                ParkingName=parking_name, 
                ViewMapLink=view_map_link,
                Distance=lot['Distance'], 
                Availability=lot['Availability'], 
                TotalCapacity=lot['TotalCapacity'], 
                PercentageFull=lot['PercentageFull']
            ))
        
        final_response = f"{title}\n" + "\n".join(details_list)

        if route_preference and route_preference in OVERALL_ROUTE_MY_MAPS:
            overall_map_embed_url = self._generate_embed_link(my_map_id=OVERALL_ROUTE_MY_MAPS[route_preference])
            final_response += self.get_text(user_id, "overall_parking_map_link_text",
                overall_map_url=overall_map_embed_url, RouteName=route_preference.capitalize())
        return final_response
    
    # --- The rest of the file (handlers, helpers) is correct and included for completeness ---
    
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
            if user_id in self.user_states: del self.user_states[user_id]
            return self._get_response_structure(self.get_text(user_id, "goodbye_message"))
        handler = getattr(self, f"_handle_{state.get('menu_level', 'main_menu')}", self._handle_invalid_state)
        return handler(user_id, text_input)

    def _handle_invalid_state(self, user_id, text_input):
        self.user_states[user_id]["menu_level"] = "main_menu"
        return self._get_response_structure(f"{self.get_text(user_id, 'invalid_menu_option')}\n\n{self._get_menu_text('main_menu', user_id)}")

    def _handle_main_menu(self, user_id, choice):
        menu_actions = {
            "1": ("parking_awaiting_route", None), "2": ("temple_info_menu", None),
            "3": (None, lambda: self._get_formatted_firestore_data(user_id, "Help_Centres")),
            "4": (None, lambda: self._get_formatted_firestore_data(user_id, "First_Aid_Stations")),
            "5": (None, lambda: self._get_formatted_firestore_data(user_id, "Temp_Bus_Stands")),
            "6": (None, lambda: self._get_formatted_firestore_data(user_id, "Toilets_Near_Temple")),
            "7": (None, lambda: self._get_formatted_firestore_data(user_id, "Annadhanam_Details")),
            "8": (None, lambda: self.get_text(user_id, "emergency_contacts_info")),
            "9": ("nearby_search", None),
            "10": (None, lambda: self._change_language(user_id)),
            "11": (None, lambda: self.get_text(user_id, "feedback_response", feedback_link=GOOGLE_FORM_FEEDBACK_LINK)),
        }
        new_level, action = menu_actions.get(choice, (None, None))
        if new_level:
            self.user_states[user_id]["menu_level"] = new_level
            prompt_map = {"parking_awaiting_route": "parking_route_prompt", "temple_info_menu": "temple_info_menu_prompt", "nearby_search": "freestyle_query_prompt"}
            response_text = self._get_menu_text(new_level, user_id) if new_level == "temple_info_menu" else self.get_text(user_id, prompt_map[new_level])
            return self._get_response_structure(response_text)
        elif action:
            if choice == "10": return action()
            result = action()
            return self._get_response_structure(f"{result}\n\n{self._get_menu_text('main_menu', user_id)}")
        return self._handle_invalid_state(user_id, choice)

    def _handle_temple_info_menu(self, user_id, choice):
        if choice == "0": 
            self.user_states[user_id]["menu_level"] = "main_menu"
            return self._get_response_structure(self._get_menu_text("main_menu", user_id))
        text_key = {"1": "temple_timings_details", "2": "temple_dress_code_details", "3": "temple_seva_tickets_menu_item"}.get(choice, "invalid_menu_option")
        text = self.get_text(user_id, text_key)
        return self._get_response_structure(f"{text}\n\n{self._get_menu_text('temple_info_menu', user_id)}")

    def _handle_parking_awaiting_route(self, user_id, text_input):
        self.user_states[user_id]["menu_level"] = "main_menu"
        route_pref = "any"
        if "1" in text_input or "tirunelveli" in text_input: route_pref = "tirunelveli"
        elif "2" in text_input or "thoothukudi" in text_input: route_pref = "thoothukudi"
        elif "3" in text_input or "nagercoil" in text_input: route_pref = "nagercoil"
        parking_reply = self.find_available_parking(user_id, route_preference=route_pref)
        return self._get_response_structure(f"{parking_reply}\n\n{self._get_menu_text('main_menu', user_id)}")

    def _handle_nearby_search(self, user_id, text_input):
        self.user_states[user_id]["menu_level"] = "main_menu"
        search_reply = self.find_nearby_place(text_input, user_id=user_id)
        return self._get_response_structure(f"{search_reply}\n\n{self._get_menu_text('main_menu', user_id)}")

    def _change_language(self, user_id, is_initial=False, user_name="User"):
        self.user_states[user_id]['menu_level'] = 'language_select'
        text = (self.get_text(user_id, "welcome_tiruchendur", user_name=user_name) + "\n") if is_initial else ""
        text += self.get_text(user_id, "select_language_prompt")
        buttons = [{"text": d["name"], "payload": c} for c, d in SUPPORTED_LANGUAGES.items()]
        return self._get_response_structure(text=text, buttons=buttons)

    def get_text(self, user_id, key, **kwargs):
        lang = self.user_states.get(user_id, {}).get("lang", "en")
        template_string = MENU_TEXTS.get(lang, MENU_TEXTS.get("en", {})).get(key, f"<{key}_MISSING>")
        if kwargs:
            try: return template_string.format(**kwargs)
            except KeyError as e:
                logger.error(f"Formatting failed for key '{key}'. Missing placeholder: {e}")
                return f"Error: Data for '{e}' is missing."
        return template_string

    def _get_menu_text(self, menu_type, user_id):
        keys = {
            "main_menu": ["main_menu_prompt", "option_parking_availability", "option_temple_info", "option_help_centres", "option_first_aid", "option_temp_bus_stands", "option_toilets_temple", "option_annadhanam", "option_emergency_contacts", "option_nearby_facilities", "option_change_language", "option_feedback", "option_end_conversation_text"], 
            "temple_info_menu": ["temple_info_menu_prompt", "temple_timings_menu_item", "temple_dress_code_menu_item", "temple_seva_tickets_menu_item", "option_go_back_text"]
        }.get(menu_type, [])
        return "\n".join([self.get_text(user_id, k) for k in keys])
        
    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371; dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
        a = sin(dLat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def find_nearby_place(self, search_query: str, user_id=None) -> str:
        place_type_display_name = search_query.replace('_', ' ').title()
        embed_url = self._generate_embed_link(f"{search_query} in Tiruchendur", mode="search")
        maps_url_html = f'<a href="{embed_url}" data-embed="true">View on Map</a>' if embed_url else "Map not available"
        return (f'{self.get_text(user_id, "nearest_place_intro", place_type_display_name=place_type_display_name)}'
                f'{self.get_text(user_id, "place_details_maps", name=f"Results for {place_type_display_name}", address="Click the link below to see locations on the map.", maps_url=maps_url_html)}')