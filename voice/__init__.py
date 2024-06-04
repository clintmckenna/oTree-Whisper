from otree.api import *
import openai
import boto3
import base64
import os
import io
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

            # load s3 bucket environment
            s3_client = boto3.client('s3',
                aws_access_key_id=os.environ.get('ACCESS_KEY'),
                aws_secret_access_key=os.environ.get('SECRET_KEY')
            )

            # get filename
            filename = str(player.session.code) + '_' + str(player.id_in_group) + '.webm'


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
                client = openai.OpenAI(api_key = OPENAI_KEY)

                # load audio data
                # audio_file = open(filepath_webm, "rb") # if using file saved on server
                audio_file = s3_client.get_object(Bucket='otreewhisper', Key=filename)
                audio_data = audio_file['Body'].read()
                
                # create file-like object for requests
                audio_object = io.BytesIO(audio_data)
                files = {'file': audio_object}

                # Send the file-like object to Whisper API for transcription using requests
                response = requests.post(
                    url = 'https://api.openai.com/v1/audio/transcriptions',
                    headers = {'Authorization': f'Bearer {OPENAI_KEY}'},
                    files={"file": (filename, audio_data, "audio/webm")},
                    data={'model': 'whisper-1'}
                )

                # preview and write to player vars
                output = dict(response.json())
                print(output['text'])
                player.transcript = output["text"]    


                # run audio through api (old version from server file)
                # transcript = client.audio.transcriptions.create(
                #     model = "whisper-1",
                #     file = audio_data
                # )

                # # preview and write to player vars
                # output = dict(transcript)
                # print(output["text"])
                # player.transcript = output["text"]    
                
                
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
            path = str(player.session.code) + '_' + str(player.id_in_group) + '.webm',
            s3_accessKeyId = os.environ.get('ACCESS_KEY'),
            s3_secretAccessKey = os.environ.get('SECRET_KEY')
        )
 

page_sequence = [
    record, 
]
