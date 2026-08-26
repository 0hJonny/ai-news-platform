FROM postgres:16
RUN localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8
ENV LANG ru_RU.utf8
RUN apt update && apt install -y postgresql-16-rum postgresql-16-postgis-3 postgresql-16-pgrouting cron nano && apt-get clean && rm -rf /var/lib/apt/lists/*

# Substitute environment variables in the SQL file
ARG ADMIN_USERNAME
ARG ADMIN_PASSWORD
COPY initdb/init.sql /docker-entrypoint-initdb.d
RUN sed -i "s/\${ADMIN_USERNAME}/$ADMIN_USERNAME/g; s/\${ADMIN_PASSWORD}/$ADMIN_PASSWORD/g" /docker-entrypoint-initdb.d/init.sql