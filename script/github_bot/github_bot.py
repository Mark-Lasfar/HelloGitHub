#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   XueWeiHan
#   E-mail  :   595666367@qq.com
#   Date    :   2025-04-27
#   Desc    :   Github Bot
import os
import logging
import smtplib
import datetime
from operator import itemgetter
from email.mime.text import MIMEText
from email.header import Header
import requests

# Logging setup
logging.basicConfig(
    level=logging.WARNING,
    filename=os.path.join(os.path.dirname(__file__), 'bot_log.txt'),
    filemode='a',
    format='%(name)s %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
)
logger = logging.getLogger('Bot')  # Log name

# GitHub account details
ACCOUNT = {
    'username': os.getenv('GITHUB_USERNAME', ''),
    'password': os.getenv('GITHUB_PASSWORD', '')
}

# API to fetch events
API = {
    'events': 'https://api.github.com/users/{username}/received_events'.format(username=ACCOUNT['username'])
}

# Email sending details
MAIL = {
    'mail': os.getenv('MAIL_SENDER', ''),  # Sender email
    'username': os.getenv('MAIL_USERNAME', ''),
    'password': os.getenv('MAIL_PASSWORD', ''),
    'host': 'smtp.qq.com',
    'port': 465
}

# Receivers
RECEIVERS = os.getenv('MAIL_RECEIVERS', '').split(',')

# Days ago
DAY = 1

# Stars threshold
STARS = 100

# HTML content format
CONTENT_FORMAT = """
    <table border="2" align="center">
      <tr>
        <th>Avatar</th>
        <th>Username</th>
        <th>Repository</th>
        <th>Starred Date</th>
        <th>Stars</th>
      </tr>
      {project_info_string}
    </table>
"""

def get_data(page=1):
    """
    Fetch data from the API
    """
    args = '?page={page}'.format(page=page)
    response = requests.get(API['events'] + args, auth=(ACCOUNT['username'], ACCOUNT['password']))
    status_code = response.status_code
    if status_code == 200:
        return response.json()
    else:
        logger.error(f'Failed to request events API: {status_code}')
        return []

def get_all_data():
    """
    Fetch all data (up to 300 events)
    """
    all_data = []
    for i in range(10):
        data = get_data(i + 1)
        if data:
            all_data.extend(data)
    return all_data

def check_condition(data):
    """
    Check if the data meets the condition
    """
    create_time = datetime.datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=8)
    date_condition = create_time >= (datetime.datetime.now() - datetime.timedelta(days=DAY))
    if data['type'] == 'WatchEvent' and date_condition:
        if data['payload']['action'] == 'started' and ACCOUNT['username'] not in data['repo']['name']:
            data['date_time'] = create_time.strftime("%Y-%m-%d %H:%M:%S")
            return True
    return False

def analyze(json_data):
    """
    Analyze the data
    """
    result_data = []
    for fi_data in json_data:
        if check_condition(fi_data):
            result_data.append(fi_data)
    return result_data

def get_stars(data):
    """
    Get the star count for repositories and filter out projects with fewer stars than the threshold
    """
    project_info_list = []
    for fi_data in data:
        project_info = {
            'user': fi_data['actor']['login'],
            'user_url': f'https://github.com/{fi_data["actor"]["login"]}',
            'avatar_url': fi_data['actor']['avatar_url'],
            'repo_name': fi_data['repo']['name'],
            'repo_url': f'https://github.com/{fi_data["repo"]["name"]}',
            'date_time': fi_data['date_time']
        }
        try:
            repo_stars = requests.get(fi_data['repo']['url'], timeout=2).json()
            project_info['repo_stars'] = repo_stars.get('stargazers_count', -1)
        except Exception as e:
            project_info['repo_stars'] = -1
            logger.warning(f"Failed to fetch stars for {project_info['repo_name']} - {e}")
        
        if project_info['repo_stars'] >= STARS or project_info['repo_stars'] == -1:
            project_info_list.append(project_info)
    
    # Sort projects by star count
    project_info_list = sorted(project_info_list, key=itemgetter('repo_stars'), reverse=True)
    return project_info_list

def make_content():
    """
    Prepare the content for the email
    """
    json_data = get_all_data()
    data = analyze(json_data)
    content = []
    project_info_list = get_stars(data)
    for project_info in project_info_list:
        project_info_string = f"""
            <tr>
                <td><img src={project_info['avatar_url']} width=32px></td>
                <td><a href={project_info['user_url']}>{project_info['user']}</a></td>
                <td><a href={project_info['repo_url']}>{project_info['repo_name']}</a></td>
                <td>{project_info['date_time']}</td>
                <td>{project_info['repo_stars']}</td>
            </tr>
        """
        content.append(project_info_string)
    return content

def send_email(receivers, email_content):
    """
    Send the email
    """
    if not receivers:
        logger.warning("No email receivers specified. Email will not be sent.")
        return

    sender = MAIL['mail']
    message = MIMEText(CONTENT_FORMAT.format(project_info_string=''.join(email_content)), 'html', 'utf-8')
    message['From'] = Header('GitHub Bot', 'utf-8')
    message['To'] = Header('GitHub User', 'utf-8')
    subject = 'GitHub Starred Projects Today'
    message['Subject'] = Header(subject, 'utf-8')
    
    try:
        with smtplib.SMTP_SSL(MAIL['host'], MAIL['port']) as smtp:
            smtp.login(MAIL['username'], MAIL['password'])
            smtp.sendmail(sender, receivers, message.as_string())
        logger.info("Email sent successfully.")
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email: {e}")

if __name__ == '__main__':
    content = make_content()
    send_email(RECEIVERS, content)