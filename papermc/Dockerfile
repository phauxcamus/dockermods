FROM alpine:latest

VOLUME /data
WORKDIR /data

RUN apk -q --no-cache --update add openjdk21-jre-headless wget jq

RUN \
    rm paper.jar;
    export PAPER_VERSION=$(wget -qO - "https://api.papermc.io/v2/projects/paper" |jq -r '.versions[-1]') \
    && export PAPER_BUILD=$(wget -qO - "https://api.papermc.io/v2/projects/paper/versions/$PAPER_VERSION" |jq -r '.builds[-1]') \
    && export PAPER_JARNAME=paper-$PAPER_VERSION-$PAPER_BUILD.jar \
    && wget -nc --progress=bar:force:noscroll -O $PAPER_JARNAME "https://api.papermc.io/v2/projects/paper/versions/$PAPER_VERSION/builds/$PAPER_BUILD/downloads/$PAPER_JARNAME" \
    && ln -s $PAPER_JARNAME paper.jar

RUN apk -q del wget jq

ENV JAVA_TOOL_OPTIONS="-Xms4G -Xmx4G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true"

EXPOSE 25565/tcp 25565/udp

ENTRYPOINT ["java", "-server", "-jar", "paper.jar", "nogui"]

LABEL org.opencontainers.image.source="https://github.com/phauxcamus/dockermods"