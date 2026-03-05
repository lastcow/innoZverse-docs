# 🔒 Linux Advanced

**20 labs · Ubuntu 22.04 · Docker-verified (--privileged)**

Tune, harden, and manage complex Linux systems. Prerequisites: Linux Practitioner.

---

## Labs

| # | Lab | Topics |
|---|-----|--------|
| 01 | [sysctl — Kernel Parameters](labs/lab-01-sysctl-kernel-parameters.md) | /proc/sys/, net/vm/fs/kernel params |
| 02 | [Performance Profiling with perf](labs/lab-02-performance-profiling-perf.md) | perf stat/record/report, flamegraphs |
| 03 | [strace — System Call Tracing](labs/lab-03-strace-system-call-tracing.md) | strace -e/-c/-f/-tt, syscall analysis |
| 04 | [lsof — Open Files & Sockets](labs/lab-04-lsof-open-files-sockets.md) | lsof -i/-p/-u, deleted files, ports |
| 05 | [CPU & Memory Profiling](labs/lab-05-cpu-memory-profiling.md) | /proc/meminfo, OOM killer, taskset |
| 06 | [Linux Security Hardening](labs/lab-06-linux-security-hardening.md) | CIS controls, SSH hardening, chattr |
| 07 | [SELinux — Policies & Labels](labs/lab-07-selinux-policies-labels.md) | modes, contexts, chcon, audit2allow |
| 08 | [AppArmor — Profiles](labs/lab-08-apparmor-profiles.md) | aa-enforce, profiles, deny rules |
| 09 | [auditd — System Auditing](labs/lab-09-auditd-system-auditing.md) | auditctl, ausearch, aureport, rules |
| 10 | [fail2ban — Intrusion Prevention](labs/lab-10-fail2ban-intrusion-prevention.md) | jails, filters, fail2ban-client |
| 11 | [LVM — Logical Volume Management](labs/lab-11-lvm-logical-volume-management.md) | pvcreate, vgcreate, lvcreate, extend |
| 12 | [Software RAID with mdadm](labs/lab-12-software-raid-mdadm.md) | RAID 0/1/5, /proc/mdstat, recovery |
| 13 | [Filesystem Tuning — ext4, xfs, btrfs](labs/lab-13-filesystem-tuning-ext4-xfs-btrfs.md) | tune2fs, xfs_info, btrfs snapshots |
| 14 | [Disk Encryption with LUKS](labs/lab-14-luks-disk-encryption.md) | cryptsetup, luksFormat, /etc/crypttab |
| 15 | [Advanced Storage — NFS & Quotas](labs/lab-15-advanced-storage-nfs-quotas.md) | exportfs, NFS mount, quota tools |
| 16 | [Linux Namespaces](labs/lab-16-linux-namespaces.md) | unshare, nsenter, lsns, PID/NET/UTS |
| 17 | [cgroups — Resource Control](labs/lab-17-cgroups-resource-control.md) | memory.max, cpu.max, pids.max |
| 18 | [Docker Internals](labs/lab-18-docker-internals.md) | overlay2, veth pairs, runc, containerd |
| 19 | [systemd Deep Dive](labs/lab-19-systemd-deep-dive.md) | unit files, timers, socket activation |
| 20 | [Capstone — Hardened Container-Ready Server](labs/lab-20-capstone-hardened-container-ready-server.md) | full hardening + container security |

---

**Start here →** [Lab 01: sysctl — Kernel Parameters](labs/lab-01-sysctl-kernel-parameters.md)
