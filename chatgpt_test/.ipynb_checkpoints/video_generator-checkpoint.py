# from generator import img_generator
# from generator import text_generator
# from moviepy.editor import *
# from logger import logger
import subprocess

# # from moviepy.editor import AudioFileClip, VideoFileClip,ImageClip, concatenate_videoclips
# # from moviepy.editor import TextClip,CompositeVideoClip,CompositeAudioClip
# # from moviepy.editor import afx

# def video_generator(query,out_file="test.mp4"):
#     text_list = text_generator(query)
#     img_list = img_generator(text_list)
    
#     # merge media 
#     final_clips = []
#     for idx,(txt,img_file) in enumerate(zip(text_list,img_list)):
#         print(img_file)
#         text_clip = TextClip(txt,fontsize=30,color='black')
#         text_clip = text_clip.set_duration(10)
        
#         vision_clip = ImageClip(img_file).set_duration(10)
#         vision_clip = CompositeVideoClip([vision_clip,text_clip.set_position(('center','bottom'))])
#         vision_clip.write_videofile("test_{}.mp4".format(idx), fps=24)
#         final_clips.append(vision_clip)
        
#     logger.info('final_clips: {}'.format(len(final_clips)))
#     video = concatenate_videoclips(final_clips)
#     video.write_videofile(out_file, fps=24)
        
# def Sad_Talker_gen():
    # use subprocess to call inference.py 
    subprocess.call(['python', 'inference.py',
          '--driven_audio', './audio1.mp3' ,
           '--source_image','mom.png',
           '--result_dir', './output'])
# query= "Please help me continue the story, the background is a little girl in the forest, separated by paragraphs"
    #
    Sad_Talker_gen()# from generator import img_generator
# from generator import text_generator
# from moviepy.editor import *
# from logger import logger
import subprocess

# # from moviepy.editor import AudioFileClip, VideoFileClip,ImageClip, concatenate_videoclips
# # from moviepy.editor import TextClip,CompositeVideoClip,CompositeAudioClip
# # from moviepy.editor import afx

# def video_generator(query,out_file="test.mp4"):
#     text_list = text_generator(query)
#     img_list = img_generator(text_list)
    
#     # merge media 
#     final_clips = []
#     for idx,(txt,img_file) in enumerate(zip(text_list,img_list)):
#         print(img_file)
#         text_clip = TextClip(txt,fontsize=30,color='black')
#         text_clip = text_clip.set_duration(10)
        
#         vision_clip = ImageClip(img_file).set_duration(10)
#         vision_clip = CompositeVideoClip([vision_clip,text_clip.set_position(('center','bottom'))])
#         vision_clip.write_videofile("test_{}.mp4".format(idx), fps=24)
#         final_clips.append(vision_clip)
        
#     logger.info('final_clips: {}'.format(len(final_clips)))
#     video = concatenate_videoclips(final_clips)
#     video.write_videofile(out_file, fps=24)
        
#     # return final_text, out_file

def Sad_Talker_gen():
    # use subprocess to call inference.py 
    subprocess.call(['python', 'inference.py',
          '--driven_audio', './audio1.mp3' ,
           '--source_image','mom.png',
           '--result_dir', './output'])

if __name__ == "__main__":
    # query= "Please help me continue the story, the background is a little girl in the forest, separated by paragraphs"
    # video_generator(query)
    Sad_Talker_gen()