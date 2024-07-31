import tempfile
import zipfile
import os
import shutil
from contextlib import contextmanager

@contextmanager
def unzip_to_temp(zip_file_path):
    """
    解压缩 ZIP 文件到临时目录，并在使用后删除临时目录。

    :param zip_file_path: ZIP 文件路径
    """
    temp_dir = tempfile.mkdtemp()  # 创建一个临时目录
    
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)  # 解压到临时目录
        
        yield temp_dir  # 返回临时目录路径
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)  # 删除临时目录及其内容

# 使用上下文管理器
if __name__ == "__main__":
    zip_file_path = 'example.zip'  # 替换为你的 ZIP 文件路径
    
    with unzip_to_temp(zip_file_path) as temp_dir:
        print(f"ZIP 文件已解压到临时目录: {temp_dir}")
        
        # 示例：列出临时目录中的文件
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                print(os.path.join(root, file))
    
    # 临时目录和其中的文件将在 with 语句块结束时自动删除