FROM lscr.io/linuxserver/webtop@sha256:c4ceafc1c48ed9a61771345c74568d3bff6438802f0d89e9ebd9846e8404f696 AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        featherpad \
        lximage-qt \
        lxqt-admin \
        lxqt-archiver \
        lxqt-core \
        oxygen-icon-theme \
        pavucontrol-qt \
        python3-tk \
        python3-venv \
        qlipper \
        qps \
        qterminal \
        x11-apps \
        x11-utils \
        xauth \
        xdotool \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/workshop/requirements.txt
RUN python3 -m venv /opt/taaled-venv \
    && /opt/taaled-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/taaled-venv/bin/pip install --no-cache-dir -r /opt/workshop/requirements.txt

COPY app /opt/workshop/app
COPY assets /opt/workshop/assets
COPY bin /opt/workshop/bin
COPY docs /opt/workshop/docs
COPY fixtures /opt/workshop/fixtures
COPY root/ /

RUN python3 /opt/workshop/bin/require-xauth.py

RUN chmod 755 /opt/workshop/bin/workshop-launch \
    /opt/workshop/bin/launch-taales-window \
    /opt/workshop/bin/install-navigation.py \
    /etc/s6-overlay/s6-rc.d/init-workstation/run \
    /defaults/startwm.sh

FROM runtime AS test

RUN apt-get update \
    && apt-get install -y --no-install-recommends xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && /opt/taaled-venv/bin/pip install --no-cache-dir pytest==8.4.2

COPY tests /opt/workshop/tests
COPY host /opt/workshop/host
COPY macos /opt/workshop/macos
COPY compose.yaml /opt/workshop/compose.yaml
RUN cd /opt/workshop && xvfb-run -a /opt/taaled-venv/bin/python -m pytest -q
