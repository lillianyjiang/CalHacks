import numpy as np
import re
from colorama import Fore, Style

EMOTIONS = np.array([
    "admiring", "adoring", "appreciative", "amused", "angry", "anxious", "awestruck", "uncomfortable", "bored", "calm",
    "focused", "contemplative", "confused", "contemptuous", "content", "hungry", "determined", "disappointed",
    "disgusted", "distressed", "doubtful", "euphoric", "embarrassed", "disturbed", "entranced", "envious", "excited",
    "fearful", "guilty", "horrified", "interested", "happy", "enamored", "nostalgic", "pained", "proud", "inspired",
    "relieved", "smitten", "sad", "satisfied", "desirous", "ashamed", "negatively surprised", "positively surprised",
    "sympathetic", "tired", "triumphant"
])

NEGATIVE_EMOTIONS = np.array([
    "Angry", "Anxious", "Uncomfortable", "Sadness", "Contempt", "Bored", "Pain", "Pained",
    "Confused", "Hungry", "Disappointed", "Disgusted", "Distressed", "Doubtful", "Embarrassed", "Disturbed", "Fearful", "Guilty", "Horrified", "Pained", "Sad", "Satisfied", "Ashamed", "Negatively Surprised", "Tired"])


emotion_history = []
distress_list = []
pain_list = []


def create_message(user_message=None, user_emotion=None): 
    #  Initially the patient looked {user_emotion[0]}, then {user_emotion[1]}."

    return f"Nurse Doski! Your patient has a distress score of '{np.round(np.mean(distress_list), 2) * 100}'! Your patient has a pain score of '{np.round(np.mean(pain_list), 2) * 100}' amout out of 100. The patient says, '{user_message}'."



def find_max_emotion(predictions):

    def get_adjective(score):
        if 0.26 <= score < 0.35:  
            return "slightly"
        elif 0.35 <= score < 0.44:
            return "somewhat"
        elif 0.44 <= score < 0.53:
            return "moderately"
        elif 0.53 <= score < 0.62:
            return "quite"
        elif 0.62 <= score < 0.71:
            return "very"
        elif 0.71 <= score <= 3:
            return "extremely"
        else:
            return ""

    if len(predictions) == 0:
        return ["calm", "bored"]

    def process_section(section):
        global distress_list
        emotion_predictions = []
        for frame_dict in section:
            #print("frame dict", frame_dict)
            if 'predictions' not in frame_dict['face']:
                continue
            frame_emo_dict = frame_dict['face']["predictions"][0]["emotions"]
            emo_dict = {}
            distress_dict = {}
            pain_dict = {}
            for x in frame_emo_dict:
                emo_dict[x["name"]] = x["score"]
                if x["name"] in NEGATIVE_EMOTIONS:
                    distress_dict[x["name"]] = x["score"]
                if x["name"] in ["Pain", "Pained"]:
                    pain_dict[x["name"]] = x["score"]
                
            
            emo_frame = sorted(emo_dict.items())

            distress_frame = distress_dict.items()
            pain_frame = pain_dict.items()
            emo_frame = np.array([x[1] for x in emo_frame])
            distress_frame = np.array([x[1] for x in distress_frame])
            pain_frame =  np.array([x[1] for x in pain_frame])
            emotion_predictions.append(emo_frame)
        
            distress_list.append(np.average(distress_frame))
            pain_list.append(np.average(pain_frame))
            
        if len(emotion_predictions) == 0:
            return 'calm'
        # Assuming 'emotion_predictions' is a 2D array
        mean_predictions = np.array(emotion_predictions).mean(axis=0)
        # Get the index of the highest value
        top_index = np.argmax(mean_predictions)

        # Add adjectives to the top emotion based on the prediction score
        top_emotion_adjective = f"{get_adjective(mean_predictions[top_index])} {EMOTIONS[top_index]}"
                
        return top_emotion_adjective

    # Split predictions into 2 sections
    section_size = len(predictions) // 2
    sections = [predictions[i * section_size:(i + 1) * section_size] for i in range(2)]

    # Get top emotion for each section
    top_emotions = [process_section(section) for section in sections]
    return top_emotions

def store_emotions(result):
    emotion_history.append(result)


def message(transcription):
    global emotion_history
    user_emotions = find_max_emotion(emotion_history)
    message = create_message(transcription, user_emotions)
    print(Fore.GREEN + "PROMPT:", message + Style.RESET_ALL)
    #response = re.sub(r'\([^)]*\)', '', response)
    #response = re.sub(r'\[.*?\]', '', response)
    #response = re.sub(r'^"|"$', '', response)
    #print(Fore.CYAN + "JOAQUIN:", response + Style.RESET_ALL)
    emotion_history = []
    return message
