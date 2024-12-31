"""
使用ocr提取雨课堂的题目和答案，汇总成一个文档

使用paddleocr识别题目和答案

> https://paddlepaddle.github.io/PaddleOCR/latest/quick_start.html
> !pip install paddlepaddle
> !pip install paddleocr

使用pyautogui模拟跳转到下一题或下一作业
> !pip install pyautogui
"""

import os
import datetime
import tempfile
from functools import partial

from clipboard import copy
from PIL import Image
import pyautogui as pg
from paddleocr import PaddleOCR

OCR = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False)

PG_SLEEP_TIME = 0.5  # pyautogui的睡眠时间
START_INDEX = 27643621  # 开始的作业序号
END_INDEX = 27643801  # 结束的作业序号

URL_TEMP = "https://changjiang.yuketang.cn/v2/web/cloud/student/exercise/18949303/{start}/9158353?hide_return=1"

# region 全局变量: 坐标位置
HOMEWORK_REGION = (150, 120, 700 - 150, 150 - 120)  # 作业名字截图区域
QUESTION_TYPE_REGION = (440, 215, 590 - 440, 260 - 215)  # 题目类型截图区域
QUESTION_REGION = (381, 260, 1050 - 381, 950 - 260)  # 题目截图区域
NEXT_BUTTON = (1010, 980)  # 下一题按钮位置
BROWER_POS = (450, 20)  # 浏览器位置
URL_POS = (240, 60)  # 题目链接位置
# endregion

# region Common Functions
def screenshot(region: tuple) -> Image:
    """
    截图并保存
    """
    img = pg.screenshot(region=region)
    return img


def move_and_click(pos: tuple):
    """
    移动鼠标并点击
    """
    pg.moveTo(pos)
    pg.click()


def sleep(seconds: float = PG_SLEEP_TIME):
    pg.sleep(seconds)
# endregion



def next_question():
    """
    点击“下一题”按钮
    """
    move_and_click(NEXT_BUTTON)

def next_homework(url: str):
    """
    跳转到下一个作业
    """
    move_and_click(BROWER_POS)
    move_and_click(URL_POS)
    copy(url)
    pg.hotkey("ctrl", "a")
    pg.hotkey("ctrl", "v")
    sleep()
    pg.press("enter")
    sleep(1)

def get_homework(save_dir: str):
    '''
    获取作业的名字，如果没有则返回None
    '''
    
    save_path = os.path.join(save_dir, f"homework_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png")
    img = screenshot(HOMEWORK_REGION)
    img.save(save_path)
    try:
        result = OCR.ocr(save_path, cls=True)
        return result[0][0][1][0]
    except Exception as e:
        print(e)
        return None

def get_question_type(save_dir: str):
    '''
    获取题目类型
    '''
    save_path = os.path.join(save_dir, f"question_type_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png")
    img = screenshot(QUESTION_TYPE_REGION)
    img.save(save_path)
    try:
        result = OCR.ocr(save_path, cls=True)
        qt = result[0][0][1][0]
        # qt = qt.split('.')[-1]
        return qt
    except Exception as e:
        print(e)
        return None
    
def get_question(save_dir: str):
    '''
    获取题目
    '''
    save_path = os.path.join(save_dir, f"question_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png")
    img = screenshot(QUESTION_REGION)
    img.save(save_path)
    try:
        result = OCR.ocr(save_path, cls=True)
        contents = [r[1][0] for r in result[0]]
        return contents
    except Exception as e:
        print(e)
    
def is_homework(homework_name):
    """
    判断是否已经完成当前的作业
    """
    finished = homework_name is None or '作业' not in homework_name or '视频' in homework_name
    return finished
    
    
def homework_url_generator():
    '''
    生成作业链接
    '''
    for i in range(START_INDEX, END_INDEX+1):
        url = URL_TEMP.format(start=i)
        yield url
        
def write_to_file(content:str, save_path:str):
    with open(save_path, 'a', encoding='utf-8') as f:
        f.write(content + '\n')
    
def main():
    temp_dir = tempfile.TemporaryDirectory()
    save_path = os.path.join(os.getcwd(), f'雨课堂题目_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.md')
    write = partial(write_to_file, save_path=save_path)
    last_question = None
    current_question = None
    try:
        for url in homework_url_generator():
            next_homework(url)
            homework_name = get_homework(save_dir=temp_dir.name)
            if is_homework(homework_name):
                continue
            write(f'# {homework_name}')
            current_question = screenshot(QUESTION_REGION)
            while current_question != last_question:
                qt = get_question_type(save_dir=temp_dir.name)
                q = get_question(save_dir=temp_dir.name)
                if qt is None or q is None:
                    continue
                write(f'## {qt}')
                write("\n".join(q))
                last_question = current_question
                next_question()
                sleep(1)
                current_question = screenshot(QUESTION_REGION)
            
    finally:
        temp_dir.cleanup()
    
        
        
    print('ok')
if __name__ == '__main__':
    main()