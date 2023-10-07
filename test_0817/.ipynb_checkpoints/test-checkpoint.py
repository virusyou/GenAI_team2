import os
from moviepy.editor import *
import cv2

audio_folder = "audio"
image_folder = "img"

# 获取音频文件列表
audio_paths = [os.path.join(audio_folder, file) for file in os.listdir(audio_folder) if file.endswith(".mp3")]
audio_paths.reverse()

# 获取图片文件列表，保持与音频文件数量一致
image_paths = [os.path.join(image_folder, f"tmp_{i}.png") for i in range(len(audio_paths))]

print("audio_paths =", audio_paths)
print("image_paths =", image_paths)



# 三段音频的路径
# audio_paths = ["0_speech-cn.mp3", "1_speech-cn.mp3"]

# 三张图片的路径
# image_paths = ["tmp_0.png", "tmp_1.png"]

# 中文字幕列表
subtitles = ["hello world", "hello world2"]  # 根据实际情况修改

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

# 保存临时视频
temp_video_path = "temp_video.mp4"
final_video.write_videofile(temp_video_path, fps=fps)

# 使用OpenCV在视频中添加中文字幕
cap = cv2.VideoCapture(temp_video_path)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
output_video_path = "output_video_with_subtitles.mp4"
out = cv2.VideoWriter(output_video_path, fourcc, fps,
                      (int(cap.get(3)), int(cap.get(4))))

# 获取视频总帧数
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

index = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 添加中文字幕
    if index < len(subtitles):
        text = subtitles[index]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (255, 255, 255)  # 白色
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = frame.shape[0] - 30
        cv2.putText(frame, text, (text_x, text_y), font,
                    font_scale, font_color, thickness, cv2.LINE_AA)

    # 写入帧到输出视频
    out.write(frame)

    index += 1

    if index >= total_frames:
        break

# 释放资源
cap.release()
out.release()
cv2.destroyAllWindows()

# 使用MoviePy再次添加音频
video_with_subtitles = VideoFileClip(output_video_path)
final_video_with_audio = video_with_subtitles.set_audio(audios[0])
final_video_with_audio.write_videofile("final_output_video.mp4", fps=fps)
