# 夜间休眠

用户声明机器夜里要睡时使用本文件。只适用于 Linux（systemd + RTC）。

机器挂起期间，`sleep`、`at` 这类定时不走，没有闹钟机器也不会自己醒。所以唤醒靠 RTC 闹钟，续跑靠比较墙钟。

## Master

1. 停：等进行中的调用结束，在两个工作单元之间停进程，写一个带原因的 STOP 文件。不杀进行中的调用。
2. 设闹钟：`sudo -n rtcwake -m no -t $(date -d '<唤醒时刻>' +%s)`，再读 `/sys/class/rtc/rtc0/wakealarm` 核对等于目标 epoch。`-m no` 只设闹钟不挂起。
3. 续跑：一个每 60 秒比较 `date +%s` 与目标 epoch 的循环，到点删掉夜间停和额度重试类的 STOP 并重启。预算、质量门、人工写的 STOP 不删，只报。
4. 闹钟值、脚本路径、STOP 原因表写进交接文件的"坑"段和 Ticket，并回报给 Conductor。
5. sudo 没有放行 `rtcwake` 时，退回"用户唤醒 + 墙钟循环"，在 status 里说明。剩余风险写进交接文件：别的进程再调 `rtcwake` 会覆盖闹钟；机器被关机而不是挂起时，闹钟可能不触发。

## Conductor

1. 挂起前确认：各 Master 已停并回报了闹钟值；`worker-list --run` 里没有 live Dispatch；两个仓库工作树干净。然后停自己的 waiter，不再重挂。
2. 用 Orca automation 定早上续跑（`orca.md`"定时与自动续跑"），prompt 写"读交接文件 + `run-use <run>` + 接着做什么"。交接文件按 `references/handoff.md` 第 2 条，带上闹钟值和脚本路径。
3. 机器由用户挂起；要代为挂起时用 `systemctl suspend -i`。
4. 早上的新 session `run-use` 后，旧 session 的 waiter 会被顶掉，这是正常的。旧 session 之后不再 `run-use`。
5. 早上核对：`journalctl -q | grep "PM: suspend exit"` 的时间对照 Master 的重启时间。没按时重启就让 Master 手动续，并查原因。
6. 只想续跑一次时，用完就关掉 automation。
7. Master 的 Spec"环境说明"段写一句："夜间机器会挂起，按 references/night.md 处理。"
