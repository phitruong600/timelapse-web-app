# authenticate.py
from google_auth_oauthlib.flow import InstalledAppFlow

# Yêu cầu quyền chỉnh sửa, tạo, xóa file trên Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    """Chạy quy trình xác thực và lưu token."""
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    # Lưu credentials cho những lần chạy sau
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("Đã tạo file token.json thành công!")

if __name__ == '__main__':
    main()