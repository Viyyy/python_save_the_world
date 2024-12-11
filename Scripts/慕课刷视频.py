# -*- coding: utf-8 -*-
# Author: Vi
# Created on: 2024-12-11 10:13:05
# Description:


"""
pip install pyautogui Pillow
pip install opencv-python
pip install numpy==1.26
"""

import time
import cv2
import PIL
import numpy as np
import pyautogui as pg
import clipboard

IS_PLAYING: bool = False # 是否正在播放视频
LAST_SCREENSHOT: PIL.Image.Image = None # 上一屏幕截图

VIDEO_REGION: tuple = (360, 160, 1100-360, 650-160) # 定义播放区域的左上角坐标和宽度高度
PLAY_BUTTON = (410, 613) # 定义播放按钮的坐标
EDGE_POSITION = (500, 20) # 定义浏览器边缘的坐标
ENTER_URL_POSITION = (363, 61) # 定义输入URL的坐标

def screenshot() -> PIL.Image.Image:
    """
    获取播放区域的屏幕截图
    - param: region: 定义截图区域左上角的坐标 (x, y) 和宽度高度 (width, height)
    """
    try:
        screenshot: PIL.Image.Image = pg.screenshot(region=VIDEO_REGION)
        return screenshot
    except Exception as e:
        print(f"截图失败: {e}")
        return None


def compare_images(img1:PIL.Image.Image, img2:PIL.Image.Image):
    """
    比较当前屏幕截图与上一屏幕截图的差异
    - return: 差异值，范围 0~1，值越小表示两张图片越相似
    """
    if img1 is None or img2 is None:
        return 1.0
    
    img1:np.ndarray = np.array(img1)
    img2:np.ndarray = np.array(img2)

    # 确保两张图片具有相同的尺寸
    if img1.shape != img2.shape:
        return 1.0
    

    # 计算绝对差异
    difference = cv2.absdiff(img1, img2)

    # 将差异转为灰度图
    gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    # 阈值化
    _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

    # 计算非零像素数
    non_zero_count = cv2.countNonZero(thresh)

    return non_zero_count / (img1.shape[0] * img1.shape[1])


def play_video():
    """
    开始播放视频
    """
    global IS_PLAYING, LAST_SCREENSHOT

    pg.moveTo(PLAY_BUTTON)
    pg.click()
    
    IS_PLAYING = True
    LAST_SCREENSHOT = screenshot()


def double_speed():
    '''
    开启2倍速
    '''
    pg.moveTo(960, 616, duration=0.5)
    pg.sleep(0.5)
    pg.moveTo(960, 445, duration=0.8)
    pg.sleep(0.5)
    pg.click()


def open_next_video(video_url:str):
    """
    跳到下一个视频
    : param video_url: 下一个视频的 URL
    """
    global IS_PLAYING, LAST_SCREENSHOT
    
    pg.moveTo(EDGE_POSITION, duration=0.5)
    pg.click() # 点击浏览器
    
    pg.moveTo(ENTER_URL_POSITION, duration=0.5)
    pg.click() # 点击地址栏

    pg.hotkey("ctrl", "a") # 全选地址栏
    pg.press("delete") # 删除地址栏内容
    
    # 复制url到剪贴板
    clipboard.copy(video_url)
    pg.hotkey("ctrl", "v") # 粘贴地址栏内容
    pg.sleep(1)
    pg.press("enter") # 回车跳转到下一个视频

    time.sleep(2) # 等待视频加载完毕
    IS_PLAYING = False
    LAST_SCREENSHOT = screenshot()


def main():
    global IS_PLAYING, LAST_SCREENSHOT
    start = 27643704
    end = 27643801
    url_template = r'https://changjiang.yuketang.cn/v2/web/xcloud/video-student/18949303/{video_id}?hide_return=1'
    for video_id in range(start, end + 1):
        start_time = time.time()
        url = url_template.format(video_id=video_id)
        open_next_video(url)
        play_video()
        double_speed()
        print(f"开始播放视频: {video_id=}")
        while IS_PLAYING:
            current_screenshot = screenshot()
            diff = compare_images(current_screenshot, LAST_SCREENSHOT) # 图片差异值
            if diff < 0.001: # 图片相似度小于阈值，认为视频已经播放完毕
                IS_PLAYING = False
                print(f"视频播放完毕: {video_id=}, {diff=:.2f}, 耗时:{time.time() - start_time:.2f} 秒")

            LAST_SCREENSHOT = current_screenshot
            time.sleep(1) # 等待1秒钟
        
    print("ok")


if __name__ == "__main__":
    main()
