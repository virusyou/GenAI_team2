## 11:22
## 尝试放弃图片视频的音频，只用sadtalker的音频
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
import time

bucket_name = 'aigc-bj-team2'

openai.api_key="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"

q = "Please help me continue the story, the background is a little girl in the forest, separated by paragraphs"

story_type = {
    "美好童话": "You are an imaginative fairy tale writer.",
    "恐怖故事": "Create a chilling and suspenseful horror story.",
    "冷笑话": "Provide me with a dry and witty joke and its answer"
}

image_type = {
    "美好童话": "lora:flower_field_10k:1.1 hypernet:forest_5k:0.8, style of painting:1.0, beautiful figures:",
    "恐怖故事": "Suspenseful horror, chilling",
    "冷笑话": "Funny scene"
}

story_length = {
    "短": "generate a short fairy tale story within 50 words",
    "中": "generate a short fairy tale story within 100 words",
    "长": "generate a short fairy tale story within 150 words"
}

story_age = {
    "小孩": "You are an imaginative fairy tale writer.",
    "成年人": "Create a chilling and suspenseful horror story.",
    "老年人": "Generate a witty and light-hearted cold joke for me"
}


'''
["一个小女孩在森林中", "美好童话", "短", "小孩"],
        ["一个小男孩在海边", "美好童话", "中", "小孩"],
        ["在一个古老的王国里", "恐怖故事", "短", "成年人"]
'''

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
mp4_file_path = "output_video.mp4"
SadTalker_output_file = "./output/SadTalker_result.mp4"



# use CHATGPT generate a story
def generate_story(input_text, mode, length):
    
    q = input_text
    translate = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "将输入内容翻译成英文"},
            {"role": "user", "content": q}
                ]
            )
    new_text = translate['choices'][0]['message']['content']
    
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": story_type[mode] + "Starting with the content I input," + story_length[length]},
        {"role": "user", "content": new_text}
        ]
    )
    return completion['choices'][0]['message']['content']
    
    
def cn_text_to_speech(input_text, polly_client, s3_client, index,output_dir):
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
                    subprocess.call(["aws", "s3", "cp", "s3://aigc-bj-team2/speech-cn.mp3",output_dir+str(index) + "_speech-cn.mp3"])
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
    
    tmp_all_sentences = ""
    count = 0
    text_new = story_text.split(".")
    
    for txt in tqdm(text_new):
        if txt == "":
            continue    
        q = txt
        translate = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Translate input content into Chinese"},
                {"role": "user", "content": q}
                    ]
                )
        cn_input_text = translate['choices'][0]['message']['content']
        print(cn_input_text)
        tmp_all_sentences = tmp_all_sentences+cn_input_text
        
        cn_text_to_speech(cn_input_text, polly_client, s3_client, count,"audio/")
        count += 1
        
    file_handle=open('all_cn_sentences.txt',mode='w')
    file_handle.write(tmp_all_sentences)
    file_handle.close()
        
txt2img_url = r'http://127.0.0.1:7860/sdapi/v1/txt2img'

def submit_post(url: str, data: dict):
    return requests.post(url, data=json.dumps(data))


def save_encoded_image(b64_image: str, output_path: str):
    with open(output_path, 'wb') as image_file:
        image_file.write(base64.b64decode(b64_image))

def generate_image(story_text, mode, length):
    data = {'prompt': ' ',
            'negative_prompt': 'poorly drawn face, incongruous colors and deformed body',
            'sampler_index': 'DPM++ SDE',
            'seed': 1234,
            'steps': 20,
            'width': 512,
            'height': 512,
            'cfg_scale': 8}
    cnt = 0
    text_res = []
    text = story_text.split(".")
    for txt in tqdm(text):
        if txt=="":
            continue
        data['prompt'] = image_type[mode] + txt
        # data['prompt'] = "lora:cutescrap05v_cutescrap3.safetensors, style of painting, beautiful figures:" + txt
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
    # clips = [CompositeVideoClip([image.set_audio(audio)])
    #          for image, audio in zip(images, audios)]
    clips = [CompositeVideoClip([image])
             for image in images]
    final_video = concatenate_videoclips(clips, method="compose")

    # 保存视频
    final_video.write_videofile(
        "output_video.mp4", fps=fps)
    
        # 循环遍历文件列表并删除文件
    for filename in audio_paths:
        if os.path.isfile(filename):
            os.remove(filename)

    # 循环遍历文件列表并删除文件
    for filename in image_paths:
        if os.path.isfile(filename):
            os.remove(filename)
    
    return "output_video.mp4"
    
    
    
def generate_sadtalk():
    polly_client = boto3.client('polly')
    s3_client = boto3.client("s3")
    
    f = open('all_cn_sentences.txt')
    cn_all_sentences = f.readlines()
    cn_all_sentences = cn_all_sentences[0]
    count = 100
    print("\n cn_all_sentences : ",cn_all_sentences)
    cn_text_to_speech(cn_all_sentences, polly_client, s3_client, count,"")
    
    subprocess.call(['python', 'inference.py',
          '--driven_audio', '100_speech-cn.mp3' ,
           '--source_image','girl.png',
           '--result_dir', './output'])
    print('return st_file: ',SadTalker_output_file)
    return SadTalker_output_file



def generate_mp4(input_text, mode, length, age):
    
    
    # print(mode)
    
    story_text = generate_story(input_text, mode, length)
    
    thread1 = threading.Thread(target=generate_audio, args = (story_text,))
    thread2 = threading.Thread(target=generate_image, args = (story_text, mode, length, ))

    thread1.start()
    thread2.start()

    thread1.join() 
    thread2.join()
    
    generate_video()
    print("finish story video generation")
    generate_sadtalk()
    print("finish sadtalker video generation")
    mp4_file_path = "output_video.mp4"
    SadTalker_file_path = "./output/SadTalker_result.mp4"
    clip1 = VideoFileClip(mp4_file_path)
    size = (int(clip1.size[0]/40.0)*10, int(clip1.size[1]/40.0)*10)
    clip2 = VideoFileClip(SadTalker_file_path).resize(
        size).set_position((0, clip1.size[1]-size[1]))#.without_audio()   # 移动到左下角
    
    clip2.set_duration(clip1.duration)
#     target_duration = clip1.duration
#     repeats = int(target_duration / clip2.duration)
#     # 重复短视频帧以达到目标时长
#     long_video = clip2
#     if repeats>0: repeats-=1
#     mod_time = target_duration % clip2.duration

#     while repeats:
#         long_video = concatenate_videoclips([long_video, clip2])
#         repeats-=1
   
#     clip2 = clip2.set_duration(mod_time)
#     long_video = concatenate_videoclips([long_video, clip2])
    
    # CompositeVideoClip([clip1, long_video]).write_videofile(r'result.mp4')
    
    CompositeVideoClip([clip1, clip2]).write_videofile(r'result.mp4')
    mp4_file_path = "result.mp4"
    # generate_audio(story_text)
    # generate_image(story_text)
    
        
    return mp4_file_path

iface = gr.Interface(
    fn=generate_mp4,
    inputs=[
        "text",
        gr.Radio(["美好童话", "恐怖故事", "冷笑话"], label="故事类型",
                 info="选择故事类型"),
        gr.Radio(["短", "中", "长"], label="故事时长",
                 info="选择故事时长"),
        gr.Radio(["小孩", "成年人", "老年人"], label="您的年龄",
                 info="选择您的年龄"),
    ],
    outputs="video",

    live=False,  # 实时更新

    title="故事大王 StoryGen",
    description="请输入您需要续写的故事：",
    examples=[
        ["一个小女孩在森林中", "美好童话", "短", "小孩"],
        ["一个小男孩在海边", "美好童话", "中", "小孩"],
        ["在一个古老的王国里", "恐怖故事", "短", "成年人"]
    ]
)

if __name__ == "__main__":
    iface.queue().launch()