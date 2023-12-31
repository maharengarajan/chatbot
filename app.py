import requests
import sys
import os
import re
import mysql.connector as conn
from src.logger import logging
from src.exception import CustomException
from ip2geotools.databases.noncommercial import DbIpCity
from weathermap import Weather
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from datetime import datetime


app = Flask(__name__)

def configure():
    load_dotenv()

configure()

host = os.getenv("database_host_name")
user_name = os.getenv("database_user_name")
password = os.getenv("database_user_password")
database = os.getenv("database_name")
smtp_server = os.getenv("smtp_server")
smtp_port = os.getenv("smtp_port")
smtp_username = os.getenv("smtp_username")
smtp_password = os.getenv("smtp_password")
sender_email = os.getenv("sender_email")
receiver_emails = os.getenv("receiver_emails")
cc_email = os.getenv("cc_email")

# print(host)
# print(user_name)
# print(password)
# print(database)
# print(smtp_server)
# print(smtp_port)
# print(smtp_username)
# print(smtp_password)
# print(sender_email)
# print(receiver_emails)
# print(cc_email)

# Connection from Python to MySQL
mydb = conn.connect(host=host,user=user_name,password=password,database=database)
cursor = mydb.cursor()


current_date = datetime.now().date()
current_time = datetime.now().time()


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
    

# this API responsible for collecting user details from new client and save in DB
@app.route("/chatbot/new_client_details", methods=["POST"])
def new_client_details():
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        contact = data.get("contact")

        if not is_valid_name(name):
            return jsonify({"message": "Please enter a valid name.", "code": 400})

        if not is_valid_email(email):
            return jsonify({"message": "Please enter a valid email address.", "code": 400})

        if not is_valid_contact_number(contact):
            return jsonify({"message": "Please enter a valid contact number.", "code": 400})

        user_details = {"name": name, "email": email, "contact": contact}
        logging.info(f"user details collected :{user_details}")

        query = "INSERT INTO new_client (DATE, TIME, NAME, EMAIL_ID, CONTACT_NUMBER) VALUES (%s, %s, %s, %s, %s)"
        values = (current_date, current_time, name, email, contact)
        cursor.execute(query, values)
        row_id = cursor.lastrowid  # Get the ID (primary key) of the inserted row
        mydb.commit()  # Commit the changes to the database
        logging.info(f"user details saved in database")

        return jsonify(
            {
                "message": "User details collected successfully.",
                "row_id": row_id,
                "code": 200,
            }
        )
    except Exception as e:
        return jsonify(
            {"message": "Internal server error.", "error": str(e), "code": 500}
        )


def is_valid_name(name):
    return bool(re.match(r"^[A-Za-z\s]+$", name.strip()))


def is_valid_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def is_valid_contact_number(contact):
    return bool(re.match(r"^\+?\d{1,3}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$", contact))


# this API is responsible for selecting industries
@app.route("/chatbot/new_client/user_details/industries", methods=["POST"])
def industries():
    try:
        industries = {
            "1": "Insurance",
            "2": "Banking",
            "3": "Finance",
            "4": "IT",
            "5": "Healthcare",
            "6": "Internet",
            "7": "Automobile",
            "8": "Others",
        }
        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        selected_options = data.get("selected_options", [])
        selected_industries = [
            industries[opt] for opt in selected_options if opt in industries
        ]

        industry_str = ",".join(selected_industries)  # Convert lists to strings

        query = "UPDATE new_client SET INDUSTRY = %s WHERE ID = %s"
        values = (industry_str, row_id)
        cursor.execute(query, values)
        mydb.commit()
        logging.info(f"industries saved in database: {selected_industries}")
        return jsonify({"selected_industries": selected_industries, "code": 200})
    except Exception as e:
        return jsonify(
            {"message": "Internal server error.", "error": str(e), "code": 500}
        )

# this API is responsible for selecting verticals
@app.route("/chatbot/new_client/user_details/industries/verticals", methods=["POST"])
def verticals_new_client():
    try:
        verticals = {
            "1": "ML/DS/AI",
            "2": "Sales force",
            "3": "Microsoft dynamics",
            "4": "Custom app",
            "5": "Others",
        }

        data = request.get_json()
        row_id = data.get("row_id")  # Get the user ID from the request

        selected_options = data.get("selected_options", [])
        selected_verticals = [
            verticals[opt] for opt in selected_options if opt in verticals
        ]

        vertical_str = ",".join(selected_verticals)

        query = "UPDATE new_client SET VERTICAL = %s WHERE ID = %s"
        values = (vertical_str, row_id)
        cursor.execute(query, values)
        mydb.commit()

        logging.info(f"user selected verticals saved: {selected_verticals}")
        return jsonify({"selected_verticals": selected_verticals, "code": 200})
    except Exception as e:
        return jsonify(
            {"message": "Internal server error.", "error": str(e), "code": 500}
        )

# this API is responsible for selecting requirements
@app.route("/chatbot/new_client/user_details/industries/verticals/requirement",methods=["POST"])
def requirement():
    try:
        requirements = {
            "1": "Start the project from scratch",
            "2": "Require support from existing project",
            "3": "Looking for some kind of solutions",
            "4": "Others",
        }

        data = request.get_json()
        selected_option = data.get("selected_option")
        row_id = data.get("row_id")  # Get the user ID from the request

        if selected_option in requirements:
            selected_requirement = requirements[selected_option]

            query = "UPDATE new_client SET REQUIREMENTS = %s WHERE ID = %s"
            values = (selected_requirement, row_id)
            cursor.execute(query, values)
            mydb.commit()

            logging.info(f"selected requirement: {selected_requirement}")
            return jsonify({"selected_requirement": selected_requirement, "code": 200})
        else:
            return jsonify({"message": "Please choose a valid option.", "code": 400})
    except Exception as e:
        return jsonify(
            {"message": "Internal server error.", "error": str(e), "code": 500}
        )


    
if __name__ == "__main__":
    app.run()
