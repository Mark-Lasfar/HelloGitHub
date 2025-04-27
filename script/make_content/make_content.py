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
支持多语言支持，异常处理和其他功能增强。
"""

import sys
import os
import gettext
from concurrent.futures import ThreadPoolExecutor

# Set up multi-language support
locale_dir = os.path.join(os.path.abspath(os.curdir), 'locales')
lang = gettext.translation('messages', localedir=locale_dir, languages=['en'])
lang.install()

# Placeholders for template replacement
CONTENT_FLAG = '{{ hello_github_content }}'
NUM_FLAG = '{{ hello_github_num }}'


class InputError(Exception):
    """Custom exception: Invalid input error"""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return repr(self.message)


class FileWriteError(Exception):
    """Custom exception: File write error"""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return repr(self.message)


def check_path(path):
    """Check if the file or directory exists"""
    if not os.path.exists(path):
        print(f'{_("Error: Path does not exist")} -> {path}')
        return False
    return True


def check_write_permission(path):
    """Check if the path is writable"""
    if not os.access(path, os.W_OK):
        raise FileWriteError(f"{_('No write permission to the file')} -> {path}")
    return True


def read_file(file_path):
    """Read file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"{_('File not found')} -> {file_path}")
    except Exception as e:
        raise Exception(f"{_('Error reading file')}: {e}")


def write_file(file_path, data):
    """Write content to a file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
    except PermissionError:
        raise FileWriteError(f"{_('No write permission to the file')} -> {file_path}")
    except Exception as e:
        raise FileWriteError(f"{_('Error writing to file')}: {e}")


def make_content(num, custom_filename=None):
    """
    Generate the monthly content file based on the given issue number
    :param num: The issue number, e.g. '01', '02', '10', etc.
    :param custom_filename: Optional custom filename for the output
    """
    cur_dir = os.path.abspath(os.curdir)
    template_path = os.path.join(cur_dir, 'template.md')
    output_dir = os.path.join(cur_dir, num)
    content_path = os.path.join(output_dir, f'content{num}.md')

    if not (check_path(template_path) and check_path(content_path)):
        print(f"{_('Skipping')} {num} {_('due to missing template or content files')}")
        return

    template_data = read_file(template_path).replace(NUM_FLAG, num)
    content_data = read_file(content_path)
    output_data = template_data.replace(CONTENT_FLAG, content_data)

    # Define output filename, using custom filename if provided
    output_filename = f'HelloGitHub{num}.md' if not custom_filename else custom_filename
    output_file = os.path.join(output_dir, output_filename)

    check_write_permission(output_dir)  # Check write permission to the output directory
    write_file(output_file, output_data)

    print(f'{_("Successfully generated")} 《HelloGitHub》第 {num} 期')


def make_all_content():
    """Generate all valid issue files in the current directory"""
    cur_dir = os.path.abspath(os.curdir)
    with ThreadPoolExecutor() as executor:
        for item in os.listdir(cur_dir):
            item_path = os.path.join(cur_dir, item)
            if os.path.isdir(item_path) and item.isdigit():
                executor.submit(make_content, item)  # Run make_content in parallel for each directory


def sanitize_filename(filename):
    """
    Clean up the filename by removing invalid characters
    :param filename: Original filename
    :return: Cleaned-up filename
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def main():
    """Main entry function"""
    try:
        args = sys.argv
        if len(args) < 2:
            raise InputError(_('Input error: Need one parameter (Issue number or "all")'))

        input_arg = args[1].lower()

        # Handle optional custom filename argument
        custom_filename = None
        if len(args) == 3:
            custom_filename = sanitize_filename(args[2])

        if input_arg == 'all':
            make_all_content()
        elif input_arg.isdigit():
            # Pad single-digit numbers with leading zeros, e.g., '1' -> '01'
            if len(input_arg) == 1:
                input_arg = f'0{input_arg}'
            make_content(input_arg, custom_filename)
        else:
            raise InputError(_('Input error: Parameter must be a number or "all"'))

    except InputError as e:
        print(f"{_('Input error')}: {e}")
        sys.exit(1)
    except FileWriteError as e:
        print(f"{_('File write error')}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{_('Program exited unexpectedly')}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()