#!/usr/bin/python3

# importing needed modules
import eel
import csv
import os
import random
import re
import smtplib
import threading
import time
import webbrowser
from datetime import datetime
from subprocess import Popen
from sys import argv

import pyjokes
import pyowm
import pyscreenshot
import requests
import screen_brightness_control as sbc
import wikipedia
from googlesearch import search as gSearch
from googletrans import Translator
from gtts import gTTS
from playsound import playsound
from PyDictionary import PyDictionary
from quotes import random as random_quote

# importing dataset from data.py file
from data import data

dictionary = PyDictionary()

last_assistant = ""

before_last_assistant = ""

tts_off = False

word_to_remove = ""

to_send_to_js = ""

printed = False

said = False

turnTTSOff = False

timers = []

last_user = ""

mode = "dark"

API_KEY = "AIzaSyCJwTqEZBqNmLru1kCSnQZOoPjDLXgqWko"

SEARCH_ENGINE_ID = "74b00f5aa1b238403"


eel.init("web")

if len(argv) > 1:
    if argv[1] == "--tts-off":
        tts_off = True


def say(string, lang="en"):
    if len(string) < 200:
        string = re.sub(r"<[\w\W]*?>", "", string)
        tts = gTTS(text=string, lang=lang)
        try:
            filename = "speech" + str(random.randint(0, 1000000)) + ".mp3"
            tts.save(filename)
            playsound(filename)
            os.remove(filename)
        except:
            pass


@eel.expose
def send_to_js():
    global to_send_to_js, turnTTSOff, tts_off
    tmp = True if turnTTSOff else False
    turnTTSOff = False
    if tmp:
        tts_off = True
    to_send = to_send_to_js
    to_send_to_js = None
    if to_send:
        return to_send, tmp


@eel.expose
def print_answer(string, end="\n", tts=True):
    if string:
        string = string.replace("\n", "<br>")
        global last_assistant, to_send_to_js, last_assistant2, to_send, printed, tts_off
        printed = True
        before_last_assistant = last_assistant
        last_assistant = string
        if not tts_off and tts:
            thread = threading.Thread(target=say, args=(string,))
            thread.start()
        to_send_to_js = string


@eel.expose
def remove_syntax(string):
    return re.sub("[,.!?\"']*", "", string)


@eel.expose
def toggle_tts():
    global tts_off
    tts_off = not tts_off


@eel.expose
def done():
    global to_send_to_js
    to_send_to_js = None


def get_input(string):
    global answer, to_send_to_js

    answer = string
    print_answer(answer)
    to_send_to_js = answer
    eel.get_input()()

    value = eel.send_input_value()()
    while not value:
        value = eel.send_input_value()()
    return value


def send(string):
    global answer, send_to_js

    answer = string
    send_to_js = answer
    print_answer(answer)


def translate(text, dest="en"):
    translator = Translator()
    translation = translator.translate(text, dest=dest)
    return translation


@eel.expose
def toggle_mode():
    global mode
    mode = "light" if mode == "dark" else "dark"


def search(search_item, person, google=False):
    global mode
    answer = ""
    if google:
        try:
            more = ""
            page = 1
            start = (page - 1) * 10 + 1
            url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={search_item}&start={start}"
            data = requests.get(url).json()
            search_items = data.get("items")
            for i, search_item in enumerate(search_items, start=1):
                # get the page title
                title = search_item.get("title")
                # page snippet
                snippet = search_item.get("snippet")
                # extract the page url
                link = search_item.get("link")
                for word in title.split():
                    if len(word) > 30:
                        title = title.replace(word, word[:25] + "...")
                for word in snippet.split():
                    if len(word) > 30:
                        snippet = snippet.replace(word, word[:25] + "...")
                if i < 4:
                    if mode == "dark":
                        answer += "<a class='news news-dark' target='_blank' href='" + \
                            link + "'>" + "<h2>" + title + "</h2>" + snippet + "</a><br><br>"
                    else:
                        answer += "<a class='news news-light' target='_blank' href='" + \
                            link + "'>" + "<h2>" + title + "</h2>" + snippet + "</a><br><br>"
                else:
                    if mode == "dark":
                        more += "<a class='news news-dark' target='_blank' href='" + \
                            link + "'>" + "<h2>" + title + "</h2>" + snippet + "</a><br><br>"
                    else:
                        more += "<a class='news news-light' target='_blank' href='" + \
                            link + "'>" + "<h2>" + title + "</h2>" + snippet + "</a><br><br>"
            eel.update_news(more)()
            answer += "<div class='more' onclick='expand();'>Click for more</div>"
        except:
            pass
    elif person:
        try:
            answer = search_wikipedia(search_item)
            found_on_wikipedia()
        except:
            try:
                answer = search_wikipedia(search_item.split()[-1])
                found_on_wikipedia()
            except:
                try:
                    answer = search_wikipedia(search_item.split()[0])
                    found_on_wikipedia()
                except:
                    answer = search(search_item, False, google=True)
                    return
    else:
        answered = False
        try:
            for category in data:
                for item in data[category]:
                    if item.startswith(search_item) or item.endswith(search_item) or search_item.startswith(item) or search_item.endswith(item):
                        answer = search_item + " is a " + category if search_item != category else search_item + \
                            " means " + random.choice(data[category])
                        return answer
        except:
            pass
        if not answered:
            search_item = search_item.replace("a ", "").strip()
            definition = dictionary.meaning(search_item)
            if definition:
                print_answer("Here are some definitions that I found: ")
                answer = ""
                for part in definition:
                    answer += part + ":<br>"
                    for meaning in definition[part]:
                        answer += str(definition[part].index(meaning) +
                                      1) + ". " + meaning + ". <br>"
                return answer

        if not answered:
            answer = search(search_item, False, google=True)
    return answer


def search_wikipedia(search_item):
    return wikipedia.summary(search_item)


def found_on_wikipedia():
    print_answer("Here is what I found on Wikipedia:")


def sleep(seconds, index):
    global timers
    if seconds > 15:
        print_answer("A timer was set. Countdown has started.")
    elif seconds > 1:
        print_answer("A countdown has started")
    timer = timers[index]
    for i in range(seconds):
        if timer[5]:
            time.sleep(1)
        else:
            timers.remove(timer)
            print_answer("The timer " + str(index+1) + " was canceled.")
            break
    try:
        timers.remove(timer)
        playsound("timeover.wav")
        print_answer("Time is over")
    except:
        pass


def check_reminder(reminder, date, index):
    date, time = date.split()
    hours = int(time.split(":")[0])
    minutes = int(time.split(":")[1])
    while True:
        date_now = str(datetime.now().date())
        time_now = str(datetime.now().time())
        hours_now = int(time_now.split(":")[0])
        minutes_now = int(time_now.split(":")[1])
        if date_now == date:
            if hours_now > hours:
                break
            if hours_now == hours and minutes_now > minutes:
                break
            elif int(time.split(":")[0]) < int(time.split(":")[0]) or int(time_now.split(":")[1]) < int(time.split(":")[1]):
                break
        elif int(date.split("-")[1]) < int(date.split("-")[1]) or int(date_now.split("-")[2]) < int(date.split("-")[2]):
            break
    if not data["reminder_threads"][index][3]:
        playsound("timeover.wav")
        print_answer("Reminder: " + reminder + " on " + date + " " + time)
        data["reminder_threads"][index][3] = True
        with open("data.py", "w") as file:
            file.write("data = " + str(data))


def take_screenshot(seconds):
    time.sleep(seconds)
    image = pyscreenshot.grab()
    say_thread = threading.Thread(target=say, args=(
        "Screenshot was taken. Press CTRL S or CTRL SHIFT S to save it",))
    say_thread.start()
    image.show()


@eel.expose
def generate_answer(user_input, user_input_without_syntax):
    global tts_off, last_assistant, word_to_remove, printed, to_send_to_js, said, turnTTSOff, timers, last_user

    words = user_input_without_syntax.split()
    user_input_without_syntax = user_input_without_syntax.replace("whats", "what is").replace("whatre", "what are").replace(
        "whos", "who is").replace("whore", "who are").replace(" r ", " are ").replace(" u ", " you ").lower()
    if words[-1] == "u":
        user_input_without_syntax = user_input_without_syntax[:len(
            user_input_without_syntax)-2] + " you"
    user_input = user_input.replace("whats", "what is").replace("whatre", "what are").replace(
        "whos", "who is").replace("whore", "who are").replace(" r ", " are ").replace(" u ", " you ")
    if words[-1] == "u":
        user_input = user_input[:len(user_input)-2] + " you"
    words = user_input_without_syntax.split()

    types = recognize_type(user_input, user_input_without_syntax, words)

    question = types[0]
    greeting = types[1]
    about_themselves = types[2]
    statement = types[3]
    about_it = types[4]
    greeting_word = types[5]

    trnslt = False
    language = ""
    code = ""
    file = open("languages.csv", "r")
    reader = csv.DictReader(file)
    rows = list(reader)
    file.close()

    for wrd in words:
        if not trnslt:
            for row in rows:
                if wrd.lower() == row["Language"].lower():
                    language = row["Language"]
                    trnslt = True
                    break
        else:
            break
    
    if "reminder_threads" in data:
        for reminder in data["reminder_threads"]:
            try:
                if not reminder[3]:
                    reminder_thread = threading.Thread(
                        target=check_reminder, args=(reminder[0], reminder[1], reminder[2]))
                    reminder_thread.start()
            except: pass

    user_input = user_input.lower()

    answer = ""

    printed = False

    if user_input == "show me your knowledge":
        answer = str(data)
        print_answer(answer)
        return

    elif "brightness" in words:
        percentage = re.findall(r"(\d+)", user_input_without_syntax)
        if percentage:
            percentage = int(percentage[0].strip())
            try:
                sbc.set_brightness(percentage)
            except:
                print_answer("Sorry, couldn't set the brightness")
        else:
            percentage = int(re.sub(r"[^\d]", "", get_input(
                "Please, enter the brightness percentage")).strip())
            try:
                sbc.set_brightness(percentage)
            except:
                print_answer("Sorry, couldn't set the brightness")

    elif "weather" in words or "temperature" in words or ("like" in words and "outside" in words):
        weather = pyowm.OWM("6d00d1d4e704068d70191bad2673e0cc").weather_manager(
        ).weather_at_place(eel.get_location()()).weather
        temperature = ""
        max_temperature = ""
        min_temperature = ""
        feels_like = ""
        if "fahrenheit" in words:
            temperature = str(weather.temperature("fahrenheit")["temp"]) + "°F"
            max_temperature = str(weather.temperature(
                "fahrenheit")["temp_max"]) + "°F"
            min_temperature = str(weather.temperature(
                "fahrenheit")["temp_min"]) + "°F"
            feels_like = str(weather.temperature(
                "fahrenheit")["feels_like"]) + "°F"
        else:
            temperature = str(weather.temperature("celsius")["temp"]) + "°C"
            max_temperature = str(weather.temperature(
                "celsius")["temp_max"]) + "°C"
            min_temperature = str(weather.temperature(
                "celsius")["temp_min"]) + "°C"
            feels_like = str(weather.temperature(
                "celsius")["feels_like"]) + "°C"
        temperature_C = str(weather.temperature("celsius")["temp"]) + "°C"
        max_temperature_C = str(
            weather.temperature("celsius")["temp_max"]) + "°C"
        min_temperature_C = str(
            weather.temperature("celsius")["temp_min"]) + "°C"
        feels_like_C = str(weather.temperature("celsius")["feels_like"]) + "°C"
        if float(temperature_C.replace("°C", "")) > 0:
            if float(temperature_C.replace("°C", "")) > 15:
                temperature = "<span style='color: lightcoral;'>+" + temperature + "</span>"
            else:
                temperature = "<span style='color: #fcba03;'>+" + temperature + "</span>"
        else:
            temperature = "<span style='color: lightblue;'>" + temperature + "</span>"
        if float(max_temperature_C.replace("°C", "")) > 0:
            if float(max_temperature_C.replace("°C", "")) > 15:
                max_temperature = "<span style='color: lightcoral;'>+" + max_temperature + "</span>"
            else:
                max_temperature = "<span style='color: #fcba03;'>+" + max_temperature + "</span>"
        else:
            max_temperature = "<span style='color: lightblue;'>" + max_temperature + "</span>"
        if float(min_temperature_C.replace("°C", "")) > 0:
            if float(min_temperature_C.replace("°C", "")) > 15:
                min_temperature = "<span style='color: lightcoral;'>+" + min_temperature + "</span>"
            else:
                min_temperature = "<span style='color: #fcba03;'>+" + min_temperature + "</span>"
        else:
            min_temperature = "<span style='color: lightblue;'>" + min_temperature + "</span>"
        if float(feels_like_C.replace("°C", "")) > 0:
            if float(feels_like_C.replace("°C", "")) > 15:
                feels_like = "<span style='color: lightcoral;'>+" + feels_like + "</span>"
            else:
                feels_like = "<span style='color: #fcba03;'>+" + feels_like + "</span>"
        else:
            feels_like = "<span style='color: lightblue;'>" + feels_like + "</span>"

        humidity = str(weather.humidity)
        status = weather.detailed_status
        status_icon = ""
        if "sunny" in status:
            status_icon += "☀ "
        elif "cloud" in status:
            status_icon += "🌥 "
        elif "rain" in status:
            status_icon += "🌧 "
        elif "snow" in status:
            status_icon += "🌧 "
        elif "storm" in status:
            status_icon += "🌪 "
        elif "clear" in status:
            status_icon += "☀ "
        answer = "Temperature: " + temperature + "<br>Maximum temperature: <span style='color: lightcoral;'>" + temperature + "</span><br>Minimum temperature: <span style='color: blue;'>" + \
            min_temperature + "</span><br>Feels like: " + feels_like + \
            "<br>Humidity: 💧" + humidity + "<br>Weather status: " + status_icon + status
        print_answer(answer, tts=False)
        if not tts_off:
            say_thread = threading.Thread(
                target=say, args=(f"Right now, it is {temperature}",))
            say_thread.start()

    elif "screenshot" in words:
        if "seconds" in words:
            seconds = re.findall(r"(\d+)", user_input_without_syntax)
            if seconds:
                seconds = seconds[0]
                say("Taking screenshot in " + seconds + " seconds")
                take_screenshot(int(seconds))
        else:
            say("Taking screenshot in 3 seconds")
            take_screenshot(3)

    elif "joke" in words and "not" not in words or "humor" in words or "make me laugh" in user_input_without_syntax or ("tell" in words and "funny" in words):
        answer = pyjokes.get_joke()
        print_answer(answer)

    elif "quote" in user_input_without_syntax:
        quote = random_quote()
        answer = "\"" + quote[1] + "\"" + "—" + quote[0]
        print_answer(answer)

    elif "time" in words:
        answer = "Right now it is " + str(datetime.now().time())[:8]
        print_answer(answer)

    elif "date" in words:
        answer = "Right now it is " + str(datetime.now().date())
        print_answer(answer)

    elif trnslt and "to" in words or "in" in words:
        text = ""
        for row in rows:
            if language == row["Language"]:
                code = row["Code"]
        if "translate" in words:
            text = ""
            if "to" in words:
                for word in words:
                    if words.index(word) > words.index("translate") and words.index(word) < words.index("to"):
                        text += word + " "
            elif "in" in words:
                if words.index(word) > words.index("translate") and words.index(word) < words.index("in"):
                    text += word + " "
        else:
            text = user_input_without_syntax[:user_input_without_syntax.lower().index(
                language.lower())-3].strip()
        translation = translate(text=text, dest=code)
        answer = "Translation: " + translation.text
        answer += "<div>Pronunciation: " + translation.pronunciation + \
            "</div>" if translation.pronunciation else ""
        print_answer(answer, tts=False)
        pronunciation = threading.Thread(
            target=say, args=(translation.text, code))
        pronunciation.start()
        return

    elif user_input_without_syntax == "0 or 1" or user_input_without_syntax == "1 or 0" or user_input_without_syntax == "1 or 2" or user_input_without_syntax == "2 or 1":
        print_answer("1!")

    elif "random" in words and "number" in words:
        number = str(random.randint(0, 100000000000000))
        print_answer(number)

    elif "remember this" in user_input_without_syntax or "remember" in user_input_without_syntax and "thing" in user_input_without_syntax:
        answer = "Sure! Just say something like \"Remember the door code is 4453\" and then ask \"What is the door code\""
        print_answer(answer)

    elif "one more" in user_input_without_syntax or "another one" in user_input_without_syntax:
        user_input = last_user
        user_input_without_syntax = remove_syntax(last_user).lower().strip()
        words = user_input_without_syntax.split()
        question, greeting, about_themselves, statement, about_it, greeting_word = recognize_type(
            user_input, user_input_without_syntax, words)
        answer = generate_answer(user_input, user_input_without_syntax)
        print_answer(answer)
        return

    last_user = user_input

    if re.match(r"[\w\W]*[\d]+[\+\-\*\/]+[\w\W]*", user_input_without_syntax, re.IGNORECASE) and "timer" not in words and "timers" not in words:
        user_input_without_syntax = user_input_without_syntax.replace(
            "^", "**")
        to_calculate = re.findall(
            r"([\d\+\-\*\/]+)", user_input_without_syntax, re.IGNORECASE)[0]
        answer = str(eval(to_calculate))
        print_answer(answer)

    elif "news" in words:
        if "about" in words or "on" in words:
            index = None
            if "about" in words:
                index = user_input_without_syntax.index("about")
            elif "on" in words:
                index = user_input_without_syntax.index("on")
            query = user_input_without_syntax[index:].strip() + " news"
            news = search(query, False, google=True)
            print_answer(news)
        else:
            news = search("latest news", False, google=True)
            print_answer(news)

    elif "google" in words or "search" in words or "wikipedia" in words and words[0] != "open":
        query = user_input_without_syntax.lower().replace("google", "").replace(
            "search for", "").replace("search", "").strip()
        if "wikipedia" in words:
            answer = search_wikipedia(query)
            print_answer(answer)
        else:
            search_result = search(query, False, google=True)
            print_answer(search_result)

    elif re.match(r"[create|set]+[ a]* reminder$", user_input_without_syntax, re.IGNORECASE):
        reminder = get_input("What's the reminder?")
        month_day_time = get_input(
            "Got it, \"" + reminder + "\". When do you want to be reminded?")
        months = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                  "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
        month = None
        for word in month_day_time.split():
            if word.lower() in months:
                month = word.lower()
                break
        date = str(datetime.now().date().year) + "-"
        if month:
            if months[month] < 10:
                month = "0" + str(months[month]) + "-"
            else:
                month = str(months[month]) + "-"
            date += month
            day = None
            time = None
            hour = None
            minutes = "00"
            if re.match(r"[a-zA-Z\s]+(\d+)[a-zA-Z\s]+(\d+[:\d]*)[a-zA-Z\s]*", month_day_time, re.IGNORECASE):
                day_time = re.findall(
                    r"[a-zA-Z\s]+(\d+)[a-zA-Z\s]+(\d+[:\d]*)[a-zA-Z\s]*", month_day_time, re.IGNORECASE)[0]
                if len(day_time) < 2:
                    print_answer(
                        "Please, provide the time in the following format: month day time. Reminder canceled")
                    return
                else:
                    day = day_time[0]
                    if len(day) < 2:
                        day = "0" + day
                    time = day_time[1]
                    if ":" in time:
                        hour = time[:time.index(":")]
                        minutes = time[time.index(":")+1:]
                        if len(minutes) < 2:
                            minutes = "0" + minutes
                    else:
                        hour = time
                    if len(hour) < 2:
                        hour = "0" + hour
                    if "pm" in month_day_time.lower():
                        hour = str(int(hour)+12)
            else:
                print_answer(
                    "You should provide the month, the day and the time. Reminder canceled.")
                return
            if day:
                date += day + " " + hour + ":" + minutes
            else:
                date += "00"
            yes = get_input("So, that's \"" + reminder + "\" on " + date + "?")
            if yes[0] == "y":
                index = len(data["reminder_threads"]) if "reminder_threads" in data else 0
                reminder_thread = threading.Thread(
                    target=check_reminder, args=(reminder, date, index))
                if "reminder_threads" in data:
                    data["reminder_threads"].append([reminder, date, index, False])
                else:
                    data["reminder_threads"] = [[reminder, date, index, False]]
                with open("data.py", "w") as file:
                    file.write("data = " + str(data))
                reminder_thread.start()
                print_answer("Reminder saved")
            else:
                print_answer("Reminder canceled")
        else:
            print_answer("Reminder canceled")
        return
    
    elif "show" in words and "reminders" in words:
        answer = ""
        index = 1
        if "reminder_threads" in data:
            for reminder in data["reminder_threads"]:
                try:
                    if not reminder[3]:
                        answer += str(index) + ". "
                        answer += reminder[0] + " on " + reminder[1] + "<br>"
                        index += 1
                except: pass
            print_answer(answer)
        else: print_answer("There are no reminders created")
        if not answer:
            print_answer("There are no reminders created")
    
    elif "cancel" in words and "reminder" in words and "all" not in words:
        index = re.findall(r"(\d+)", user_input_without_syntax)
        if index:
            index = int(index[0])
            try:
                data["reminder_threads"][index-1][3] = True
                with open("data.py", "w") as file:
                    file.write("data = " + str(data))
                print_answer("Reminder " + str(index) + " canceled")
            except: print_answer("Reminder " + str(index) + " does not exist")
        else: print_answer("You need to provide the index of the reminder")
    
    elif "cancel" in words and "reminders" in words and "all" in words:
        for i in range(len(data["reminder_threads"])):
            data["reminder_threads"][i][3] = True
        with open("data.py", "w") as file:
            file.write("data = " + str(data))
        print_answer("All reminders were canceled")

    elif user_input_without_syntax == "exit":
        with open("data.py", "w") as file:
            file.write("data = " + str(data))
        available_words = data["exit"].copy()
        available_words.remove("exit")
        available_words.remove("cya")
        available_words.remove("see you")
        available_words.remove("see ya")
        answer = random.choice(available_words).capitalize()
        print_answer(answer)
        exit()

    elif user_input_without_syntax in data["exit"]:
        available_words = data["exit"].copy()
        available_words.remove("exit")
        available_words.remove("cya")
        available_words.remove("see you")
        available_words.remove("see ya")
        answer = random.choice(available_words).capitalize()
        print_answer(answer)
        return

    elif re.match(r"[\w\W]*shut[\w\W]*", user_input_without_syntax, re.IGNORECASE) and "mouth" in words or re.match(r"[\w\W]*shut up[\w\W]*", user_input_without_syntax, re.IGNORECASE) or user_input_without_syntax == "silence" or user_input_without_syntax == "quiet" or re.match(r"[\w\W]*be quiet[\w\W]*", user_input_without_syntax, re.IGNORECASE):
        tts_off = True
        answer = "Okay"
        turnTTSOff = True
        print_answer(answer)
        return

    elif user_input_without_syntax == "what" or "say again" in user_input_without_syntax or user_input_without_syntax == "what do you say" or user_input_without_syntax == "what do you mean":
        answer = last_assistant
        print_answer(answer)
        return

    elif re.match(r"[\w\s]*say [\w\s]*something[\w\s]*", user_input_without_syntax, re.IGNORECASE):
        words = ["Hullo", "Sup", "Hulo", "Day", "Morning", "Evening", "Night", "Good morning!", "Good day!",
                 "Good evening!", "Good night!", "Yo", "Afternoon", "Good afternoon!", "Halo", "Hallo", "Howdy"]
        available_words = data["greeting"].copy()
        for word in words:
            available_words.remove(word)
        answer = random.choice(available_words)
        print_answer(answer)
        return

    elif len(user_input) == 1:
        if user_input == ")":
            answer = ")"
            print_answer(answer)
            return
        elif user_input == "(":
            answer = "("
            print_answer(answer)
            return

    # if user's input is a question
    elif question:

        if "my" in words and "name" in words:
            try:
                print_answer("Your name is " + data["name"].title())
                return
            except:
                print_answer(
                    "Sorry, but I don't yet know your name. Please, tell me, what's your name?")
                return

        elif "what" in words and "can" in words and "do" in words:
            if not tts_off:
                say_thread = threading.Thread(target=say, args=(
                    "Here are some things that I can do",))
                say_thread.start()
            answer = "Tell current weather ⛅<br>"
            answer += "Take a screenshot 📷<br>"
            answer += "Tell time ⏰<br>"
            answer += "Tell date 📅<br>"
            answer += "Perform calculations +/-/×/÷<br>"
            answer += "Open websites and apps<br>"
            answer += "Tell jokes 😉<br>"
            answer += "Send emails 📨<br>"
            answer += "Translate from and to pretty much every language A/漢<br>"
            answer += "Look up a word in dictionary 📙<br>"
            answer += "Search for people on Wikipedia<br>"
            answer += "Chat with you<br>"
            answer += "Get news from Google<br>"
            answer += "Create reminders<br>"
            answer += "Cance reminders<br>"
            answer += "Display the reminders<br>"
            answer += "Create timers ⏱<br>"
            answer += "Cancel timers<br>"
            answer += "Display the timers<br>"
            answer += "Set the brightness of the display🔆<br>"
            answer += "Search for anything you might possibly want"
            print_answer(answer)
            return

        if re.match(r"what does [\w\s]+ mean", user_input_without_syntax, re.IGNORECASE):

            search_item = user_input_without_syntax[user_input_without_syntax.index(
                "does") + len("does") + 1: user_input_without_syntax.index("mean")].strip()

            answer = search(search_item, False)
            print_answer(answer, tts=False)
            return
        else:
            if re.match(r"wh[\w]*[is\s]*[\w\s]+", user_input_without_syntax, re.IGNORECASE):
                search_item = re.findall(
                    r"wh[\w]*[is\s]*([\w\s]+)", user_input_without_syntax, re.IGNORECASE)[0]
                answer = search(
                    search_item, False if words[0] == "what" else True)
                print_answer(answer, tts=False)
                return

        if re.match(r"[\w\W]*and you[\w\W]*", user_input_without_syntax, re.IGNORECASE) or re.match(r"[\w\W]*what about you[\w\W]*", user_input_without_syntax, re.IGNORECASE):
            user_input = before_last_assistant
            user_input_without_syntax = remove_syntax(
                before_last_assistant).lower().strip()
            words = user_input_without_syntax.split()
            question, greeting, about_themselves, statement, about_it, greeting_word = recognize_type(
                user_input, user_input_without_syntax, words)
            if not question:
                user_input = last_assistant
                user_input_without_syntax = remove_syntax(
                    last_assistant).lower().strip()
                words = user_input_without_syntax.split()
                question, greeting, about_themselves, statement, about_it, greeting_word = recognize_type(
                    user_input, user_input_without_syntax, words)
            answer = generate_answer(user_input, user_input_without_syntax)
            print_answer(answer)
            return
    # if user said something about assistant
    elif about_it:

        answered = False

        for noun in words:
            if not answered:
                for word in data["bad"]:
                    if noun.startswith(word) or noun.endswith(word):
                        answer = "Please, contact @bekhruzniyazov on Tim's Discord and tell him the reason why you didn't like me. :("
                        print_answer(answer)
            else:
                break
        if not answered:
            for noun in words:
                if not answered:
                    for word in data["good"]:
                        if noun.startswith(word) or noun.endswith(word):
                            answer = random.choice(
                                ["Thanks a ton!", "Happy to help!"])
                            print_answer(answer)
        if "you" in words and "are" in words:
            print_answer(
                "I am an assistant created by Bekhruz Niyazov. Ask me \"What can you do?\" if you want to know what I am capable of.")

    # if user's input is a greeting
    elif greeting:
        answered = False

        hour = datetime.now().time().hour

        if greeting_word == "Good morning!" or greeting_word == "Morning":
            if hour > 12:
                if hour < 17:
                    answer = "It is no longer morning, I believe. It is already afternoon."
                    print_answer(answer)
                    return
                elif hour < 20 and hour > 17:
                    answer = "It is evening now. Good evening to you!"
                    print_answer(answer)
                    return
                else:
                    answer = "Good night. It's night now."
                    print_answer(answer)
                    return
            else:
                answer = "Good morning!"
                print_answer(answer)
                return

        elif greeting_word == "Good day!" or greeting_word == "Day" or greeting_word == "Good afternoon!" or greeting_word == "Afternoon":
            if hour < 12 or hour > 17:
                if hour < 12:
                    answer = "It is only morning yet, I believe. Good morning to you!"
                    print_answer(answer)
                    return
                elif hour > 17 and hour < 20:
                    answer = "It is evening now."
                    print_answer(answer)
                    return
                elif hour > 20:
                    answer = "Good night. It is night now."
                    print_answer(answer)
                    return
            else:
                answer = "Good afternoon!"
                print_answer(answer)
                return

        elif greeting_word == "Good evening" or greeting_word == "Evening":
            if hour < 17 or hour > 20:
                if hour < 12:
                    answer = "It is only morning now. Good morning!"
                    print_answer(answer)
                    return
                elif hour < 17:
                    answer = "It is not evening yet. Good day to you!"
                    print_answer(answer)
                    return
                elif hour > 20:
                    answer = "It is night now. Good night to you!"
                    print_answer(answer)
                    return
            else:
                answer = "Good evening!"
                print_answer(answer)
                return

        elif greeting_word == "Good night!" or greeting_word == "Night":
            if hour < 20 or hour > 6:
                if hour < 20:
                    answer = "It is not night yet."
                    print_answer(answer)
                    return
                elif hour > 6:
                    answer = "It is no longer night."
                    print_answer(answer)
                    return
            else:
                answer = "Good night to you!"
                print_answer(answer)
                return

        if re.match(r"[\w\W]*glad[\w\W]*see[\w\W]*you", user_input_without_syntax, re.IGNORECASE):
            answer = "Thanks"
            print_answer(answer)
            return

        if not answered:
            # answering to the user

            # if user asked "what's up?"
            if greeting_word == "What's up?" or greeting_word == "Sup":
                responses = ["Nothing", "Not much", "All right"]
                answer = random.choice(responses)
                print_answer(answer)
                return

            # if user did not ask "what's up?" but they asked "how are you" or "how do you do" or "how are you doing"
            elif greeting_word == "How are you?" or greeting_word == "How do you do?" or greeting_word == "How are you doing?":

                # creating an answer variable; at start one word will be appended to it
                answer = random.choice(["Everything is ", "I feel "])

                # creating a copy of data["good"] list
                available_words = data["good"].copy()

                # filtering the list from unwanted words
                words_to_remove = ["well", "outstanding",
                                   "terrific", "fine", "cool", "exceptional"]
                if word_to_remove not in words_to_remove and word_to_remove in available_words:
                    available_words.remove(word_to_remove.strip())
                for wrd in words_to_remove:
                    available_words.remove(wrd)
                available_words.append("really well")

                # appending a word to the answer
                answer += random.choice(available_words)

                # answering to the user
                print_answer(random.choice(
                    [answer, "I'm doing great now that I'm chatting with you. How about yourself?"]))
                return

            # if user did not ask "what's up?" nor "how are you" or "how do you do" or "how are you doing"
            else:
                # creating a copy of data["greeting"] list
                greetings = data["greeting"].copy()

                # filtering the list
                words = ["Hullo", "Sup", "Hulo", "Day", "Morning", "Evening", "Night", "Good morning!", "Good day!",
                         "Good evening!", "Good night!", "Yo", "Afternoon", "Good afternoon!", "Halo", "Hallo", "Howdy"]
                if greeting_word not in words:
                    greetings.remove(greeting_word)
                for wrd in words:
                    greetings.remove(wrd)

                greetings.append("How can I help you?")
                greetings.append("What can I help you with?")

                # answering to the user
                answer = random.choice(greetings)
                print_answer(answer)
                return

    # if user's input is a statement about themselves
    elif about_themselves:

        if re.match(r"my name is [\w\W]+", user_input, re.IGNORECASE):
            name = re.findall(
                "my name is ([\w\W]+)", user_input, re.IGNORECASE)[0]
            data["name"] = name
            with open("data.py", "w") as file:
                file.write("data = " + str(data))
            print_answer("I remembered it")
            return

        if re.match(r"i [do ]*feel [\w\s]+[,]*[\w\s]*", user_input_without_syntax, re.IGNORECASE):

            their_feelings = re.findall(
                r"i [do ]*feel ([\w\s]+)?,*[\w\s]*", user_input_without_syntax, re.IGNORECASE)[0]

            answered = False

            for word in their_feelings.split():

                word = word.strip()

                if word in data["good"] and "not" not in words:
                    print_answer("Glad you do")
                    return

                elif word in data["good"] and "not" in words:
                    print_answer(
                        "Can I cheer you up somehow? You can ask me for a joke.")
                    return

                elif word in data["bad"]:
                    print_answer(answer)
                    return

                elif word in data["bad"] and "not" in words:
                    print_answer("Glad you do")
                    return

            if not answered:
                answer = "Sorry, but I don't know what \"" + their_feelings + "\" means."
                print_answer(answer)
                return

        if re.match(r"i[anm\s]* [\w\s]+", user_input_without_syntax, re.IGNORECASE):

            answered = False

            noun = re.findall(r"i[anm\s]* ([\w\s]+)",
                              user_input_without_syntax, re.IGNORECASE)[0]

            for word in noun.split():

                word = word.strip()

                if word in data["good"]:
                    answer = "I agree with you"
                    print_answer(answer)
                    return

                elif word in data["bad"]:
                    answer = "I feel so sorry about that. Can I help you somehow?"
                    print_answer(answer)
                    return

            if not answered:
                answer = "I am sorry, but I do not know what \"" + noun + "\" means."
                print_answer(answer)
                return

        if re.match(r"my [\w\W]+ is [\w\W]+", user_input_without_syntax, re.IGNORECASE):

            noun = re.findall(r"my [\w\W]+ is ([\w\W]+)",
                              user_input_without_syntax, re.IGNORECASE)[0]

            for word in noun.split():

                if word in data["good"]:
                    available_words = data["good"].copy()
                    available_words.remove("well")
                    available_words.remove("outstanding")
                    available_words.remove("terrific")
                    available_words.remove("fine")
                    available_words.remove("cool")
                    available_words.remove("exceptional")
                    available_words.append("really well")
                    answer = random.choice(available_words).capitalize()
                    print_answer(answer)
                    return

                elif word in data["bad"]:
                    answer = ":("
                    print_answer(answer)
                    return

        if re.match(r"i am doing \w+ [\w\W]*", user_input_without_syntax, re.IGNORECASE):
            noun = re.findall(
                r"i am doing (\w+) [\w\W]*", user_input_without_syntax, re.IGNORECASE)[0]
            _not = False
            for word in data["good"]:
                if word == "not":
                    _not = True
                if word in data["good"]:
                    if _not:
                        answer = "Can I help you somehow?"
                        print_answer(answer)
                        return
                    else:
                        available_words = data["good"].copy()
                        words_to_remove = ["terrific",
                                           "exceptional", "outstanding"]
                        if word not in words:
                            available_words.remove(word)
                        for word in words_to_remove:
                            available_words.remove(word)
                        answer = "That's " + \
                            random.choice(available_words) + "!"
                        print_answer(answer)
                        return

    # if user's input is a statement
    elif statement:

        if re.match(r"my name is [\w\W]+", user_input, re.IGNORECASE):
            name = re.findall(
                "my name is ([\w\W]+)", user_input, re.IGNORECASE)[0]
            data["name"] = name
            with open("data.py", "w") as file:
                file.write("data = " + str(data))
            print_answer("I remembered it")
            return

        # creating variables that will hold information about user's input
        explanation = False

        # initializing variables that will be useful in the future
        means = False
        are = False

        if "means" in words:
            explanation = True
            means = True
        elif "is" in words or "'s" in user_input:
            explanation = True
        elif "are" in words or "'re" in user_input:
            explanation = True
            are = True

        for word in words:
            if word in data["good"] and "not" not in words:
                answer = "I feel really happy about that" if not said and "feel" not in last_assistant else random.choice(
                    [")", "Happy to help!", "Glad you like it"])
                print_answer(answer)
                said = not said
                return
            elif word in data["good"] and "not" in words:
                answer = "What's wrong?"
                print_answer(answer)
                return
            elif word in data["bad"] and "not" not in words:
                answer = "What's wrong?"
                print_answer(answer)
                return
            elif word in data["bad"] and "not" in words:
                answer = "I feel really happy about that" if not said and "feel" not in last_assistant else random.choice(
                    [")", "Happy to help!", "Glad you like it"])
                print_answer(answer)
                said = not said
                return

        if "timers" in words and "show" in words:
            answer = ""
            if timers:
                for timer in timers:
                    answer += "Timer " + str(timers.index(timer)+1) + " was created on " + str(timer[0]) + ":" + str(
                        timer[1]) + ":" + str(timer[2]) + ". It was set for " + str(timer[3]) + " seconds." + "<br>"
            else:
                answer = "There are no timers set"
            send(answer)
            return

        elif ("timer" in words or "timers" in words) and ("cancel" in words or "remove" in words):
            if re.match(r"[\w\W]*\d+[\w\W]*", user_input_without_syntax):
                index = re.findall(r"(\d+)", user_input_without_syntax)
                if index:
                    index = int(index[0])-1
                    timers[index][-1] = False
                else:
                    timers[index][-1] = False
                return
            else:
                if "all" in words:
                    for i in range(len(timers)):
                        timers[i][-1] = False
                print_answer("All timers were canceled")

        elif user_input_without_syntax == "same" or re.match("i feel[ the]* same[\w ]*", user_input_without_syntax):
            user_input = last_assistant
            user_input_without_syntax = remove_syntax(
                last_assistant).lower().strip()
            words = user_input_without_syntax.split()
            question, greeting, about_themselves, statement, about_it, greeting_word = recognize_type(
                user_input, user_input_without_syntax, words)
            answer = generate_answer(user_input, user_input_without_syntax)
            print_answer(answer)
            return

        elif re.match(r"open [\w|\s]+", user_input.lower().strip()):
            application = re.findall(
                r"open ([\w\W]+)", user_input.lower().strip())[0].strip()
            try:
                Popen[application + ".exe", ""]
            except:
                try:
                    Popen([application, ""])
                except:
                    try:
                        request = requests.get(
                            "http://" + application if not application.startswith("http") else application)
                        if request.status_code != 404:
                            webbrowser.open(application)
                    except:
                        os.system(application)

        elif re.match(r"send[(a)|(an)\s]*[(email)|(message)\s]+[(please)|(cant you)\s]", user_input_without_syntax, re.IGNORECASE):
            try:
                email = data["email"]
                password = data["password"]
            except:
                email = get_input("Please, type in your email address")
                if email.lower() == "cancel":
                    print_answer("Canceled")
                    return
                password = get_input("Please, type in your password")
                if password.lower() == "cancel":
                    print_answer("Canceled")
                    return
                remember = get_input("Do you want me to remember them? (y|n)")
                if remember.lower() == "cancel":
                    print_answer("Canceled")
                    return
                if remember == "y":
                    data["email"] = email
                    data["password"] = password
                    with open("data.py", "w") as file:
                        file.write("data = " + str(data))
            to_email = get_input(
                "Please, type the email address of a person you want to send this email to")
            if to_email.lower() == "cancel":
                print_answer("Canceled")
                return
            subject = get_input("Please, enter the subject of the email")
            if subject.lower() == "cancel":
                print_answer("Canceled")
            body = get_input("Please, enter the body of the email")
            if body.lower() == "cancel":
                print_answer("Canceled")
                return

            try:
                server = smtplib.SMTP(
                    "smtp." + email[email.index("@")+1:], 587)
                server.starttls()
                server.login(email, password)
                message = "Subject: " + subject + "\n\n" + body
                server.sendmail(email, to_email, message)
                send("Email was sent")
            except:
                data.pop("email", "")
                data.pop("password", "")
                with open("data.py", "w") as file:
                    file.write("data = " + str(data))
                answer = "Sorry, an error occurred"
                to_send_to_js = answer
                print_answer(answer)
                return

        # if user's input is an explanation:
        if explanation:
            if "remember" in user_input_without_syntax:
                user_input_without_syntax = user_input_without_syntax.replace(
                    "remember", "")
            if "that" in user_input_without_syntax:
                user_input_without_syntax = user_input_without_syntax.replace(
                    "that", "")
            if "this" in user_input_without_syntax:
                user_input_without_syntax = user_input_without_syntax.replace(
                    "this", "")
            index = None
            if means:
                index = user_input_without_syntax.index("means")
            else:
                if are:
                    index = user_input_without_syntax.index("are")
                else:
                    index = user_input_without_syntax.index("is")
            to_remember = user_input_without_syntax[:index].strip()
            length = None
            if means:
                length = len("means")
            else:
                if are:
                    length = len("are")
                else:
                    length = len("is")
            category = user_input_without_syntax[index+length:].strip()
            # if category already exists
            if category in data:
                # append the word to the category
                data[category].append(to_remember)
            # if category does not exist
            else:
                # create it and append to it the word
                data[category] = [to_remember]
            with open("data.py", "w") as file:
                file.write("data = " + str(data))
            print_answer("Got it! " + to_remember + " is " + category)
            return

        if re.match(r"[create|set]+[ a]* timer$", user_input_without_syntax, re.IGNORECASE):
            seconds = get_input("How many seconds should I set timer for?")
            if seconds.isdigit():
                seconds = int(seconds)
            else:
                answer = "Timer canceled"
                to_send_to_js = answer
                print_answer(answer)
                return

            if type(seconds) == int:
                if seconds > 0:
                    timer_thread = threading.Thread(
                        target=sleep, args=(seconds, len(timers)))
                    timers.append([datetime.now().hour, datetime.now(
                    ).minute, datetime.now().second, seconds, timer_thread, True])
                    timer_thread.start()
                    return
                else:
                    answer = "Timer was canceled"
                    print_answer(answer)
                    return

        elif re.match(r"set[ \w]* timer for [\d]*[ hours\W]*[and ]*[\d]*[ minutes\W]*[and ]*[\d]*[ seconds\W]", user_input_without_syntax, re.IGNORECASE):
            hours, minutes, seconds = 0, 0, 0
            if "hours" in words or "hour" in words:
                try:
                    hours = int(re.findall(
                        r"\s([\d]+) hour", user_input_without_syntax)[0])
                except:
                    pass
            if "minutes" in words or "minute" in words:
                try:
                    minutes = int(re.findall(
                        r"\s([\d]+) minute", user_input_without_syntax)[0])
                except:
                    pass
            if "seconds" in words or "second" in words:
                try:
                    seconds = int(re.findall(
                        r"\s([\d]+) second", user_input_without_syntax)[0])
                except:
                    pass

            time = seconds
            time += minutes * 60
            time += hours * 3600

            if time > 0:
                timer_thread = threading.Thread(
                    target=sleep, args=(time, len(timers)))
                timers.append([datetime.now().hour, datetime.now(
                ).minute, datetime.now().second, time, timer_thread, True])
                timer_thread.start()
                return
            else:
                answer = "Timer was canceled"
                print_answer(answer)
                return

        elif re.match(r"[\w\W]*thank you[\w\W]*", user_input_without_syntax, re.IGNORECASE) or user_input_without_syntax == "thanks" or user_input_without_syntax.endswith("thanks") or user_input_without_syntax.replace(" a ", " ").endswith("thanks ton") or user_input_without_syntax.startswith("thanks for"):
            answer = "You are welcome"
            print_answer(answer)
            return

        elif re.match(r"[\w\W]*nice[\w\W]to[\w\W]*you[\w\W]*", user_input_without_syntax, re.IGNORECASE):
            answer = "Thanks"
            print_answer(answer)
            return

    if not printed:
        to_send_to_js = ""


@eel.expose
def recognize_type(user_input, user_input_without_syntax, words):
    question = False
    greeting = False
    about_themselves = False
    statement = False
    about_it = False

    user_input = user_input.lower()

    # initializing variables that may become useful in the future
    greeting_word = ""
    greetings = [remove_syntax(grtng.lower()) for grtng in data["greeting"]]

    # checking if user's input is a greeting
    if user_input_without_syntax in greetings:
        greeting_word = data["greeting"][greetings.index(
            user_input_without_syntax)]
        greeting = True

    # if user's input wasn't yet recognized as a greeting
    if not greeting:
        if len(words) > 1:
            if words[1] in data["greeting"]:
                greeting_word = words[1]
                greeting = True

    # last check
    if not greeting:
        for grtng in data["greeting"]:
            if user_input_without_syntax.startswith(remove_syntax(grtng).lower() + " "):
                greeting_word = grtng
                greeting = True
                break
            elif user_input_without_syntax.endswith(" " + remove_syntax(grtng).lower()):
                greeting_word = grtng
                greeting = True

    # if user's input is not a greeting
    if not greeting:

        if len(user_input) > 2:
            for word in data["self"]:
                if word in words:
                    if word == "youre" or word == "you" and "are" in words or word == "you're":
                        about_it = True
                        break

            if not about_it:
                # if the last character in user's input is "?"
                if user_input[-1] == "?" or user_input[-2] == "?" or user_input[-3] == "?":
                    question = True

                # if user's input was not yet recognized as a question
                if not question:
                    if words[0].capitalize() in data["question_keywords"]:
                        question = True

                # last check
                if not question:
                    if re.match("[\w\W]*and you", user_input_without_syntax) or re.match("[\w\W]*what[s]* about you", user_input_without_syntax):
                        question = True

                # if user's input is not a question
                if not question:
                    # checking, if user is saying something about themselves/their feelings
                    for word in words:
                        word = word.lower()
                        if word in data["themselves"]:
                            if word == "my":
                                if "is" in words:
                                    statement = True
                            about_themselves = True
                            break

                    # if user's input is not a greeting or a question or a statement about themselves/their feelings
                    if not about_themselves:
                        statement = True

    return question, greeting, about_themselves, statement, about_it, greeting_word


if __name__ == "__main__":
    eel.start("index.html", size=(475, 750))
