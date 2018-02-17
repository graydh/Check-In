#MAIN2 uses the original user base file format

import speech_recognition as sr
import pyaudio
from boto3 import client
from contextlib import closing
import subprocess

import json
from time import gmtime, strftime
import time

import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

from boto3 import client
from contextlib import closing
from fbchat import Client
from fbchat.models import *
 
filename = "db.json"
name = "Brian"

# Setup Amazon web service client for text to speech
polly = client("polly", 'us-east-1', aws_access_key_id="KEY_ID", aws_secret_access_key="ACESS_KEY")
# For Speech Recognition
r = sr.Recognizer()
r.energy_threshold = 3000 #crank up to 4000 if super noisy
r.operation_timeout = 6 #number of seconds before speech recognition timeout

client = Client('EMAIL', 'PSSWD')
chatid = "CHAT_ID"

CHECK_AGAIN = 0
CONTACT = 1
BE_NICE = 2

nextSpokenOutput = ""

# Add OAuth2 access token here.
TOKEN = 'DROPBOX_TOKEN'

LOCALFILE = 'db.json'
BACKUPPATH = '/db.json'

def getSpeechtoText():
    #   ***WORKING***
    # Must have r=sr.Recognizer() before this function called
    # Similar to recordAudioGooglespeech only using local sphinx speech to text
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        
        print("Say something!")
        audio = r.listen(source)
    data = ""
    # recognize speech using Sphinx
    try:
        data = r.recognize_sphinx(audio)
        print("You: " + data)
    except sr.UnknownValueError:
        print("Sphinx could not understand audio")
    except sr.RequestError as e:
        print("Sphinx error; {0}".format(e))
    return data

def speak(wordstosay):
    #	***WORKING***
    # Turning text into speech
    # this function creates a polly Amazon web services voice and speaks with that voice with the name as input
    response = polly.synthesize_speech(Text=wordstosay, OutputFormat="mp3", VoiceId=name)
    # US: Joanna, Female: Salli, Female: Kimberly, Female: Kendra, Female: Ivy, Female: Justin, Male: Joey, Male
    # British: Emma, Female: Amy, Female: Brian, Male
    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            data = stream.read()
            fo = open("/Locationofpollyspeechfile/pollyspeech.mp3", "w+")
        fo.write(data)
        fo.close()

    # output speech file - always same file
    inputstring = ["afplay", "/locationofpollyspeechfile/pollyspeech.mp3"]
    subprocess.call(inputstring)

    return;

def contactCaretaker():
    currenttimearray = getCurrentTime()
    stringtime = ''.join(str(currenttimearray))
    sendFacebookMsg("Notification at " + stringtime + " failed to recieve an affirmative response.")
    return

def isAffirmative(spokenWords):
    spokenWords = spokenWords.lower()
    if (spokenWords.find("yes") & spokenWords.find("yeah") & spokenWords.find("yep") != -1):
        return True
    else:
        return False

def getInput():
    return getSpeechtoText()

def isInputAffirmative():
    return isAffirmative(getInput())

def setNextOutput(action):
    global nextSpokenOutput
    if action == CHECK_AGAIN:
        nextSpokenOutput = "Have you received this reminder?"
    elif action == CONTACT:
        nextSpokenOutput = "I'm worried that you're not ok. I'm reaching out to someone who can help you."
    elif action == BE_NICE:
        nextSpokenOutput = "Great! Have a nice day."
    return

def determineAction():
    affirmativeResponse = isInputAffirmative()
    attemptNumber = 0
    while not affirmativeResponse:
        attemptNumber += 1
        if attemptNumber >= 3:
            contactCaretaker()
            setNextOutput(CONTACT)
            speak(nextSpokenOutput)
            return
        else:
            setNextOutput(CHECK_AGAIN)
            speak(nextSpokenOutput)
            affirmativeResponse = isInputAffirmative()
    if affirmativeResponse:
        setNextOutput(BE_NICE)
        speak(nextSpokenOutput)
        return

def readDatabase(file, desiredUsername):
    # returns the desired user object from the indicated file and desiredUsername
    f = open(file, 'r')
    filetext = f.read()
    jsondata = json.loads(filetext)
    f.close()
    usernameIndex = getIndex(desiredUsername, jsondata)
    return jsondata[usernameIndex]

def readDatabaseMessage(file, desiredUsername, index):
    f = open(file, 'r')
    filetext = f.read()
    jsondata = json.loads(filetext)
    f.close()
    return(jsondata[index]["reminders"][0]["message"])

    #userdata = readDatabase(file, desiredUsername)
    #return userdata["reminders"][0]["message"]

def readDatabaseTime(file, desiredUsername, index):
    userdata = readDatabase(file, desiredUsername)
    return userdata["reminders"][0]["time"]

def parseTimefromString(timeString):
    # The time must be in the format HH:MM
    hourtemp = int(timeString[:2])
    minutetemp = int(timeString[3:5])
    timeArray = [hourtemp, minutetemp]
    return timeArray
    # seperate hour and minute pieces

    # a seperate function will need to compare all times

def getCurrentTime():
    currentTimeString = strftime("%H:%M", gmtime())
    timeArray = currentTimeString.split(":")
    if(int(timeArray[0]) > 5):
        hourtemp = int(timeArray[0]) - 5
    else:
        hourtemp = (24 - (5 - int(timeArray[0])))
    minutetemp = int(timeArray[1])
    timeArray = [hourtemp, minutetemp]
    return timeArray

def isSooner(time1, time2):
    currentTime = getCurrentTime()

    ht1 = time1[0]
    ht2 = time2[0]
    mt1 = time1[1]
    mt2 = time2[1]

    if ht1 * 60 + mt1 <= currentTime[0] * 60 + currentTime[1]:
        ht1 += 24
    if ht2 * 60 + mt2 <= currentTime[0] * 60 + currentTime[1]:
        ht2 += 24
    if ht1 > ht2:
        return False
    elif ht1 < ht2:
        return True
    else:
        if mt1 < mt2:
            return True
        else:
            return False




def getIndexOfNextReminder(reminderTimes):
    # Where reminderTimes is the array of times
    currentTime = getCurrentTime()
    indexOfNextReminder = 0
    timeOfNextReminder = reminderTimes[0]
    index = 0
    for time in reminderTimes:
        if isSooner(time, timeOfNextReminder):
            indexOfNextReminder = index
            timeOfNextReminder = time
        index += 1
    #print(indexOfNextReminder)
    return indexOfNextReminder

def makeReminderArray(username):
    with open(filename, "r") as data_file:
        data = json.load(data_file)

    reminderArray = []

    #userIndex = getIndex(username, data)
    index = 0

    for reminder in data:
        time = reminder['reminders'][0]['time']
        time = parseTimefromString(time)
        reminderArray.append(time)
    data_file.close()
    return reminderArray

def getIndex(name, database):
    # find the index number of a username within our json database
    index = 0
    for jsonObject in database:
        currentName = database[0]['username']
        if (currentName == name):
            return index
        else:
            index += 1
    return -1


#-Dropbox Methods

# Uploads contents of LOCALFILE to Dropbox
def backup():
    with open(LOCALFILE, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        print("Uploading " + LOCALFILE + " to Dropbox as " + BACKUPPATH + "...")
        try:
            dbx.files_upload(f.read(), BACKUPPATH, mode=WriteMode('overwrite'))
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                sys.exit("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
                sys.exit()
            else:
                print(err)
                sys.exit()

# Change the text string in LOCALFILE to be new_content
# @param new_content is a string
def change_local_file(new_content):
    print("Changing contents of " + LOCALFILE + " on local machine...")
    with open(LOCALFILE, 'wb') as f:
        f.write(new_content)

# Restore the local and Dropbox files to a certain revision
def restore(rev=None):
    # Restore the file on Dropbox to a certain revision
    print("Restoring " + BACKUPPATH + " to revision " + rev + " on Dropbox...")
    dbx.files_restore(BACKUPPATH, rev)

    # Download the specific revision of the file at BACKUPPATH to LOCALFILE
    print("Downloading current " + BACKUPPATH + " from Dropbox, overwriting " + LOCALFILE + "...")
    dbx.files_download_to_file(LOCALFILE, BACKUPPATH, rev)

# Look at all of the available revisions on Dropbox, and return the oldest one
def select_revision():
    # Get the revisions for a file (and sort by the datetime object, "server_modified")
    print("Finding available revisions on Dropbox...")
    entries = dbx.files_list_revisions(BACKUPPATH, limit=5).entries
    revisions = sorted(entries, key=lambda entry: entry.server_modified)

    #for revision in revisions:
        #print(revision.rev, revision.server_modified)

    # Return the oldest revision (first entry, because revisions was sorted oldest:newest)
    return revisions[len(revisions)-1].rev

def pullMostRecentFile():
    #Downloads the most recent file from dropbox and replaces the local file
    to_rev = select_revision()
    print to_rev
    restore(to_rev)

def sendFacebookMsg(message):
    client.sendMessage(message, thread_id = chatid)

#---------------------------------------------------------
currentUser = "oldman"
dbx = None
def main():
    #print("Creating a Dropbox object...")
    global dbx
    dbx = dropbox.Dropbox(TOKEN)
    #pullMostRecentFile()

    to_rev = select_revision()
    print to_rev
    restore(to_rev)
    timesArray = makeReminderArray(currentUser)
    #print timesArray
    #print timesArray
    #print "!!!!!!!!!!!!!"
    nextReminderIndex = getIndexOfNextReminder(timesArray)
    #print(nextReminderIndex)
    nextReminderTimeArray = timesArray[nextReminderIndex]
    nextTimeString = ''.join(str(nextReminderTimeArray))
    nextMessage = readDatabaseMessage(filename, currentUser, nextReminderIndex)
    #print(nextMessage)
    while (True):
        to_rev = select_revision()
        print to_rev
        restore(to_rev)
        currentTimeArray = getCurrentTime()
        print("Current time")
        print currentTimeArray
        print "------"
        print("Time of next reminder")
        print nextReminderTimeArray
        if ((currentTimeArray[0] == nextReminderTimeArray[0]) & (
            currentTimeArray[1] == nextReminderTimeArray[1])):  
            # check if the next reminder time is now
            # if the times are equal, then try to get vocal confirmation
            speak(nextMessage)
            determineAction()
            time.sleep(30)
        timesArray = makeReminderArray(currentUser)
        nextReminderIndex = getIndexOfNextReminder(timesArray)
        nextTimeString = ''.join(str(nextReminderTimeArray))
        nextReminderTimeArray = timesArray[nextReminderIndex]
        nextMessage = readDatabaseMessage(filename, currentUser, nextReminderIndex)
        time.sleep(2)
main()
