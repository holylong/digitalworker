   openclaw cron add \
     --name "提醒喝水-用户" \
     --at "5m" \
     --session isolated \
     --message "💧 该喝水啦！" \
     --deliver \
     --channel qqbot \
     --to "4F69BDAA46E04AC7F97A2AE9BF4C9D66" \
     --delete-after-run