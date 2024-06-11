from selenium import webdriver
from bs4 import BeautifulSoup
import time
import json
import os
import telebot
from datetime import datetime
from dotenv import load_dotenv
from sys import argv
load_dotenv()

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2024-06-15&dateIn=&isConnectedFlight=false&discount=0&promoCode=&isReturn=false&originIata=TNG&destinationIata=AGA&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2024-06-15&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=TNG&tpDestinationIata=AGA")
    return driver

def get_date(day, month, year):
    #add zeroes for single digit days and months
    if day < 0 or day > 31:
        raise ValueError("Day must be between 0 and 31")
    if month < 0 or month > 12:
        raise ValueError("Month must be between 0 and 12")
    if year < 0:
        raise ValueError("Year must be positive")
    day = str(day).zfill(2)
    month = str(month).zfill(2)
    return f"{year}-{month}-{day}"


TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(TOKEN)
# site = "https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT=1&TEEN=0&CHD=0&INF=0&Origin=TNG&Destination=AGA&promoCode=&IncludeConnectingFlights=false&DateOut=2024-06-15&DateIn=&FlexDaysBeforeOut=2&FlexDaysOut=2&FlexDaysBeforeIn=2&FlexDaysIn=2&RoundTrip=false&ToUs=AGREED"


def get_data(driver, site):
    driver.get(site)
    response_body = driver.page_source
    html = BeautifulSoup(response_body, 'html.parser')
    element = html.find('pre').text
    return json.loads(element)


def get_flight_info(driver):
    info = {}
    data = get_data(driver)
    trip = data['trips'][0]
    dates = trip['dates']
    for date in dates:
        flight_date = date["dateOut"]
        if ("2024-06-15" in flight_date):
            flight  = date["flights"][0]
            info["flight_price"] = flight["regularFare"]["fares"][0]["amount"]
            info["flight_origin"] = flight["segments"][0]["origin"]
            info["flight_destination"] = flight["segments"][0]["destination"]
            info["flight_duration"] = flight["segments"][0]["duration"]
            
#     return info
def parse_date_input(argv):
    day = int(argv[0])
    month = int(argv[1])
    year = int(argv[2])
    try:
        date = get_date(day, month, year)
    except ValueError as e:
        print("Error: ", e)
        exit(1)
    return date


def get_flight_price(date, frm="AGA", to="TNG"):
    print(frm, to, date)
    chrome = init_driver()
    query = f"https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT=1&TEEN=0&CHD=0&INF=0&Origin={frm}&Destination={to}&promoCode=&IncludeConnectingFlights=false&DateOut={date}&DateIn=&FlexDaysBeforeOut=2&FlexDaysOut=2&FlexDaysBeforeIn=2&FlexDaysIn=2&RoundTrip=false&ToUs=AGREED"
    info = get_data(chrome, query)
    dates = info["trips"][0]["dates"]
    for d in dates:
        if date in d["dateOut"]:
            flight = d["flights"][0]
            price = flight["regularFare"]["fares"][0]["amount"]
            flight_number = flight["segments"][0]["flightNumber"]
            return [price, flight_number]
    return None

def pause(hours=1, seconds=0, minutes=0):
    time.sleep(60 * 60 * hours)

def save_data_to_file(file, data: dict):
    with open(file, "a+") as file:
        #check if file is empty
        file.seek(0)
        char = file.read(1)
        file.seek(0, 2)
        if not char:
            file.write("current_date,flight_number, price, date, from, to\n")
        else:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"{current_date}, {data['flight_number']}, {data['price']}, {data['date']}, {data['from']}, {data['to']}\n")

def get_the_last_price_from_file():
    with open("file.csv", "r") as file:
        lines = file.readlines()
        last_line = lines[-1]
        data = last_line.split(", ")
        return float(data[2])

if __name__ == "__main__":
    if len(argv) != 6:
        print("Usage: python main.py day month year from to")
        exit(1)
    frm = argv[4].upper()
    to = argv[5].upper()
    date = parse_date_input(argv[1:4])
    bot.send_message(CHAT_ID, f"Bot started listening for date {date} from {frm} to {to}")
    while True:
        price, flight_number = get_flight_price(date, frm=frm, to=to)
        save_data_to_file("file.csv", {
            "flight_number": flight_number,
            "price": price,
            "date": date,
            "from": "AGA",
            "to": "TNG"
        })
        last_price_added = get_the_last_price_from_file()
        if last_price_added != price:
            bot.send_message(CHAT_ID, f"Price has changed from {last_price_added} to {price} for flight {flight_number} on {date}")
        pause(hours=1)
