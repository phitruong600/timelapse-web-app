from flask import Flask, render_template, jsonify
import os
import pytz
from datetime import datetime
from collections import defaultdict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Cấu hình ---
TARGET_FOLDER_ID = "1nh31RKzoJB0PwYl41Q8rVkpH3ecO-84y"
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] # Chỉ cần quyền đọc

# --- Khởi tạo ứng dụng Flask ---
app = Flask(__name__)

# --- Tải sử dụng các hàm làm việc với Google Drive ---
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

@app.route('/')
def index():
    """Trang chủ, hiển thị danh sách file từ Google Drive."""
    try:
        service = get_drive_service()
        # --- SỬA LỖI: Bỏ yêu cầu 'embedLink' không hợp lệ ---
        fields_to_get = "nextPageToken, files(id, name, createdTime, mimeType, webViewLink, thumbnailLink, iconLink)"
        
        results = service.files().list(
            q=f"'{TARGET_FOLDER_ID}' in parents",
            pageSize=1000,
            fields=fields_to_get
        ).execute()
        
        all_files = results.get('files', [])
        
        all_files.sort(key=lambda x: x['createdTime'], reverse=True)

        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        grouped_files = defaultdict(lambda: {'videos': [], 'images': []})
        videos = []

        for item in all_files:
            utc_dt = datetime.fromisoformat(item['createdTime'].replace('Z', '+00:00'))
            vn_dt = utc_dt.astimezone(vn_tz)
            date_key = vn_dt.strftime('%Y-%m-%d')
            item['createdTime_vn'] = vn_dt

            if 'video' in item['mimeType']:
                # --- SỬA LỖI: Tự tạo embedLink từ ID của file ---
                item['embedLink'] = f"https://drive.google.com/file/d/{item['id']}/preview"
                grouped_files[date_key]['videos'].append(item)
                videos.append(item)
            else:
                grouped_files[date_key]['images'].append(item)

        featured_video = max(videos, key=lambda x: x['createdTime'], default=None)

        return render_template('index.html', grouped_files=grouped_files.items(), featured_video=featured_video)

    except HttpError as error:
        print(f"An error occurred: {error}")
        return f"Đã xảy ra lỗi khi kết nối với Google Drive: {error}", 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"Đã xảy ra lỗi không xác định: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)

