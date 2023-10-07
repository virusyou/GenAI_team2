import boto3

from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir

from IPython.display import Audio

import openai
import json 
import base64
import requests
from tqdm import tqdm
import time

bucket_name = 'aigc-bj-team2'

openai.api_key="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"

q = "Please help me continue the story, the background is a little girl in the forest, separated by paragraphs"

completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are an imaginative fairy tale writer."},
        {"role": "user", "content": q}
        # {"role": "user", "content": "Who won the world series in 2020?"},
        # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        # {"role": "user", "content": "Where was it played?"}
    ]
)


    
def en_text_to_speech(input_text, polly_client, s3_client, index):
    try:
        # Request speech synthesis
        response = polly_client.synthesize_speech(Text=input_text, OutputFormat="mp3",
                                            VoiceId="Joanna")
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)
    
    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            output = os.path.join(gettempdir(), str(index) + "_speech.mp3")

            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
                    print("Written to %s" % output)
                    s3_client.upload_file(output, bucket_name, "speech-en.mp3")
                    # download audio file from s3 
                    subprocess.call(["aws", "s3", "cp", "s3://aigc-bj-team2/speech-en.mp3", "audio/"+str(index) + "_speech-en.mp3"])
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                sys.exit(-1)
    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)

def cn_text_to_speech(input_text, polly_client, s3_client, index):
    try:
        # Request speech synthesis
        response = polly_client.synthesize_speech(Text=input_text, OutputFormat="mp3",
                                            VoiceId="Zhiyu")
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)
    
    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            output = os.path.join(gettempdir(), str(index) + "_speech.mp3")

            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
                                        
                    print("Written to %s" % output)
                    s3_client.upload_file(output, bucket_name, "speech-cn.mp3")
                    # download audio file from s3 
                    subprocess.call(["aws", "s3", "cp", "s3://aigc-bj-team2/speech-cn.mp3", "audio/"+str(index) + "_speech-cn.mp3"])
                    
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                sys.exit(-1)
    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)
        
def main():
    global text
    
    count = 0
    # text = completion['choices'][0]['message']['content']
    text_new = text.split("\n")
    
    polly_client = boto3.client('polly')
    s3_client = boto3.client("s3")
    
    for txt in tqdm(text_new):
        if txt == "":
            continue    

        # en_input_text = txt
        q = txt
        
        translate = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an excellent translator who can help me translate the recognized text and support automatic detection and mutual translation of Chinese and English content"},
                {"role": "user", "content": q}
                # {"role": "user", "content": "Who won the world series in 2020?"},
                # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                # {"role": "user", "content": "Where was it played?"}
                    ]
                )

        cn_input_text = translate['choices'][0]['message']['content']
        print(cn_input_text)
                
        # en_text_to_speech(en_input_text, polly_client, s3_client, count)
        # count += 1

        cn_text_to_speech(cn_input_text, polly_client, s3_client, count)
        count += 1

if __name__ == '__main__':
    main()