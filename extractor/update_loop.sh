#!/bin/sh
# 起動時に1回、その後 INTERVAL 秒(既定 1日)ごとに問題データを更新する。
cd "$(dirname "$0")" || exit 1
INTERVAL="${UPDATE_INTERVAL_SECONDS:-86400}"

while true; do
    echo "[$(date '+%F %T')] update start"
    if python autodl.py && python get_text.py; then
        echo "[$(date '+%F %T')] update done"
    else
        echo "[$(date '+%F %T')] update FAILED (次回 ${INTERVAL}s 後に再試行)"
    fi
    sleep "$INTERVAL"
done
