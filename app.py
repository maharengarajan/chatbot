import requests
import sys
import os
from src.logger import logging
from src.exception import CustomException
from ip2geotools.databases.noncommercial import DbIpCity
from weathermap import Weather
from dotenv import load_dotenv
from flask import Flask, jsonify, request


app = Flask(__name__)

def configure():
    load_dotenv()

def get_ip_address():
    try:
        address = requests.get("https://api.ipify.org").text
        logging.info(f"user's ip address is {address}")
        return address
    except Exception as e:
        raise CustomException(e,sys)
    
def get_location():
    ip_address = get_ip_address()
    try:
        location = DbIpCity.get(ip_address, api_key='free')
        logging.info(f"user's location is {location.region}")
        return str(location.region)
    except Exception as e:
        raise CustomException(e,sys)
    

def get_weather():
    try:
        city = get_location()
        configure()
        weather_info = Weather(apikey='weather_api_key', city="Chennai")
        current_weather = weather_info.get_current_weather()
        logging.info(f"user,s current weather is {current_weather}")
        return current_weather["weather"][0]["main"].lower()
    except Exception as e:
        raise CustomException(e,sys)
    

def weather_greeting():
    try:
        weather = get_weather()
        if weather in ["thunderstorm", "drizzle", "rain", "snow"]:
            logging.info(f"It seems like there's {weather} outside. Stay safe!")
            return f"It seems like there's {weather} outside. Stay safe!"
        elif weather in ["atmosphere", "clear", "clouds"]:
            logging.info(f"Enjoy the {weather} weather!")
            return f"Enjoy the {weather} weather!"
        elif weather in ["mist", "smoke", "haze", "dust", "fog", "sand", "ash"]:
            logging.info(f"Be cautious as there's {weather} in the air.")
            return f"Be cautious as there's {weather} in the air."
        elif weather in ["squall", "tornado"]:
            logging.info(f"Take extra precautions due to {weather} in the area.")
            return f"Take extra precautions due to {weather} in the area."
    except Exception as e:
        raise CustomException(e,sys)   
    
# this API responsible for greeting the user
@app.route("/chatbot/greeting", methods=["GET"])
def greeting():
    try:
        ip_location = get_location()
        weather_info_greet = weather_greeting()
        greet = f"Hello, buddy! Welcome to Datanetiix! We hope you're connecting from {ip_location}. {weather_info_greet}"
        logging.info(f"greet given: {greet}")
        return jsonify({"message": greet})
    except Exception as e:
        raise CustomException(e,sys)


@app.route("/chatbot/client", methods=["POST"])
def client():
    try:
        data = request.get_json()
        client_type = data.get("client_type")

        welcome_messages = {
            "1": "Welcome, New client!",
            "2": "Welcome, existing client!",
            "3": "Welcome, Job seeker!",
            "4": "Bye!",
        }

        message = welcome_messages.get(client_type, "Invalid option. Please choose a valid option.")
        status_code = 200 if client_type in welcome_messages else 400

        return jsonify({"message": message, "code": status_code})

    except Exception as e:
        return jsonify({"message": "Internal server error.", "error": str(e), "code": 500})

    
if __name__ == "__main__":
    app.run()
