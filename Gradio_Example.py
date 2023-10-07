'''
Prerequisite: Run the following commands on your Amazon Linux 2 terminal (or equivalent commands on other operating system):

pip3 install gradio

pip3 install boto3

curl -O https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz &&
mkdir -p ffmpeg-release &&
tar Jxf ffmpeg-release-amd64-static.tar.xz —strip-components=1 -C ffmpeg-release &&
PATH=$(readlink -f ffmpeg-release):$PATH
'''

import gradio as gr
import boto3
import time
import json

bucket_name = 'aigc-bj-team2'

def upload_to_s3(file_path, bucket):
    object_name = "example.wav" # unique in a bucket
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_path, bucket, object_name)
    except:
        return False
    return "s3://"+bucket+"/"+object_name

def get_transcript(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    response_json = json.loads(obj['Body'].read())
    transcript = response_json['results']['transcripts'][0]['transcript']
    return transcript
    
def transcribe(audio):
    bucket = bucket_name
    s3_url = upload_to_s3(audio, bucket)
    # create a transciption job
    job_name = "ExampleJob" + str(time.time()) # a unique name in your Amazon Transcribe
    transcribe_client = boto3.client('transcribe')
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': s3_url},
        MediaFormat='wav',
        LanguageCode='en-US',
        OutputBucketName=bucket,
        OutputKey='example_text.txt'
    )
    max_tries = 100
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']
        if job_status in ['COMPLETED', 'FAILED']:
            print(f"Job {job_name} is {job_status}.")
            if job_status == 'COMPLETED':
                transcript = get_transcript(bucket,'example_text.txt')
                return transcript
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)
    return "Fail"

gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(source="upload", format="wav", type="filepath"),
    outputs="text").launch()





