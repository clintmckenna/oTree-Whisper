from otree.api import *
import openai
import base64
import os

doc = """
voice transcription with whisper api
"""


class C(BaseConstants):
    NAME_IN_URL = 'voice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    base64 = models.LongStringField(blank=True)
    transcript = models.LongStringField(blank=True)


# PAGES
class record(Page):
    form_model = 'player'
    form_fields = ['base64']
    
    @staticmethod
    def live_method(player: Player, data):
        
        # functions for retrieving text from openAI
        if 'text' in data:
           
            # grab base64 text and decode
            text = data['text']
            b64 = base64.b64decode(text)

            # save current base64 text
            player.base64 = data['text']

            # make files directory in static   
            path = 'voice/static/voice/audio/'
            while not os.path.exists(path):
                os.mkdir(path) 
            
            # save webm to file
            filepath_webm = path + str(player.id_in_group) + '.webm'
            webm_file = open(filepath_webm, "wb")
            webm_file.write(b64)


            # Whisper API functions
            try:
                
                # openAI key (saved as environment variable)
                OPENAI_KEY = os.environ.get('CHATGPT_KEY')
                # or if you want to just paste it in...
                # OPENAI_KEY = "sk-..."
                
                client = openai.OpenAI(api_key = OPENAI_KEY)

                # perform analysis on the loaded audio
                audio_file = open(filepath_webm, "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )

                # preview and write to player vars
                output = dict(transcript)
                print(output["text"])
                player.transcript = output["text"]    
                
                
            except Exception as e:
                print("error loading wav file:", e)

            return {player.id_in_group: output}  
        else: 
            pass

    @staticmethod
    def before_next_page(player, timeout_happened):
        return {
        }
    
    @staticmethod
    def js_vars(player):
        return dict(
            path = 'voice/audio/' + str(player.id_in_group) + '.webm'
        )
 

page_sequence = [
    record, 
]
