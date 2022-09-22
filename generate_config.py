#!/usr/bin/env python
# coding: utf-8

# In[1]:


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
from PIL import Image, ImageFont, ImageDraw



# could be made into config option in the future
CACHED_RESULT_PATH = xdg_cache_home() / "starcli.json"
CACHE_EXPIRATION = 1  # Minutes


# In[2]:


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


# In[3]:


def _now():
    return time.strftime("%Y-%m-%d", time.localtime()) 

def _month_ago():
    return (datetime.now()-timedelta(days =30)).strftime("%Y-%m-%d")


# In[4]:


def _select_music_as_background():
    musics = glob.glob('mp3s/*mp3')
    random_music = random.choice(musics)
    shutil.copy2(random_music, 'mp3s/background.mp3')
    return os.path.basename(random_music).replace('.mp3', '')


# In[5]:


def generate_show_photo(image, lang, name, n):
 
    image = Image.open('background.png')
    title_font = ImageFont.truetype('Pacifico.ttf', 100)
    title_text = f'''{_now()}
Github Trending 
{lang}:{n}
{name}'''
    image_editable = ImageDraw.Draw(image)
    image_editable.text((15, 315), title_text,
                        (237, 230, 211), font=title_font)
    image.save(f'figures/{lang}_{n}.png')


# In[6]:


def _generate_ga_config(info_list,  lang):
    default_config = f'''
name: github_trending_{lang}
on:
  schedule:
    - cron: "0 5 * * *"
  workflow_dispatch:
jobs:
    '''
    for i, j in enumerate(info_list):
        generate_show_photo('background.png', lang, j["name"], i)
        config = f'configs/{j["name"]}.json'
        with open(config, 'w') as f:
            json.dump(j, f, indent=4)
        default_config += f'''
  {lang}_github_trending_{i}:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      - uses: actions/checkout@v2
      - name: get Environment
        run: |
          sudo apt update
          sudo apt install ffmpeg
          export refresh_token="${{{{ secrets.refresh_token }}}}"
          export access_token="${{{{ secrets.access_token }}}}"
          export json_file={config}
          export number={i}
          export language={lang}
          pip install git+https://github.com/FortuneDayssss/BilibiliUploader.git
          pip install -r requirements.txt
          wecover "GithubTrending_{lang}_{j['name']}"
          export jpg="figures/{lang}_{i}.png"
          python run.py        
'''

    return default_config


# In[7]:


def main(lang):
    info_list = _cli(lang)
    today = _now()
    
    with open(f'.github/workflows/github_trending_{lang}.yaml', 'w') as f:
        f.write(_generate_ga_config(info_list,  lang))
   


# In[8]:


if __name__ == '__main__':
    main('python')
    main('java')
    main('javascript')
    main('go')
    main('R')
    main('c')
    main('Perl')


# 

# In[ ]:




