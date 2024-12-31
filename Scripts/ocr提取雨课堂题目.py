"""
使用ocr提取雨课堂的题目和答案，汇总成一个文档

使用paddleocr识别题目和答案

> https://paddlepaddle.github.io/PaddleOCR/latest/quick_start.html
> !pip install paddlepaddle
> !pip install paddleocr

使用pyautogui模拟跳转到下一题或下一作业
> !pip install pyautogui

使用ai补充题目的选项和去掉多余的符号，非必须
> pip install langchain langchain-chroma langchain-community langchain-core langchain-openai langchain-text-splitters langchainhub python-dotenv
"""

import os
import datetime
import tempfile
from functools import partial

from clipboard import copy
from PIL import Image
import pyautogui as pg
from paddleocr import PaddleOCR

OCR = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False, show_log=False)

USE_AI = True  # 是否使用AI自动补充题目选项
PG_SLEEP_TIME = 0.5  # pyautogui的睡眠时间
START_INDEX = 27643621  # 开始的作业序号
START_INDEX = 27643660  # 开始的作业序号
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

# region AI
from dotenv import load_dotenv

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=500,
    temperature=0.1
)

# system是机器人，human是人类用户
prompt_template = ChatPromptTemplate.from_messages(
    [
        ('system', '现在你是一个项目管理概论老师的助理，你需要帮我整理考试的题目。对于单选题或多选题，你需要补充选项编号（如A、B、C、D），并去掉多余的换行符或多余符号。对于判断题，同样需要去掉多余的换行符。如果是包含一些缩写，在后面添加上注释。以下是一些例子：'
            '\n\n## 1.单选题\n'
            '从人类社会整体上来看，下列关于项目与日常运营关系的描述错误的是\n'
            '项目往往是先于日常运营存在的\n'
            '日常运营不是以项目为基础的\n'
            '项目投入需要通过日常运营来回收\n'
            '广义的项目包含了狭义的项目和日常运营\n'
            '正确答案：B\n'
            '修改为：\n'
            '## 1.单选题\n'
            '从人类社会整体上来看，下列关于项目与日常运营关系的描述错误的是\n'
            'A. 项目往往是先于日常运营存在的\n'
            'B. 日常运营不是以项目为基础的\n'
            'C. 项目投入需要通过日常运营来回收\n'
            'D. 广义的项目包含了狭义的项目和日常运营\n'
            '正确答案：B\n\n'
            '*********************************\n\n'
            '## 10.判断题\n'
            '项目管理的重要工作是从两个方面管理和约束各项目相关利益主体的需求和期望，其一是不要使人们的要求与期望过高而不切实际，其二是努力满足和超越人们的要求与期望。\n'
            'X\n'
            '正确答案：正确\n'
            '修改为：\n'
            '## 10.判断题\n'
            '项目管理的重要工作是从两个方面管理和约束各项目相关利益主体的需求和期望，其一是不要使人们的要求与期望过高而不切实际，其二是努力满足和超越人们的要求与期望。\n'
            '正确答案：正确'
            '*********************************\n\n'
            '## 5.单选题\n'
            ' （）是用于给出项目工作范围的图形文件，包括项目工作包、项目工作包之间的关系以及项目工作包与项目产出物或项目交付物之间的关系。\n'
            'A. OBS\n'
            'B. WBS\n'
            'C. RBS\n'
            'D. BOM\n'
            '正确答案：B\n'
            '修改为：\n'
            '## 1.单选题\n'
            '（）是用于给出项目工作范围的图形文件，包括项目工作包、项目工作包之间的关系以及项目工作包与项目产出物或项目交付物之间的关系。\n'
            'A. OBS(Organization Breakdown Structure, 组织结构图)\n'
            'B. WBS(Work Breakdown Structure, 工作分解结构)\n'
            'C. RBS(Resource Breakdown Structure, 资源分解结构)\n'
            'D. BOM(Bill of Materials, 物料清单)\n'
            '正确答案：B\n'
        ),
        ('human', "题目的类型是{type}，题目的内容为:{question}")
    ]
)


chain = prompt_template | model
def polish_by_ai(question:str, type:str):
    answer = chain.invoke(input = {'type': type, 'question': question})
    return answer.content
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
    
def write_to_file(content:str, save_path:str):
    with open(save_path, 'a', encoding='utf-8') as f:
        f.write(content + '\n')
# endregion


# region Main Functions
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
        
# endregion

    
def main():
    temp_dir = tempfile.TemporaryDirectory()
    save_path = f'雨课堂题目_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.md'
    save_path = '雨课堂题目_20241231143510.md'
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
                
                q = "\n".join(q)
                # 使用ai补充题目选项和去掉多余的符号
                if USE_AI:
                    q = polish_by_ai(q, qt)
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), qt, q)
                    write(f'{q}')
                else:
                    write(f'## {qt}')
                    write(q)
                last_question = current_question
                next_question()
                sleep(1)
                current_question = screenshot(QUESTION_REGION)
            
    finally:
        temp_dir.cleanup()
    
        
        
    print('ok')
if __name__ == '__main__':
    main()