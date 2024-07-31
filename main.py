from Scripts.ppt注释转为markdown import ppt_notes2md
import os

if __name__ == '__main__':
    file_path = r"你的ppt文件.pptx"
    save_dir = '你的markdown文件保存目录'
    save_path = ppt_notes2md(file_path, save_dir) # 转换后的markdown文件路径
    os.startfile(save_path) # 打开转换后的markdown文件