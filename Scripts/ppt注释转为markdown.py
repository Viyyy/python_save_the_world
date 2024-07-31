# -*- coding: utf-8 -*-
# Author: Vi
# Created on: 2024-07-31 14:31:23
# Description: 提起ppt文件中的注释并存为markdown文件

import os
import re
import xml.etree.ElementTree as ET
from .zip_helper import unzip_to_temp

def filter_notes(notes_dir)->list[tuple[int, str]]:
    '''
    过滤notes目录下xml文件
    :param notes_dir: notes目录路径
    :return: 包含文件名和序号的元组列表
    '''
    files = [f for f in os.listdir(notes_dir) if f.endswith('.xml')]
    
    results = []
    
    for file in files:
        number = int(re.findall(r'\d+', file)[-1])
        results.append((number, file))
    
    results = sorted(results, key=lambda x: x[0])
    return results

def extract_text(element):
    '''
    提取xml元素中的文本
    :param element: xml元素
    :return: 元素中的文本列表
    '''
    texts = []
    if element.text:
        texts.append(element.text)
    for child in element:
        texts.extend(extract_text(child))
    if element.tail:
        texts.append(element.tail)
        
    texts = [a for a in texts if len(a.strip()) > 0]
    return texts

def extract_ppt_notes(ppt_file_path)->str:
    '''
    提取ppt文件中的注释
    :param ppt_file_path: ppt文件路径
    :return: 注释列表
    '''
    results = []
    with unzip_to_temp(ppt_file_path) as temp_dir:
        notes_dir = os.path.join(temp_dir, 'ppt', 'notesSlides')
        if not os.path.exists(notes_dir):
            return results
        else:
            note_files = filter_notes(notes_dir)
            for number, file in note_files:
                ppt_file_path = os.path.join(notes_dir, file)
                tree = ET.parse(ppt_file_path)
                root = tree.getroot()
                texts = extract_text(root)
                text = ''.join(texts)
                if len(text) > 0:
                    results.append((number, text))
    return results

def ppt_notes2md(file_path:str, save_dir:str)->str:
    '''
    ppt文件中的注释转为markdown文件
    :param file_path: ppt文件路径
    :param save_dir: 保存markdown文件的目录
    :return: 保存markdown文件的路径
    '''
    file_name = os.path.basename(file_path)
    save_path = os.path.join(save_dir, f'{file_name}.md')
    
    notes = extract_ppt_notes(file_path)
    assert len(notes) > 0, f'在{file_path}中没有找到任何注释'
    with open(save_path, 'w', encoding='utf-8') as f:
        for number, text in notes:
            f.write(f'## Slide {number}\n\n{text}\n\n')
            
    return save_path