#! /bin/bash
jupyter-nbconvert --to python generate_config.ipynb
jupyter-nbconvert --to python run.ipynb
python generate_config.py

./download_music.bash