#!/usr/bin/env python
# coding: utf-8

# In[48]:


from starcli.layouts import print_results, shorten_count
from starcli.search import (
    search,
    debug_requests_on,
    search_github_trending,
    search_error,
    status_actions,
)
from xdg import xdg_cache_home
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



# could be made into config option in the future
CACHED_RESULT_PATH = xdg_cache_home() / "starcli.json"
CACHE_EXPIRATION = 1  # Minutes


# In[56]:


def _cli(
    lang='',
    spoken_language='',
    created='',
    topic=[],
    pushed='',
    layout='list',
    stars='>=100',
    limit_results=10,
    order='desc',
    long_stats=True,
    date_range='today',
    user='',
    debug=False,
    auth="",
    pager=False,
):
    """Find trending repos on GitHub"""
    if debug:
        import logging

        debug_requests_on()

    tmp_repos = None
    options_key = "{lang}_{spoken_language}_{created}_{topic}_{pushed}_{stars}_{order}_{date_range}_{user}".format(
        lang=lang,
        spoken_language=spoken_language,
        created=created,
        topic=topic,
        pushed=pushed,
        stars=stars,
        order=order,
        date_range=date_range,
        user=user,
    )

    if os.path.exists(CACHED_RESULT_PATH):
        with open(CACHED_RESULT_PATH, "r") as f:
            json_file = json.load(f)
            result = json_file.get(options_key)
            if result:
                t = result[-1].get("time")
                time = datetime.strptime(t, "%Y-%m-%d %H:%M:%S.%f")
                diff = datetime.now() - time
                if diff < timedelta(minutes=CACHE_EXPIRATION):
                    if debug:
                        logger = logging.getLogger(__name__)
                        logger.debug("Fetching results from cache")

                    tmp_repos = result

    if not tmp_repos:  # If cache expired or results not yet cached

        if (
            not spoken_language and not date_range
        ):  # if filtering by spoken language and date range not required
            tmp_repos = search(
                lang, created, pushed, stars, topic, user, debug, order, auth
            )
        else:
            tmp_repos = search_github_trending(
                lang, spoken_language, order, stars, date_range
            )

        if not tmp_repos:  # if search() returned None
            return
        else:  # Cache results
            tmp_repos.append({"time": str(datetime.now())})
            with open(CACHED_RESULT_PATH, "a+") as f:
                if os.path.getsize(CACHED_RESULT_PATH) == 0:  # file is empty
                    result_dict = {options_key: tmp_repos}
                    f.write(json.dumps(result_dict, indent=4))
                else:  # file is not empty
                    f.seek(0)
                    result_dict = json.load(f)
                    result_dict[options_key] = tmp_repos
                    f.truncate(0)
                    f.write(json.dumps(result_dict, indent=4))

    repos = tmp_repos[0:limit_results]

    if not long_stats:  # shorten the stat counts when not --long-stats
        for repo in repos:
            repo["stargazers_count"] = shorten_count(repo["stargazers_count"])
            repo["watchers_count"] = shorten_count(repo["watchers_count"])
            if "date_range" in repo.keys() and repo["date_range"]:
                num_stars = repo["date_range"].split()[0]
                repo["date_range"] = repo["date_range"].replace(
                    num_stars, str(shorten_count(int(num_stars.replace(",", ""))))
                )
    return repos


# In[57]:


def _now():
    return time.strftime("%Y-%m-%d", time.localtime()) 

def _month_ago():
    return (datetime.now()-timedelta(days =30)).strftime("%Y-%m-%d")


# In[58]:


def _select_music_as_background():
    musics = glob.glob('mp3s/*mp3')
    random_music = random.choice(musics)
    shutil.copy2(random_music, 'mp3s/background.mp3')
    return os.path.basename(random_music).replace('.mp3', '')


# In[59]:


def _generate_video(info):
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
    return 'wait_uploads/{}.mp4'.format(info['name'])


# In[4]:


def _up_load(video_files, music_name_list, title_list, info_list, now,lang):
    uploader = BilibiliUploader()
    uploader.login_by_access_token(os.environ['access_token'], os.environ['refresh_token'])
    parts = []
    for i, j, k,l in zip(video_files, music_name_list, title_list, info_list):
        parts.append(VideoPart(
            path=i,
            title=k,
            desc=f'''
bgm: {j}
repo: {l['html_url']}
stars: {l['stargazers_count']}
description: {l['description']}
Stars today: {l['date_range']}
            '''
        ))
    # 上传
    avid, bvid = uploader.upload(
        parts=parts,
        copyright=1,
        title=f'{now}: Github Trending of {lang}',
        tid=95,
        tag=",".join(title_list),
        desc=f'Github Trending on {now} ',
        source='Github Trending',
        thread_pool_workers=5,
    )


# In[ ]:


def main(lang):
    info_list = _cli(lang)
    video_files = []
    music_name_list = []
    title_list = []
    today = _now()
    for idx,info in enumerate(info_list):
        music_name_list.append(_select_music_as_background())
        video_files.append(_generate_video(info))
        title_list.append(f"{idx}:{info['name']}")
    _up_load(video_files, music_name_list, title_list, info_list, today,lang)


# In[ ]:


if __name__ == '__main__':
    main('python')

