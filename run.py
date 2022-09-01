#!/usr/bin/env python
# coding: utf-8

# In[48]:


import re
import json
import os
from datetime import datetime, timedelta
import subprocess
import time

from bilibiliuploader.bilibiliuploader import BilibiliUploader
from bilibiliuploader.core import VideoPart

from git import Repo
import docker
import shutil
import glob
import random



# In[58]:


def _select_music_as_background():
    musics = glob.glob('mp3s/*mp3')
    random_music = random.choice(musics)
    shutil.copy2(random_music, 'mp3s/background.mp3')
    return os.path.basename(random_music).replace('.mp3', '')


# In[1]:


def _now():
    return time.strftime("%Y-%m-%d", time.localtime())


def _month_ago():
    return (datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d")


# In[59]:


def _generate_video():
    info=json.load(open(os.environ['json_file']))
    pwd = os.getcwd()
    client = docker.from_env()
    client.containers.run(image='utensils/envisaged',
                          remove=True,
                          volumes=[f'{pwd}/mp3s/background.mp3:/tmp/background.mp3',
                                   f'{pwd}/border_template.sh:/visualization/border_template.sh',
                                   f'{pwd}/results/:/visualization/output/', f'{pwd}/docker-entrypoint.sh:/usr/local/bin/entrypoint.sh'],
                          environment=[
                              f'''GIT_URL={info["html_url"]}''',
                              f'''GOURCE_TITLE="{info['name']}"''',
                              'mp3=/tmp/background.mp3',
                              'VIDEO_RESOLUTION=2160p',
                              'GOURCE_SECONDS_PER_DAY=3'
                          ])
    os.rename('results/output.mp4', 'wait_uploads/{}.mp4'.format(info['name']))
    return 'wait_uploads/{}.mp4'.format(info['name']),info


# In[4]:


def _up_load(video, music, info, now,lang):
    uploader = BilibiliUploader()
    uploader.login_by_access_token(os.environ['access_token'], os.environ['refresh_token'])
    parts = [
        VideoPart(
            path=video,
            title=f'{now}: Github Trending of {lang} : {int(os.environ["number"])+1} - {info["name"]}',
            desc=f'''
bgm: {music}
repo: {info['html_url']}
stars: {info['stargazers_count']}
description: {info['description']}
Stars today: {info['date_range']}
            '''
        )
    ]
    
    avid, bvid = uploader.upload(
        parts=parts,
        copyright=1,
        title=f'{now}: Github Trending of {lang} : {int(os.environ["number"])+1} - {info["name"]}',
        tid=95,
        tag=f"{lang},{info['name']},{now}",
        desc=f'''
bgm: {music}
repo: {info['html_url']}
stars: {info['stargazers_count']}
description: {info['description']}
Stars today: {info['date_range']}
            ''',
        source='Github Trending',
        thread_pool_workers=5,
        cover=os.environ['jpg']
    )


# In[ ]:


def main():
    lang = os.environ['language']
    today = _now()
    music = _select_music_as_background()
    print(lang,today,music,os.environ['number'])
    video, info = _generate_video()
    _up_load(video, music, info, today, lang)


# In[ ]:


if __name__ == '__main__':
    main()

