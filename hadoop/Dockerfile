FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV HADOOP_HOME=/opt/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
ENV HADOOP_VERSION=3.3.6

# 1. Instalar dependencias del sistema, Java 17, Python 3 y OpenSSH Server
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    python3 \
    python3-pip \
    openssh-server \
    openssh-client \
    curl \
    tar \
    procps \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 2. Descargar e instalar Apache Hadoop en modo standalone
RUN curl -fSL "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" -o /tmp/hadoop.tar.gz \
    && mkdir -p /opt/hadoop \
    && tar -xzf /tmp/hadoop.tar.gz -C /opt/hadoop --strip-components=1 \
    && rm -f /tmp/hadoop.tar.gz

# 3. Configurar variables en hadoop-env.sh
RUN echo "export JAVA_HOME=${JAVA_HOME}" >> ${HADOOP_HOME}/etc/hadoop/hadoop-env.sh

# 4. Crear usuario 'hadoop' para ejecución y acceso SSH seguro
RUN useradd -m -s /bin/bash hadoop \
    && echo "hadoop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 5. Configurar OpenSSH Server y llaves sin contraseña (ssh-keygen + authorized_keys)
RUN mkdir -p /var/run/sshd \
    && mkdir -p /home/hadoop/.ssh \
    && ssh-keygen -t rsa -P '' -f /home/hadoop/.ssh/id_rsa \
    && cat /home/hadoop/.ssh/id_rsa.pub >> /home/hadoop/.ssh/authorized_keys \
    && chmod 700 /home/hadoop/.ssh \
    && chmod 600 /home/hadoop/.ssh/authorized_keys \
    && chown -R hadoop:hadoop /home/hadoop/.ssh

# Configurar SSH también para root y deshabilitar verificación de host estricta
RUN mkdir -p /root/.ssh \
    && cp /home/hadoop/.ssh/id_rsa /root/.ssh/id_rsa \
    && cp /home/hadoop/.ssh/authorized_keys /root/.ssh/authorized_keys \
    && chmod 700 /root/.ssh \
    && chmod 600 /root/.ssh/authorized_keys \
    && echo "Host *\n    StrictHostKeyChecking no\n    UserKnownHostsFile /dev/null\n" >> /etc/ssh/ssh_config

# 6. Preparar directorios de trabajo y datos
RUN mkdir -p /data/input /data/output /mapreduce \
    && chown -R hadoop:hadoop /data /mapreduce

# 7. Copiar script de arranque
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /mapreduce

EXPOSE 22

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
