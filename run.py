#!/usr/bin/env python
# coding: utf-8

# In[54]:


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

# could be made into config option in the future
CACHED_RESULT_PATH = xdg_cache_home() / "starcli.json"
CACHE_EXPIRATION = 1  # Minutes


# In[55]:



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
        if auth and not re.search(".:.", auth):  # Check authentication format
            click.secho(
                f"Invalid authentication format: {auth} must be 'username:token'",
                fg="bright_red",
            )
            click.secho(
                "Use --help or see: https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token",
                fg="bright_red",
            )
            auth = None

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


# In[56]:


def _up_load(path,title,desc,tags):
    uploader = BilibiliUploader()
    uploader.login_by_access_token(os.environ['access_token'], os.environ['refresh_token'])
    parts = []
    parts.append(VideoPart(
        path=path,
        title=title,
        desc=desc
    ))
    # 上传
    avid, bvid = uploader.upload(
        parts=parts,
        copyright=1,
        title=title,
        tid=95,
        tag=",".join(tags),
        desc=desc,
        source='Github Trending',
        thread_pool_workers=5,
    )


# In[57]:


def _date():
    return time.strftime("%Y-%m-%d", time.localtime()) 

_date()


# In[61]:


def _generate_bash(repo_list,lang):
    if lang == '':
        lang = 'pan'
    
    for repo in repo_list:
        with open(f'{lang}.bash', 'w') as f:
            cmd = f'''
#!/bin/bash

set -x
set -e
echo "{repo['name']}"
mkdir -p avatars mp3s repo results
cp bg.mp3 mp3s/
git clone {repo['html_url']} repo
docker run --rm  -v {os.getcwd()}/repo:/repos -v {os.getcwd()}/results:/results -v {os.getcwd()}/avatars:/avatars -v {os.getcwd()}/mp3s:/mp3s sandrokeil/gource:latest
            '''
            f.write(cmd)
        p = subprocess.Popen(f'bash {os.getcwd()}/{lang}.bash', stdout=subprocess.PIPE,stderr=subprocess.PIPE ,shell=True)
        o,e = p.communicate()
        print(o,e)
        mp4_path = f'results/gource.mp4'
        _up_load(mp4_path,f'{_date()} Github Trending of {lang}', '每日Github趋势更新',['github trending',lang])
        os.remove(f'results')
        os.remove('repo')
        


# In[62]:


for i in ['python']:
    repo_list=_cli(i)
    _generate_bash(repo_list,i)


# In[ ]:




