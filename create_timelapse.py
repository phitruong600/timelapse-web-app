import os
import sys
import tempfile
import subprocess
import shutil
import glob  # <-- Thêm thư viện này
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.credentials import Credentials

# --- Cấu hình ---
TARGET_FOLDER_ID = "1nh31RKzoJB0PwYl41Q8rVkpH3ecO-84y" # ID thư mục chính
TOKEN_FILE = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        return None
    return build('drive', 'v3', credentials=creds)

def create_timelapse_for_date(service, date_str):
    print(f"Bắt đầu quá trình tạo timelapse cho ngày: {date_str}")
    
    query = f"'{TARGET_FOLDER_ID}' in parents and (mimeType contains 'image/') and name contains '{date_str}'"
    results = service.files().list(
        q=query, pageSize=1000, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print(f"Không tìm thấy ảnh nào cho ngày {date_str}.")
        return

    print(f"Tìm thấy {len(items)} ảnh. Bắt đầu tải về...")
    
    temp_dir = tempfile.mkdtemp(prefix=f"timelapse_{date_str}_")
    print(f"Đã tạo thư mục tạm tại: {temp_dir}")
    
    try:
        downloaded_count = 0
        for item in items:
            file_path = os.path.join(temp_dir, item['name'])
            request = service.files().get_media(fileId=item['id'])
            with open(file_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            downloaded_count += 1
            print(f"  Đã tải về {downloaded_count}/{len(items)} ảnh.", end='\r')
        
        print("\nĐã tải xong toàn bộ ảnh. Tạo danh sách file cho FFmpeg...")

        # --- NÂNG CẤP: Tạo file danh sách cho FFmpeg ---
        # Tìm tất cả các file ảnh (jpg, png, heic) trong thư mục tạm
        image_files = glob.glob(os.path.join(temp_dir, '*.heic')) \
                    + glob.glob(os.path.join(temp_dir, '*.jpg')) \
                    + glob.glob(os.path.join(temp_dir, '*.png'))

        if not image_files:
            print("!!! Lỗi: Không tìm thấy file ảnh nào trong thư mục tạm để tạo video.")
            return
            
        # Sắp xếp file theo tên để đảm bảo đúng thứ tự thời gian
        image_files.sort()

        file_list_path = os.path.join(temp_dir, 'file_list.txt')
        with open(file_list_path, 'w', encoding='utf-8') as f:
            for file_path in image_files:
                # Cú pháp mà FFmpeg yêu cầu: file 'tên_file.ext'
                f.write(f"file '{os.path.basename(file_path)}'\n")
        
        print("Bắt đầu ghép video...")
        video_name = f"timelapse_{date_str}.mp4"
        video_output_path = os.path.join(temp_dir, video_name)
        
        try:
            # --- THAY ĐỔI CÂU LỆNH FFmpeg ---
            command = [
                'ffmpeg',
                '-r', '30',               # Tốc độ khung hình (rate)
                '-f', 'concat',           # Sử dụng bộ ghép file (concat demuxer)
                '-safe', '0',             # Cho phép sử dụng tên file an toàn
                '-i', file_list_path,     # <-- File đầu vào là file danh sách
                '-vf', 'scale=1920:-2',   # Giảm độ phân giải xuống Full HD
                '-preset', 'fast',        # Tăng tốc độ xử lý
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                video_output_path
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            print("Ghép video thành công!")
        except subprocess.CalledProcessError as e:
            print("!!! Lỗi khi ghép video bằng FFmpeg:")
            print(e.stderr)
            return
        
        print(f"Đang tải video {video_name} lên Google Drive...")
        # ... (Phần code tải video lên giữ nguyên) ...
        file_metadata = {'name': video_name, 'parents': [TARGET_FOLDER_ID]}
        media = MediaFileUpload(video_output_path, mimetype='video/mp4', resumable=True)
        request = service.files().create(body=file_metadata, media_body=media, fields='id')
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"  Đã tải lên {int(status.progress() * 100)}%")
        print(f"Tải video lên thành công! File ID: {response.get('id')}")

    finally:
        try:
            shutil.rmtree(temp_dir)
            print(f"Đã dọn dẹp thành công thư mục tạm.")
        except PermissionError:
            print(f"!!! Cảnh báo: Không thể xóa thư mục tạm {temp_dir} do đang bị khóa.")
        except Exception as e:
            print(f"!!! Lỗi không xác định khi dọn dẹp thư mục tạm: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Lỗi: Vui lòng cung cấp ngày theo định dạng YYYY-MM-DD.")
        sys.exit(1)
    
    target_date = sys.argv[1]
    drive_service = get_drive_service()
    if drive_service:
        create_timelapse_for_date(drive_service, target_date)

