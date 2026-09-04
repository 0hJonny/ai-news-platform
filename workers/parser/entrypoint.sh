#!/bin/sh
set -e

# cron (via /etc/cron.d) runs jobs with its own minimal environment — it does
# NOT inherit the container's `environment:` block from docker-compose.yml.
# Dump the environment this container actually started with into a file
# outside the /app bind mount (so it isn't written back onto the host repo),
# and have cronjob explicitly source it before running producer.py. Without
# this, GOLANG_API/CELERY_BROKER_URL/API_USER_* would silently fall back to
# producer.py's/celery_app.py's localhost-only defaults instead of the
# compose-provided values (redis://redis:6379/0 etc.).
printenv | grep -Ev '^(HOME|PWD|OLDPWD|SHLVL|_)=' | sed 's/^/export /' > /etc/cron_env.sh
chmod 0600 /etc/cron_env.sh

exec "$@"
