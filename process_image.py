import os
import subprocess
import tempfile  # <-- Thêm thư viện này
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ID của thư mục trên Google Drive mà anh muốn tải ảnh vào.
TARGET_FOLDER_ID = "1nh31RKzoJB0PwYl41Q8rVkpH3ecO-84y" 

# File credentials đã có từ các bước trước
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Xác thực và trả về một đối tượng service để tương tác với Drive."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def convert_to_heic(source_path, output_path):
    """Sử dụng ImageMagick để chuyển đổi ảnh sang HEIC."""
    try:
        print(f"Đang chuyển đổi {source_path} sang HEIC...")
        # Lệnh convert của ImageMagick
        # -quality 75 là mức chất lượng tốt, dung lượng thấp
        command = ['magick', source_path, '-quality', '75', output_path]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Chuyển đổi thành công: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi chuyển đổi ảnh: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy lệnh 'magick'. Hãy chắc chắn ImageMagick đã được cài đặt và thêm vào PATH.")
        return False


def upload_file(service, file_path, folder_id):
    """Tải một file lên thư mục chỉ định trên Google Drive."""
    file_name = os.path.basename(file_path)
    print(f"Đang tải lên {file_name}...")
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='image/heic')
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"Tải lên thành công! File ID: {file.get('id')}")
        return file.get('id')
    except Exception as e:
        print(f"Lỗi khi tải file lên: {e}")
        return None

def main_process(image_path):
    """Quy trình chính: chuyển đổi, tải lên và xóa file tạm."""
    if not os.path.exists(image_path):
        print(f"Ảnh không tồn tại: {image_path}")
        return

    file_name_without_ext = os.path.splitext(os.path.basename(image_path))[0]
    
    # --- SỬA LỖI Ở ĐÂY ---
    # Tự động lấy thư mục tạm của hệ điều hành (chạy được cả trên Windows, Mac, Linux)
    temp_dir = tempfile.gettempdir()
    output_heic_path = os.path.join(temp_dir, f"{file_name_without_ext}.heic")

    # 1. Chuyển đổi ảnh
    if not convert_to_heic(image_path, output_heic_path):
        return # Dừng nếu chuyển đổi lỗi
        
    # 2. Tải lên Google Drive
    service = get_drive_service()
    if service:
        upload_file(service, output_heic_path, TARGET_FOLDER_ID)
    
    # 3. Xóa file HEIC tạm sau khi tải lên
    if os.path.exists(output_heic_path):
        os.remove(output_heic_path)
        print(f"Đã xóa file tạm: {output_heic_path}")

    print(f"Đã xử lý xong: {image_path}")

# --- CÁCH CHẠY THỬ NGHIỆM ---
# 1. Bỏ dấu # ở 3 dòng dưới
# 2. Thay đổi đường dẫn đến file ảnh của anh
if __name__ == '__main__':
    # Ví dụ trên Windows, nhớ dùng 2 dấu \\
    test_image = "E:\\Ảnh\\Screenshots\\Screenshot 2025-09-08 143415.png"
    main_process(test_image)
