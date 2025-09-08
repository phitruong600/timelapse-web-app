import schedule
import time
import subprocess
import sys
from datetime import datetime
import os # <-- Thêm thư viện os

def run_create_timelapse(date_str):
    """Hàm để gọi script create_timelapse.py với ngày chỉ định."""
    print(f"--- Bắt đầu tác vụ tự động tạo video cho ngày {date_str} ---")
    try:
        # Lấy đường dẫn tới trình thông dịch Python đang chạy script này
        python_executable = sys.executable
        
        # --- SỬA LỖI TRIỆT ĐỂ: Thiết lập môi trường UTF-8 cho script con ---
        # Lấy một bản sao của môi trường hệ thống hiện tại
        my_env = os.environ.copy()
        # Ra lệnh cho Python trong script con phải sử dụng UTF-8 cho việc in ra màn hình
        my_env["PYTHONIOENCODING"] = "utf-8"

        # Chạy script con với môi trường đã được thiết lập
        result = subprocess.run(
            [python_executable, 'create_timelapse.py', date_str], 
            check=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='ignore',
            env=my_env # <-- Sử dụng môi trường mới
        )
        
        # In output của script con ra để tiện theo dõi
        print("--- Log từ create_timelapse.py ---")
        print(result.stdout)
        print("---------------------------------")
        
        print(f"--- Tác vụ tự động cho ngày {date_str} đã hoàn thành. ---")
    except subprocess.CalledProcessError as e:
        print(f"!!! Lỗi khi chạy script create_timelapse.py cho ngày {date_str}:")
        # In ra output lỗi đã được decode an toàn
        print(e.stderr)
    except Exception as e:
        print(f"!!! Gặp lỗi không xác định: {e} !!!")

def job_create_daily_timelapse():
    """Công việc được lên lịch để chạy mỗi ngày."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"\n>>> Đã đến giờ chạy tác vụ hàng ngày. Sẽ tạo video cho ngày {today_str}.")
    run_create_timelapse(today_str)

# --- THIẾT LẬP LỊCH TRÌNH TẠI ĐÂY ---
schedule.every().day.at("23:30").do(job_create_daily_timelapse)

# Anh cũng có thể lập lịch chạy mỗi giờ (bỏ dấu # ở dòng dưới nếu muốn)
# schedule.every().hour.do(job_create_daily_timelapse)


print("=====================================================")
print("  Bắt đầu chạy trình lập lịch tự động tạo video.")
print("  Chương trình sẽ kiểm tra lịch mỗi phút.")
print("  (Nhấn Ctrl+C để dừng)")
print("=====================================================")

# Chạy công việc đầu tiên ngay lập tức nếu cần (bỏ dấu #)
job_create_daily_timelapse()

# Vòng lặp chính để chương trình chạy mãi mãi
while True:
    schedule.run_pending()
    time.sleep(1)

