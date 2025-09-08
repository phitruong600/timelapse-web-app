import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# Quan trọng: Import hàm main_process từ file của anh
from process_image import main_process 

# !!! THAY ĐỔI ĐƯỜNG DẪN NÀY CHO ĐÚNG VỚI MÁY CỦA ANH !!!
# Đây là thư mục mà các máy ảnh sẽ lưu ảnh vào.
# Ví dụ trên Windows: "E:\\Camera\\landing_zone"
# Hãy chắc chắn thư mục này tồn tại trước khi chạy.
WATCH_DIRECTORY = "test"

class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        """Hàm này sẽ được gọi khi có file mới được tạo."""
        if event.is_directory:
            return

        file_path = event.src_path
        # Kiểm tra đuôi file là ảnh để tránh xử lý các file tạm
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"\n--- Phát hiện ảnh mới: {file_path} ---")
            # Đợi một chút để đảm bảo file đã được ghi xong hoàn toàn
            time.sleep(2) 
            try:
                main_process(file_path)
            except Exception as e:
                print(f"!!! Gặp lỗi nghiêm trọng khi xử lý file {file_path}: {e} !!!")

if __name__ == "__main__":
    if not os.path.isdir(WATCH_DIRECTORY):
        print(f"Lỗi: Thư mục '{WATCH_DIRECTORY}' không tồn tại.")
        print("Vui lòng tạo thư mục hoặc kiểm tra lại đường dẫn trong biến WATCH_DIRECTORY.")
    else:
        event_handler = ImageHandler()
        observer = Observer()
        observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
        
        print("=====================================================")
        print(f"   Bắt đầu theo dõi thư mục: {WATCH_DIRECTORY}")
        print(f"   (Nhấn Ctrl+C để dừng chương trình)")
        print("=====================================================")
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\nĐã dừng theo dõi.")
        observer.join()
