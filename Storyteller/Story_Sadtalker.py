# UI界面

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import gradio as gr
import os
import sys
import subprocess
import threading
from tempfile import gettempdir
from IPython.display import Audio
import openai
import json 
import base64
import requests
from tqdm import tqdm
from moviepy.editor import *

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



# 准备一个预先准备好的 MP4 视频文件路径
mp4_file_path = "output2.mp4"

# use CHATGPT generate a story
def generate_story(input_text):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an imaginative fairy tale writer."},
        {"role": "user", "content": input_text}
        ]
    )
    return completion['choices'][0]['message']['content']
    
    
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
    
    
def generate_audio(story_text):
    polly_client = boto3.client('polly')
    s3_client = boto3.client("s3")
    
    count = 0
    text_new = story_text.split("\n")
    
    for txt in tqdm(text_new):
        if txt == "":
            continue    
        q = txt
        translate = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an excellent translator who can help me translate the recognized text and support automatic detection and mutual translation of Chinese and English content"},
                {"role": "user", "content": q}
                    ]
                )
        cn_input_text = translate['choices'][0]['message']['content']
        print(cn_input_text)
        cn_text_to_speech(cn_input_text, polly_client, s3_client, count)
        count += 1

txt2img_url = r'http://127.0.0.1:7864/sdapi/v1/txt2img'

def submit_post(url: str, data: dict):
    return requests.post(url, data=json.dumps(data))


def save_encoded_image(b64_image: str, output_path: str):
    with open(output_path, 'wb') as image_file:
        image_file.write(base64.b64decode(b64_image))

def generate_image(story_text):
    data = {'prompt': ' ',
            'negative_prompt': '',
            'sampler_index': 'DPM++ SDE',
            'seed': 1234,
            'steps': 20,
            'width': 512,
            'height': 512,
            'cfg_scale': 8}
    cnt = 0
    text_res = []
    text = story_text.split("\n")
    for txt in tqdm(text):
        if txt=="":
            continue
        data['prompt'] = "Style of painting, beautiful figures:" + txt
        text_res.append(txt)
        response = submit_post(txt2img_url, data)
        save_image_path = r'img/tmp_'+str(cnt)+'.png'
        save_encoded_image(response.json()['images'][0], save_image_path)
        cnt+=1
    
def generate_video():
    audio_folder = "audio"
    image_folder = "img"

    count = 0
    for file in os.listdir(audio_folder) :
        if file.endswith(".mp3"):
            count += 1
    
    # 获取音频文件列表
    audio_paths = [os.path.join(audio_folder, f"{i}_speech-cn.mp3") for i in range(count)]

    # 获取图片文件列表，保持与音频文件数量一致
    image_paths = [os.path.join(image_folder, f"tmp_{i}.png") for i in range(count)]
    
    # 加载音频和图片
    audios = [AudioFileClip(audio_path) for audio_path in audio_paths]
    images = [ImageClip(image_path).set_duration(audio.duration)
              for audio, image_path in zip(audios, image_paths)]


    # 设置帧率
    fps = 5  # 可以根据需要进行调整

    # 合成视频
    clips = [CompositeVideoClip([image.set_audio(audio)])
             for image, audio in zip(images, audios)]
    final_video = concatenate_videoclips(clips, method="compose")

    # 保存视频
    final_video.write_videofile(
        "output_video.mp4", fps=fps)
    
    return "output_video.mp4"
    

def generate_sadtalk(story_text):
    polly_client = boto3.client('polly')
    s3_client = boto3.client("s3")
    
    
    count = 100
    cn_text_to_speech(story_text, polly_client, s3_client, count)
    
    res = subprocess.call(['python', 'inference.py',
          '--driven_audio', 'audio/100_speech_cn.mp3' ,
           '--source_image','mom.png',
           '--result_dir', './output'])
    print('return: ',res)
    return res
    

def generate_mp4(input_text):
    
    story_text = generate_story(input_text)
    
    
    thread1 = threading.Thread(target=generate_audio, args = (story_text,))
    thread2 = threading.Thread(target=generate_image, args = (story_text,))
    # thread3 = threading.Thread(target=generate_sadtalk,args = (story_text,))

    thread1.start()
    thread2.start()
    # thread3.start()

    thread1.join()
    thread2.join()
    # thread3.join()
    
    # generate_audio(story_text)
    # generate_image(story_text)
    
    return generate_video(),generate_sadtalk(story_text)

    
    
iface = gr.Interface(
    fn=generate_mp4,
    inputs="text",
    
    outputs=[
        gr.Video(label="Out"),
            gr.Video(label="Out2")],
    live=False,
    title="Storyteller",
    description="Generate a story video based on the given input text.",
    examples=[
        ["Please help me continue the story, the background is a little girl in the forest, separated by paragraphs"]
    ]
)


    
# demo = gr.Blocks()
# with demo:
#     au

if __name__ == "__main__":
    iface.launch()