# Cron Jobs & Scheduling

## Cron Syntax

```
* * * * * command
│ │ │ │ │
│ │ │ │ └── Day of week (0-7, 0=Sunday)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

## Common Patterns

```bash
# Every minute
* * * * * /script.sh

# Every hour at minute 0
0 * * * * /script.sh

# Every day at 2:30 AM
30 2 * * * /script.sh

# Every Monday at 9 AM
0 9 * * 1 /script.sh

# Every 15 minutes
*/15 * * * * /script.sh

# First day of every month at midnight
0 0 1 * * /script.sh
```

## Managing Crontab

```bash
crontab -e          # Edit your crontab
crontab -l          # List current crontab
crontab -r          # Remove your crontab
sudo crontab -u alice -e    # Edit another user's crontab
```

## Practical Examples

```bash
# Daily backup at 3 AM
0 3 * * * /home/alice/scripts/backup.sh >> /var/log/backup.log 2>&1

# Clear temp files every Sunday at midnight
0 0 * * 0 rm -rf /tmp/myapp/*

# Check disk space every 6 hours, alert if >80%
0 */6 * * * df -h | awk '$5 > 80 {print $0}' | mail -s "Disk Alert" admin@example.com
```

## systemd Timers (Modern Alternative)

```bash
# List all timers
systemctl list-timers

# View timer status
systemctl status my-timer.timer
```
