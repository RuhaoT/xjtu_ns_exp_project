#!/usr/bin/env python3
import cgi
import os
import sys
import tempfile
import shutil
from datetime import datetime
import subprocess

# 启用调试
import cgitb
cgitb.enable()

def process_upload():
    
    # for debugging
    # return False, "Debugging enabled"
    
    # 创建表单对象处理POST数据
    form = cgi.FieldStorage()
    
    # 检查是否有文件上传
    if "file" not in form:
        return False, "No file uploaded"
    
    # 将文件保存到../test目录
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'test')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    # 获取上传的文件
    file_item = form["file"]
    if not file_item.file:
        return False, "No file uploaded"
    # 获取文件名
    filename = os.path.basename(file_item.filename)
    # 生成唯一的文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    # 保存文件到指定目录
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(file_item.file, f)
    # 返回文件名
    return True, unique_filename

# 生成HTTP响应
def main():
    print("Content-Type: application/json")
    print()  # 空行分隔头部和主体
    
    success, result = process_upload()
    
    if success:
        print('{"status": "success", "filename": "' + result + '"}')
    else:
        print('{"status": "error", "message": "' + result + '"}')

if __name__ == "__main__":
    main()