#!/bin/bash

# Start Xvfb
echo "Starting Xvfb"
Xvfb :99 -ac -screen 0 $XVFB_WHD -nolisten tcp &
xvfb_pid="$!"

# possible race condition waiting for Xvfb.
sleep 5

if [ ! -d /visualization/git_repos ]; then
    # Clone our git repo for the visualization.
    if [ ! -d /visualization/git_repo ]; then
        git clone ${GIT_URL} git_repo
    fi
    echo "Using volume mounted git repo"
    gource --output-custom-log development.log git_repo
else
    FILES=
    for D in /visualization/git_repos/*; do
        if [ -d "${D}" ]; then
            NAME=${D##*/}
            echo "Using volume mounted git repo $D as ${NAME}"
            gource --output-custom-log ${NAME}.log $D
            sed -i -r "s#(.+)\|#\1|/$NAME#" ${NAME}.log
            FILES="$FILES ${NAME}.log"
        fi
    done
    cat ${FILES} | sort -n > development.log
fi

# Set proper env variables if we have a logo.
if [ "${LOGO_URL}" != "" ]; then
    wget -O ./logo.image ${LOGO_URL}
    convert -geometry x160 ./logo.image ./logo.image
    if [ "$?" = 0 ]; then
        echo "Using logo from: ${LOGO_URL}"
        export LOGO=" -i ./logo.image "
        if [[ "${TEMPLATE}" == "border" ]]; then
            export LOGO_FILTER_GRAPH=";[with_date][2:v]overlay=main_w-overlay_w-40:main_h-overlay_h-40[with_logo]"
            export FILTER_GRAPH_MAP=" -map [with_logo] "
        else
            export LOGO_FILTER_GRAPH="[1:v]overlay=main_w-overlay_w-40:main_h-overlay_h-40[with_logo]"
            export FILTER_GRAPH_MAP=" -map [with_logo] "
        fi
    else
        if [[ "${TEMPLATE}" == "border" ]]; then
            echo "Not using a logo."
            export FILTER_GRAPH_MAP=" -map [with_date] "
        else
            export FILTER_GRAPH_MAP=""
        fi
    fi
else
    if [[ "${TEMPLATE}" == "border" ]]; then
        echo "Not using a logo."
        export FILTER_GRAPH_MAP=" -map [with_date] "
    else
        export FILTER_GRAPH_MAP=""
    fi
fi

/visualization/border_template.sh


# Exit
echo "Exiting"
exit