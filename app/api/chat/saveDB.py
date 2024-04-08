import os
import base64


def save_image_to_db(image_data_base64, folderPath, filename):
    # tao folder neu chua co
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # Giải mã dữ liệu ảnh từ base64
    image_data = base64.b64decode(image_data_base64)

    # Tạo đường dẫn đến file ảnh
    image_path = os.path.join(folderPath, filename + ".png")

    # Lưu dữ liệu ảnh vào file
    with open(image_path, "wb") as f:
        f.write(image_data)
    print("Image saved to", image_path)


def save_video_to_db(video_data, folderPath, filename):
    # Tạo folder nếu chưa có
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # Tạo đường dẫn đến file video
    video_path = os.path.join(folderPath, filename + ".mp4")

    # Lưu dữ liệu video vào file
    with open(video_path, "wb") as f:
        f.write(video_data)

    print("Video saved to", video_path)


def save_audio_to_db(audio_data, folderPath, filename):
    # tao folder neu chua co
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # Tạo đường dẫn đến file
    audio_path = os.path.join(folderPath, filename + ".mp3")

    # Lưu dữ liệu vào file
    with open(audio_path, "wb") as f:
        f.write(audio_data)

    print("Audio saved to", audio_path)
