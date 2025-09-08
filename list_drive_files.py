import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- ANH CẦN THAY ĐỔI ID NÀY ---
# Dán ID của thư mục trên Google Drive mà anh muốn lấy danh sách ảnh vào đây.
# Ví dụ: "1nh31RKzoJB0PwYl41Q8rVkpH3ecO-84y"
TARGET_FOLDER_ID = "1nh31RKzoJB0PwYl41Q8rVkpH3ecO-84y" 

# Các file credentials, giữ nguyên như cũ
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] # Chỉ cần quyền đọc

def get_drive_service():
    """Xác thực và trả về một đối tượng service để tương tác với Drive."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Nếu token hết hạn và có refresh_token, ta làm mới nó
            # Nhưng vì ta đổi SCOPE, nên cần xác thực lại từ đầu
            creds = None 
            os.remove(TOKEN_FILE) # Xóa token cũ để xác thực lại
        
        # Nếu không có token hợp lệ, chạy lại quy trình xác thực
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def list_files(service, folder_id):
    """Lấy và in ra danh sách các file trong một thư mục cụ thể."""
    try:
        # Câu lệnh query để tìm tất cả file có cha là folder_id
        query = f"'{folder_id}' in parents"
        
        # Lấy danh sách file
        results = service.files().list(
            q=query,
            pageSize=100,  # Lấy tối đa 100 file mỗi lần gọi
            # Chỉ lấy các trường thông tin cần thiết: id và name
            fields="nextPageToken, files(id, name)" 
        ).execute()
        
        items = results.get('files', [])

        if not items:
            print('Không tìm thấy file nào trong thư mục.')
        else:
            print('Các file có trong thư mục:')
            for item in items:
                print(f"- Tên file: {item['name']} (ID: {item['id']})")
                
    except HttpError as error:
        print(f'Đã xảy ra lỗi: {error}')
    except Exception as e:
        print(f'Đã xảy ra lỗi không xác định: {e}')


if __name__ == '__main__':
    print("Đang kết nối tới Google Drive...")
    drive_service = get_drive_service()
    if drive_service:
        print(f"\nĐang lấy danh sách file từ thư mục ID: {TARGET_FOLDER_ID}")
        list_files(drive_service, TARGET_FOLDER_ID)
