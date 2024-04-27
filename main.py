from selenium import webdriver
from bs4 import BeautifulSoup
import time
import json
import os
import telebot
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(TOKEN)
site = "https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT=1&TEEN=0&CHD=0&INF=0&Origin=TNG&Destination=AGA&promoCode=&IncludeConnectingFlights=false&DateOut=2024-06-15&DateIn=&FlexDaysBeforeOut=2&FlexDaysOut=2&FlexDaysBeforeIn=2&FlexDaysIn=2&RoundTrip=false&ToUs=AGREED"

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2024-06-15&dateIn=&isConnectedFlight=false&discount=0&promoCode=&isReturn=false&originIata=TNG&destinationIata=AGA&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2024-06-15&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=TNG&tpDestinationIata=AGA")
    return driver

def get_data(driver):
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
            
    return info


if __name__ == "__main__":
    bot.send_message(CHAT_ID, "Bot started")
    chrome = init_driver();
    old_price = float(get_flight_info(chrome)["flight_price"])
    while True:
        flight_info = get_flight_info(chrome)
        new_price = float(flight_info["flight_price"])
        if new_price != old_price:
            message = f"Price has changed for the flight from {old_price} to {new_price}"
            bot.send_message(CHAT_ID, message)
            bot.send_message(CHAT_ID, f"lien: {site}")
        with open("file.csv", "a") as file:
            file.write(f"\n{old_price}, {new_price}, {datetime.now()}")
        time.sleep(60 * 60 * 1)