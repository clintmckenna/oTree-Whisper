from otree.api import *
import boto3
import base64
import os
import requests

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

            # save webm to file (not advised for security reasons!)
            # # make files directory in static   
            # path = 'voice/static/voice/audio/'
            # while not os.path.exists(path):
            #     os.mkdir(path) 
            # # save webm
            # filepath_webm = path + str(player.id_in_group) + '.webm'
            # webm_file = open(filepath_webm, "wb")
            # webm_file.write(b64)


            # you can remove the amazon s3 bucket code if you do not want to save any files
            # create filename format: (sessioncode)_(player id in group).webm
            filename = str(player.session.code) + '_' + str(player.id_in_group) + '.webm'

            # load s3 bucket environment
            s3_client = boto3.client('s3',
                aws_access_key_id=os.environ.get('ACCESS_KEY'),
                aws_secret_access_key=os.environ.get('SECRET_KEY')
            )

            # save webm to s3
            s3_client.put_object(
                Bucket='otreewhisper',
                Key=filename,
                Body= b64
            )   

            # Whisper API functions
            try:
                
                # openAI key (saved as environment variable)
                OPENAI_KEY = os.environ.get('CHATGPT_KEY')
                # or if you want to just paste it in...
                # OPENAI_KEY = "sk-..."

                # Send the file-like object to Whisper API for transcription using requests
                response = requests.post(
                    url = 'https://api.openai.com/v1/audio/transcriptions',
                    headers = {'Authorization': f'Bearer {OPENAI_KEY}'},
                    files={"file": (filename, b64, "audio/webm")}, # base64 decoded data sent directly
                    data={'model': 'whisper-1'}
                )

                # preview and write to player vars
                output = dict(response.json())
                print(output['text'])
                player.transcript = output["text"]    
                
            except Exception as e:
                print("error loading audio file:", e)

            return {player.id_in_group: output}  
        else: 
            pass

page_sequence = [
    record, 
]
