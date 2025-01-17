# -*- coding: utf-8 -*-
# Author: Vi
# Created on: 2025-01-17 10:43:39
# Description: This script is used to convert multiple images to a gif file.
"""
! pip install pillow imageio
"""

from PIL import Image


def convert_to_gif(
    image_files: list[str], output_file_name: str, duration: int = 500, loop: int = 0
):
    """
    转换图片到 GIF 文件
    - param image_files: 图片文件列表, list[str]
    - param output_file_name: 输出 GIF 文件名, str
    - param duration: 每帧的显示时间（毫秒）, int, default=500
    - param loop: 循环次数（0 表示无限循环）, int, default=0
    - return: 输出 GIF 文件名, str
    """
    if not output_file_name.lower().endswith(".gif"):
        output_file_name += ".gif"

    # 打开所有图片并存入列表
    images = [Image.open(image) for image in image_files]

    # 保存为 GIF
    images[0].save(
        output_file_name,  # 输出文件名
        save_all=True,  # 保存所有图片
        append_images=images[1:],  # 添加剩余图片
        duration=duration,  # 每帧的显示时间（毫秒）
        loop=loop,  # 循环次数（0 表示无限循环）
    )
    print(f"Gif file saved to {output_file_name}")
    return output_file_name


if __name__ == "__main__":
    import os

    # test_base_dir = "image/多图转gif"
    # image_dirs = os.listdir(test_base_dir)
    # print(image_dirs)

    # for i, image_dir in enumerate(image_dirs):
    #     image_files = [
    #         os.path.join(test_base_dir, image_dir, file)
    #         for file in os.listdir(os.path.join(test_base_dir, image_dir))
    #     ]
    #     output_file_name = os.path.join(test_base_dir, f"{image_dir}.gif")
    #     output_file_name = convert_to_gif(image_files, output_file_name, duration=1000)
    #     print("转换完成:", i + 1, output_file_name)

    image_dir1 = r'image\多图转gif\origin'
    image_dir2 = r'image\多图转gif\new'
    
    image_files1 = [os.path.join(image_dir1, file) for file in os.listdir(image_dir1)]
    image_files2 = [os.path.join(image_dir2, file) for file in os.listdir(image_dir2)]
    
    image_files1 = sorted(image_files1, key=lambda x: int(x.split('\\')[-1].split('.')[0]))
    image_files2 = sorted(image_files2, key=lambda x: int(x.split('\\')[-1].split('.')[0]))
    
    duration = 500
    convert_to_gif(image_files1, 'origin', duration=duration)
    convert_to_gif(image_files2, 'new', duration=duration)