#!/usr/bin/env python3
"""
Script để sửa các file model bị lặp code
"""
import os
import re

def fix_duplicate_content(file_path):
    """Sửa nội dung bị lặp trong file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tìm pattern lặp: }""" followed by same content
    pattern = r'(\s*}\s*"""[^"]*"""\s*from app import db.*?)(?="""[^"]*"""\s*from app import db)'
    
    # Nếu tìm thấy pattern lặp, chỉ giữ lại phần đầu
    if '"""' in content and content.count('from app import db') > 1:
        # Tìm vị trí của }""" đầu tiên
        first_end = content.find('}"""')
        if first_end != -1:
            # Tìm vị trí bắt đầu của phần lặp
            second_start = content.find('"""', first_end + 4)
            if second_start != -1:
                # Cắt bỏ phần lặp
                content = content[:first_end + 1]
    
    # Ghi lại file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {os.path.basename(file_path)}")

def main():
    """Main function"""
    models_dir = "/app/models"
    
    # Lấy tất cả file .py trừ __init__.py
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_dir, filename)
            fix_duplicate_content(file_path)

if __name__ == "__main__":
    main()
