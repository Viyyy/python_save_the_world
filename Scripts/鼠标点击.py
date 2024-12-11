# -*- coding: utf-8 -*-
# Author: Vi
# Created on: 2024-12-11 09:55:28
# Description: 一个可移动的按钮，点击按钮可以点击其他位置

'''
pip install pyautogui
'''

import pyautogui as pg
import tkinter as tk

CLICK_POSITION = (727, 987) # 点击位置

class DraggableFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.start_x = None
        self.start_y = None

        # 添加按钮
        self.submit_btn = tk.Button(self, text='提交', command=self.click_submit)
        self.submit_btn.pack()

        # 按住按钮可以拖动窗口
        self.submit_btn.bind('<ButtonPress-1>', self.start_move)
        self.submit_btn.bind('<B1-Motion>', self.move_window)
        self.submit_btn.bind('<ButtonRelease-1>', self.stop_move)

        self.pack()

    def start_move(self, event):
        # 记录按下时鼠标位置
        self.start_x = event.x
        self.start_y = event.y

    def move_window(self, event):
        # 计算新的位置
        x = self.master.winfo_x() + event.x - self.start_x
        y = self.master.winfo_y() + event.y - self.start_y
        self.master.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        # 处理鼠标释放事件（如果需要）
        pass

    def click_submit(self):
        print("提交按钮被点击")
        # 在这里你可以添加点击提交按钮后的逻辑
        pg.moveTo(CLICK_POSITION)
        pg.click()

# 创建主窗口
root = tk.Tk()
root.resizable(False, False)
root.attributes('-topmost', True)
root.overrideredirect(True)
root.geometry('40x30+470+400')

# 创建可拖动的框架
draggable_frame = DraggableFrame(root)

root.mainloop()

