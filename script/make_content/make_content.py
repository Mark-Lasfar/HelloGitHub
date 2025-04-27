#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author  : XueWeiHan
E-mail  : 595666367@qq.com
Date    : 2016-10-21
Updated : 2025-04-27
Desc    : HelloGitHub项目——生成月刊脚本

该脚本用于根据模板和内容文件自动生成《HelloGitHub》月刊，
统一格式，便于后期维护和批量操作。
"""

import sys
import os

# 占位符，用于替换模板中的内容
CONTENT_FLAG = '{{ hello_github_content }}'
NUM_FLAG = '{{ hello_github_num }}'


class InputError(Exception):
    """自定义异常：输入参数错误"""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return repr(self.message)


def check_path(path):
    """检查文件或目录是否存在"""
    if not os.path.exists(path):
        print(f'错误：路径不存在 -> {path}')
        return False
    return True


def read_file(file_path):
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path, data):
    """将内容写入文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(data)


def make_content(num):
    """
    根据指定期号，生成对应的月刊文件
    :param num: 期号，例如 '01', '02', '10' 等
    """
    cur_dir = os.path.abspath(os.curdir)
    template_path = os.path.join(cur_dir, 'template.md')
    output_dir = os.path.join(cur_dir, num)
    content_path = os.path.join(output_dir, f'content{num}.md')

    if not (check_path(template_path) and check_path(content_path)):
        print(f"跳过：期号 {num} 的模板或内容文件缺失")
        return

    template_data = read_file(template_path).replace(NUM_FLAG, num)
    content_data = read_file(content_path)
    output_data = template_data.replace(CONTENT_FLAG, content_data)

    output_file = os.path.join(output_dir, f'HelloGitHub{num}.md')
    write_file(output_file, output_data)

    print(f'成功生成：《HelloGitHub》第 {num} 期')


def make_all_content():
    """
    批量生成当前目录下所有有效期号的月刊
    """
    cur_dir = os.path.abspath(os.curdir)
    for item in os.listdir(cur_dir):
        item_path = os.path.join(cur_dir, item)
        if os.path.isdir(item_path) and item.isdigit():
            make_content(item)


def main():
    """主入口函数"""
    try:
        args = sys.argv
        if len(args) != 2:
            raise InputError('输入错误：需要一个参数（期号或 "all"）')

        input_arg = args[1].lower()

        if input_arg == 'all':
            make_all_content()
        elif input_arg.isdigit():
            # 如果是单数字补0，比如 '1' -> '01'
            if len(input_arg) == 1:
                input_arg = f'0{input_arg}'
            make_content(input_arg)
        else:
            raise InputError('输入错误：参数必须是数字或 "all"')
    except InputError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"程序异常退出：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()