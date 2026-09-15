FROM lscr.io/linuxserver/webtop@sha256:c4ceafc1c48ed9a61771345c74568d3bff6438802f0d89e9ebd9846e8404f696

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-tk python3-venv xdotool x11-apps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/workshop/requirements.txt
RUN python3 -m venv /opt/taaled-venv \
    && /opt/taaled-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/taaled-venv/bin/pip install --no-cache-dir -r /opt/workshop/requirements.txt

COPY app /opt/workshop/app
COPY bin /opt/workshop/bin
COPY desktop /opt/workshop/desktop
COPY root/ /

RUN chmod 755 /opt/workshop/bin/launch-taales-workshop.sh \
    /etc/cont-init.d/50-workshop-setup
