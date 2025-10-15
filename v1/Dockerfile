
FROM ubuntu:22.04

# Dépendances système
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-dev python3-pip \
    git zip unzip openjdk-17-jdk wget curl \
    zlib1g-dev libncurses5-dev libstdc++6 libffi-dev libssl-dev \
    autoconf automake libtool pkg-config cmake ninja-build build-essential ccache \
    libgl1-mesa-dev libgles2-mesa-dev && \
    rm -rf /var/lib/apt/lists/*

# Mettre à jour pip
RUN python3 -m pip install --upgrade pip

# Installer Buildozer et Cython
RUN python3 -m pip install buildozer cython==0.29.36

# Créer un utilisateur non-root
RUN useradd -ms /bin/bash buildozeruser
USER buildozeruser
WORKDIR /app

# Variables d'environnement Android
ENV ANDROID_HOME=/home/buildozeruser/android-sdk
ENV PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH

# Installer Android Command Line Tools
RUN mkdir -p $ANDROID_HOME/cmdline-tools
WORKDIR $ANDROID_HOME
RUN wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O cmdline-tools.zip && \
    unzip cmdline-tools.zip -d cmdline-tools && \
    rm cmdline-tools.zip && \
    mv cmdline-tools/cmdline-tools cmdline-tools/latest

# Accepter toutes les licences et installer SDK + build-tools stables
RUN yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --sdk_root=$ANDROID_HOME --licenses
RUN $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --sdk_root=$ANDROID_HOME \
    "platform-tools" \
    "platforms;android-33" \
    "build-tools;33.0.2"

WORKDIR /app
