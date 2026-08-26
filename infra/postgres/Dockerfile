FROM postgres:16

# rum: full-text indexes for news.titles / news.annotations (see migration news/00001_init_schema.sql)
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-rum \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
