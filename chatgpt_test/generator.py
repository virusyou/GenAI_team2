import openai
import json 
import base64
import requests
from tqdm import tqdm

openai.api_key="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"

def text_generator(query):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an imaginative fairy tale writer."},
            {"role": "user", "content": query}
            # {"role": "user", "content": "Who won the world series in 2020?"},
            # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            # {"role": "user", "content": "Where was it played?"}
        ]
    )
    # Print out the model's response
    text = completion['choices'][0]['message']['content']
    text = text.split("\n")
    text_res = []
    for txt in text:
        if txt != "":
            text_res.append(txt)
    return text_res


def submit_post(url: str, data: dict):
    return requests.post(url, data=json.dumps(data))


def save_encoded_image(b64_image: str, output_path: str):
    with open(output_path, 'wb') as image_file:
        image_file.write(base64.b64decode(b64_image))
        

def img_generator(text_list):
    txt2img_url = r'http://127.0.0.1:7864/sdapi/v1/txt2img'
    data = {'prompt': 'a dog wearing a hat',
            'negative_prompt': '',
            'sampler_index': 'DPM++ SDE',
            'seed': 1234,
            'steps': 20,
            'width': 512,
            'height': 512,
            'cfg_scale': 8}
    cnt = 0
    img_files = []
    for txt in tqdm(text_list):
        data['prompt'] = txt
        response = submit_post(txt2img_url, data)
        save_image_path = r'img/tmp_'+str(cnt)+'.png'
        save_encoded_image(response.json()['images'][0], save_image_path)
        img_files.append(save_image_path)
        cnt+=1
    
    return img_files
