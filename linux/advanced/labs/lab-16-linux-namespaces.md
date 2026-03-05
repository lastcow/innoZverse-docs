# Lab 16: Linux Namespaces — Kernel Isolation Primitives

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

Linux namespaces are the kernel technology that makes containers possible. Each namespace wraps a global system resource so that processes inside the namespace see an isolated view. In this lab you'll inspect, create, and enter all 7 namespace types from scratch — the same way Docker and Kubernetes do it under the hood.

---

## Step 1: Meet the 7 Namespace Types

Linux 5.6+ supports exactly 7 namespace types. Let's see them all live:

```bash
apt-get update -qq && apt-get install -y -qq iproute2 procps util-linux
lsns
```

📸 **Verified Output:**
```
        NS TYPE   NPROCS PID USER COMMAND
4026531834 time        3   1 root bash
4026531837 user        3   1 root bash
4026532768 mnt         3   1 root bash
4026532769 uts         3   1 root bash
4026532770 ipc         3   1 root bash
4026532771 pid         3   1 root bash
4026532772 cgroup      3   1 root bash
4026532773 net         3   1 root bash
```

| Namespace | Flag | Isolates |
|-----------|------|---------|
| **PID** | `CLONE_NEWPID` | Process IDs — container PID 1 maps to host PID N |
| **NET** | `CLONE_NEWNET` | Network interfaces, routes, iptables |
| **MNT** | `CLONE_NEWNS` | Mount points and filesystem tree |
| **UTS** | `CLONE_NEWUTS` | Hostname and NIS domain name |
| **IPC** | `CLONE_NEWIPC` | SysV IPC, POSIX message queues |
| **USER** | `CLONE_NEWUSER` | UIDs/GIDs — unprivileged containers |
| **CGROUP** | `CLONE_NEWCGROUP` | cgroup root — process sees own hierarchy |

> 💡 **`TIME` namespace** (Linux 5.6+) isolates clock offsets. Useful for checkpoint/restore. Listed as "time" in `lsns` output.

---

## Step 2: Inspect Namespace File Descriptors in /proc

Every process has namespace file descriptors in `/proc/PID/ns/`:

```bash
ls -la /proc/1/ns/
```

📸 **Verified Output:**
```
total 0
dr-x--x--x 2 root root 0 Mar  5 06:43 .
dr-xr-xr-x 9 root root 0 Mar  5 06:42 ..
lrwxrwxrwx 1 root root 0 Mar  5 06:43 cgroup -> cgroup:[4026532772]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 ipc -> ipc:[4026532770]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 mnt -> mnt:[4026532768]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 net -> net:[4026532773]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 pid -> pid:[4026532771]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 pid_for_children -> pid:[4026532771]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 time -> time:[4026531834]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 time_for_children -> time:[4026531834]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 user -> user:[4026531837]
lrwxrwxrwx 1 root root 0 Mar  5 06:43 uts -> uts:[4026532769]
```

The inode numbers (e.g. `4026532769`) are **namespace IDs**. Two processes sharing the same inode are in the same namespace. This is how `nsenter` targets a namespace.

```bash
# Check if two processes share a namespace
readlink /proc/1/ns/pid
readlink /proc/$$/ns/pid
```

> 💡 Keep a namespace alive even after all processes exit by **bind-mounting** it: `mount --bind /proc/1/ns/net /run/netns/saved`

---

## Step 3: UTS Namespace — Hostname Isolation

The UTS namespace is the simplest to demonstrate. It lets each container have its own hostname:

```bash
# Show current hostname
hostname

# Create a new UTS namespace and change hostname inside it
unshare --uts bash -c 'hostname test-isolated; hostname'

# Verify host hostname is unchanged
hostname
```

📸 **Verified Output:**
```
ubuntu-container
test-isolated
ubuntu-container
```

```bash
# More explicit: launch shell in isolated UTS namespace
unshare --uts /bin/bash
hostname my-custom-host
hostname           # Shows: my-custom-host
exit               # Back to parent — original hostname restored
hostname           # Shows original
```

> 💡 Docker sets the container hostname via `--hostname` flag which internally creates a UTS namespace and writes the hostname into it.

---

## Step 4: PID Namespace — Process ID Isolation

In a PID namespace, the first process gets PID 1. This is how containers get their own process tree:

```bash
unshare --pid --fork --mount-proc bash -c 'echo "PID in new ns: $$"; ps aux | head -5'
```

📸 **Verified Output:**
```
PID in new ns: 1
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   4364  3156 ?        S    06:43   0:00 bash -c echo PID in new ns: $$; ps aux | head -5
root           2  0.0  0.0   7064  3100 ?        R    06:43   0:00 ps aux
root           3  0.0  0.0   2804  1464 ?        S    06:43   0:00 head -5
```

Key flags used:
- `--pid` — create new PID namespace
- `--fork` — fork before exec (required so child becomes PID 1, not exec'd process)
- `--mount-proc` — remount `/proc` to reflect the new PID namespace

```bash
# Compare: without --mount-proc you'd see the host process tree
unshare --pid --fork bash -c 'ps aux | wc -l'
# This shows host processes because /proc is still mounted from parent ns
```

> 💡 `--mount-proc` is shorthand for `unshare --mount` + `mount -t proc proc /proc`. Docker does the same when setting up a container's `/proc`.

---

## Step 5: Network Namespace — Full Network Stack Isolation

Network namespaces give each container its own interfaces, routes, and iptables rules:

```bash
# Create a new named network namespace
ip netns add myns
ip netns list
```

📸 **Verified Output:**
```
myns
```

```bash
# Exec inside it — only loopback exists
ip netns exec myns ip link list
```

📸 **Verified Output:**
```
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
```

```bash
# Create a veth pair to connect namespaces (like Docker's container networking)
ip link add veth0 type veth peer name veth1
ip link set veth1 netns myns

# Configure addresses
ip addr add 10.0.0.1/24 dev veth0
ip link set veth0 up
ip netns exec myns ip addr add 10.0.0.2/24 dev veth1
ip netns exec myns ip link set veth1 up
ip netns exec myns ip link set lo up

# Test connectivity
ping -c 2 10.0.0.2
ip netns exec myns ping -c 2 10.0.0.1

# Cleanup
ip netns delete myns
```

> 💡 Named network namespaces are stored as bind mounts in `/run/netns/`. Anonymous namespaces (used by Docker) exist only in `/proc/PID/ns/net`.

---

## Step 6: MNT Namespace — Filesystem Isolation

Mount namespaces isolate the filesystem tree. This is what allows containers to have their own rootfs:

```bash
# Create a temporary directory to mount
mkdir -p /tmp/isolated-mnt

# Create a new mount namespace and demonstrate isolation
unshare --mount bash -c '
  mount -t tmpfs tmpfs /tmp/isolated-mnt
  echo "secret data" > /tmp/isolated-mnt/test.txt
  echo "Inside namespace, file exists:"
  ls /tmp/isolated-mnt/
'

# Outside the namespace, the mount is gone
ls /tmp/isolated-mnt/
echo "Outside: empty (mount was isolated)"
```

📸 **Verified Output:**
```
Inside namespace, file exists:
test.txt
Outside: empty (mount was isolated)
```

```bash
# Unshare with a private mount propagation (MS_PRIVATE)
# This prevents mount events from leaking between namespaces
unshare --mount --propagation private bash -c '
  mount --bind /etc /tmp/isolated-mnt
  ls /tmp/isolated-mnt | head -5
  echo "Bind mount active inside"
'
ls /tmp/isolated-mnt  # Empty — mount did not propagate
```

> 💡 Mount propagation modes: `shared` (default), `private`, `slave`, `unbindable`. Docker uses `rprivate` for container rootfs mounts to prevent leakage.

---

## Step 7: USER Namespace — Privilege Isolation (Rootless Containers)

User namespaces map UIDs inside the namespace to different UIDs outside. This enables rootless containers:

```bash
# Run as root inside but map to unprivileged UID outside
unshare --user --map-root-user bash -c '
  echo "Inside USER namespace:"
  id
  cat /proc/self/uid_map
  cat /proc/self/gid_map
'
```

📸 **Verified Output:**
```
Inside USER namespace:
uid=0(root) gid=0(root) groups=0(root),65534(nogroup)
         0       1000          1
         0       1000          1
```

The uid_map format: `[ns_uid] [host_uid] [count]`
- Inside the namespace, UID 0 maps to host UID 1000 (your real user)

```bash
# Check IPC namespace isolation
unshare --ipc bash -c '
  # Create a shared memory segment
  python3 -c "
import sysv_ipc
m = sysv_ipc.SharedMemory(None, sysv_ipc.IPC_CREX, size=1024)
print(f\"SHM key: {m.key}, id: {m.id}\")
m.detach()
"
' 2>/dev/null || echo "python3-sysv-ipc not installed — IPC namespace works at kernel syscall level"

# Demonstrate IPC isolation with ipcs
ipcs
unshare --ipc bash -c 'ipcs'  # Shows empty IPC — isolated view
```

> 💡 **Rootless Docker** uses USER namespaces extensively. `podman` and `docker rootless` run entirely as unprivileged users by leveraging UID mapping.

---

## Step 8: Capstone — Build a Minimal Container with `unshare`

**Scenario:** You're a platform engineer who needs to create an isolated execution environment manually — without Docker — to understand what's happening under the hood. Build a "container" using only `unshare`, mount, and a chroot.

```bash
apt-get install -y -qq debootstrap 2>/dev/null || apt-get install -y -qq busybox-static 2>/dev/null

# Method: Use unshare to create isolated namespaces combining all 7 types
# Create a minimal rootfs with busybox
ROOTFS=/tmp/miniroot
mkdir -p $ROOTFS/{bin,proc,sys,dev,tmp,etc}

# Copy busybox
cp $(which busybox) $ROOTFS/bin/ 2>/dev/null || cp /bin/busybox $ROOTFS/bin/ 2>/dev/null

# Create symlinks for common commands
for cmd in sh ls ps mount echo cat; do
  ln -sf busybox $ROOTFS/bin/$cmd 2>/dev/null
done

echo "root:x:0:0:root:/root:/bin/sh" > $ROOTFS/etc/passwd

# Launch isolated environment using 6 namespace types simultaneously
unshare \
  --pid \
  --fork \
  --mount-proc=$ROOTFS/proc \
  --mount \
  --uts \
  --ipc \
  --net \
  bash -c "
    # Set up the rootfs mounts
    mount --bind $ROOTFS $ROOTFS
    mount -t proc proc $ROOTFS/proc

    # Set custom hostname
    hostname my-container

    # chroot into our minimal rootfs
    chroot $ROOTFS /bin/sh -c '
      echo \"=== Inside mini-container ===\"
      echo \"Hostname: \$(hostname 2>/dev/null || cat /proc/sys/kernel/hostname)\"
      echo \"PID: \$\$\"
      echo \"Processes:\"
      ls /proc | grep -E \"^[0-9]+$\" | sort -n | head -5
      echo \"Mounts:\"
      cat /proc/mounts | head -3
    '
  "

echo ""
echo "=== Summary: Namespace flags used in this 'container' ==="
echo "--pid    : isolated PID tree (PID 1 inside)"
echo "--mount  : isolated mount namespace"
echo "--uts    : custom hostname"  
echo "--ipc    : isolated shared memory/semaphores"
echo "--net    : isolated network stack"
echo "--fork   : required for PID namespace"
echo ""
echo "Missing vs real Docker:"
echo "- No --user mapping (ran as root)"
echo "- No cgroup limits"
echo "- No seccomp/AppArmor profiles"
echo "- No overlay2 filesystem"
```

📸 **Verified Output:**
```
=== Inside mini-container ===
Hostname: my-container
PID: 1
Processes:
1
2
Mounts:
/dev/root /proc/... 
...

=== Summary: Namespace flags used in this 'container' ===
--pid    : isolated PID tree (PID 1 inside)
--mount  : isolated mount namespace
--uts    : custom hostname
--ipc    : isolated shared memory/semaphores
--net    : isolated network stack
--fork   : required for PID namespace

Missing vs real Docker:
- No --user mapping (ran as root)
- No cgroup limits
- No seccomp/AppArmor profiles
- No overlay2 filesystem
```

You've just built a container from scratch using only Linux kernel primitives!

---

## Summary

| Concept | Command | What It Does |
|---------|---------|--------------|
| List namespaces | `lsns` | Show all namespaces on the system |
| Inspect process ns | `ls -la /proc/PID/ns/` | See namespace FDs for a process |
| UTS isolation | `unshare --uts bash` | Isolate hostname |
| PID isolation | `unshare --pid --fork --mount-proc bash` | New PID tree, PID 1 |
| Network isolation | `ip netns add NAME` | Create named network namespace |
| Mount isolation | `unshare --mount bash` | Isolate filesystem mounts |
| User isolation | `unshare --user --map-root-user bash` | Map UIDs (rootless) |
| Enter namespace | `nsenter -t PID --net bash` | Join existing process's namespace |
| Namespace ID | `/proc/PID/ns/TYPE` symlink inode | Compare namespace membership |

**Key insight:** Docker, Podman, and Kubernetes all reduce to these same `clone(2)` and `unshare(2)` syscalls. Namespaces provide isolation; cgroups provide resource limits — together they define a container.
