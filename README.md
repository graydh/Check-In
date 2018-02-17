# Check-In
Winner of Hack Umass V Best Hardware Hack


CheckIn is designed to help elderly people, especially those living alone or living with a degenerative brain disease, to remember what they need to do day-to-day. Additionally, if a CheckIn fails, a child or caretaker is immediately notified via FaceBook so they can take the appropriate steps to ensure their charge's wellbeing. On the caretaker's end, CheckIn is an app that allows them to set a time to check in and an accompanying message. On elderly person's end, CheckIn is run as a background script so that the person does not have to remember to check their phone. When it is time for a CheckIn, the Python script uses Amazon Polly text-to-speech to communicate with the person and deliver the CheckIn message. The person can then respond out loud; the script uses Sphinx CMU to determine whether the person has responded in the affirmative. If three subsequent prompts do not result in an affirmative response, the script alerts the caretaker. The database of people and their caretakers and scheduled alerts is stored in a JSON file on Dropbox.

Our thanks to the organizers, mentors and sponsors of Hack UMass V, and to Major League Hacking.
