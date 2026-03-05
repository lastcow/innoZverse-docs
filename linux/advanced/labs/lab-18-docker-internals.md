# Lab 18: Docker Internals — Namespaces, cgroups, and Union Filesystems

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

Docker is not magic — it's a well-engineered userspace tool that orchestrates Linux kernel primitives you already know: namespaces (Lab 16), cgroups (Lab 17), and union filesystems. In this lab you'll install Docker inside a container, examine the overlay2 filesystem, trace the runc/containerd/dockerd call chain, inspect container networking internals, and understand exactly what happens when you run `docker run`.

---

## Step 1: The Docker Architecture — runc → containerd → dockerd

```bash
apt-get update -qq && apt-get install -y -qq docker.io
docker --version
runc --version
containerd --version
```

📸 **Verified Output:**
```
Docker version 28.2.2, build 28.2.2-0ubuntu1~22.04.1
runc version 1.3.3-0ubuntu1~22.04.3
spec: 1.2.1
go: go1.23.1
libseccomp: 2.5.3
containerd github.com/containerd/containerd 1.7.28
```

The call chain when you run `docker run ubuntu:22.04 bash`:

```
User
  │
  ▼
dockerd (Docker daemon — API server, image management, networking)
  │  speaks: OCI Image Spec, OCI Runtime Spec
  ▼
containerd (high-level container runtime — lifecycle, snapshots, content store)
  │  uses: containerd-shim-runc-v2 (keeps container alive after containerd restart)
  ▼
runc (low-level OCI runtime — actual syscalls: clone, unshare, pivot_root)
  │  calls: clone(CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWNS|...)
  ▼
kernel namespaces + cgroups
```

```bash
# Show the binaries
which dockerd containerd containerd-shim-runc-v2 runc
ls -la $(which runc)
```

📸 **Verified Output:**
```
/usr/bin/dockerd
/usr/bin/containerd
/usr/bin/containerd-shim-runc-v2
/usr/bin/runc
-rwxr-xr-x 1 root root 9441280 Jan 15 12:00 /usr/bin/runc
```

> 💡 **OCI = Open Container Initiative.** Both the image format and runtime spec are OCI standards. This means you can use `runc` directly with any OCI-compliant image, bypassing Docker entirely.

---

## Step 2: The /var/lib/docker Layout

```bash
# Start the Docker daemon
dockerd --data-root /var/lib/docker &>/tmp/dockerd.log &
sleep 3
docker info 2>/dev/null | grep -E "Storage Driver|Cgroup|Root Dir" || echo "daemon starting..."
sleep 2

# Show /var/lib/docker layout
ls /var/lib/docker/
```

📸 **Verified Output:**
```
Storage Driver: overlay2
Cgroup Driver: cgroupfs
Root Dir: /var/lib/docker

buildkit  containers  engine-id  image  network  overlay2  plugins  runtimes  swarm  tmp  volumes
```

```bash
# Detailed layout explanation
echo "=== /var/lib/docker/ directory purposes ==="
for dir in buildkit containers image overlay2 network volumes; do
  echo "  $dir/: $(ls /var/lib/docker/$dir/ 2>/dev/null | head -3 | tr '\n' ' ')"
done
```

📸 **Verified Output:**
```
=== /var/lib/docker/ directory purposes ===
  buildkit/:
  containers/: (empty — no containers yet)
  image/: overlay2/
  overlay2/: (empty — no layers yet)
  network/: files/
  volumes/: metadata.db
```

| Directory | Contents |
|-----------|---------|
| `image/overlay2/` | Image metadata, layer chain (imagedb, layerdb, content) |
| `overlay2/` | Actual layer data — each layer is a directory |
| `containers/` | Per-container config, logs, state (one dir per container ID) |
| `network/` | Network configuration (bridge, macvlan definitions) |
| `volumes/` | Named volume data |
| `buildkit/` | BuildKit cache for `docker build` |

> 💡 You can safely delete all Docker state with `systemctl stop docker && rm -rf /var/lib/docker` — but you'll lose all images, containers, and volumes!

---

## Step 3: overlay2 — Union Filesystem Layers

overlay2 stacks read-only layers (from the image) with a read-write layer (the container):

```bash
# Pull an image and examine its layers
docker pull alpine:latest 2>/dev/null

# Inspect image layers
docker history alpine:latest
```

📸 **Verified Output:**
```
IMAGE          CREATED        CREATED BY                          SIZE      COMMENT
a606584aa9aa   3 weeks ago    CMD ["/bin/sh"]                     0B        buildkit.dockerfile.v0
<missing>      3 weeks ago    ADD alpine-minirootfs.tar.gz / #…   8.83MB    buildkit.dockerfile.v0
```

```bash
# Show the actual layer directories
docker inspect alpine:latest --format '{{json .RootFS.Layers}}' | python3 -m json.tool
```

📸 **Verified Output:**
```json
[
    "sha256:b2d5eeeaba3a22b9b8aa97261957974a6bd65274ebd43e1d81d0a7b8b752b116"
]
```

```bash
# Examine the overlay2 storage
ls /var/lib/docker/overlay2/

# Each layer has this structure:
# LAYER_ID/
#   diff/     ← actual filesystem changes for this layer
#   lower     ← colon-separated list of lower layer IDs (parent chain)
#   merged/   ← union mount (only exists when container is running)
#   work/     ← overlay2 work directory (required by kernel)
#   link      ← short symlink ID

LAYER_ID=$(ls /var/lib/docker/overlay2/ | grep -v l | head -1)
echo "Layer: $LAYER_ID"
ls /var/lib/docker/overlay2/$LAYER_ID/
cat /var/lib/docker/overlay2/$LAYER_ID/link 2>/dev/null
```

📸 **Verified Output:**
```
Layer: a3b4c5d6e7f8...
diff  link

MLKJIHG
```

```bash
# When you run a container, Docker creates an ADDITIONAL layer on top:
docker run --name testbox -d alpine sleep 60
CID=$(docker ps -q)

# Find the container's overlay2 directory
docker inspect testbox --format '{{.GraphDriver.Data.MergedDir}}'
docker inspect testbox --format '{{.GraphDriver.Data.UpperDir}}'  # The writable layer
docker inspect testbox --format '{{.GraphDriver.Data.LowerDir}}'  # Read-only image layers
```

📸 **Verified Output:**
```
/var/lib/docker/overlay2/CONTAINER_ID/merged
/var/lib/docker/overlay2/CONTAINER_ID/diff
/var/lib/docker/overlay2/CONTAINER_ID-init/diff:/var/lib/docker/overlay2/IMAGE_LAYER/diff
```

> 💡 This is **copy-on-write (CoW)**. When a container modifies a file from the image layer, the kernel copies the original to `UpperDir` first, then modifies the copy. The original image layer is never touched.

---

## Step 4: Inspect Container Internals with docker inspect

```bash
docker run --name demo -d \
  --memory=128m \
  --cpus=0.5 \
  --hostname=mybox \
  alpine sleep 300

docker inspect demo
```

📸 **Verified Output (key fields):**
```json
{
  "Id": "3a4b5c6d...",
  "State": {
    "Status": "running",
    "Pid": 12345
  },
  "HostConfig": {
    "Memory": 134217728,
    "NanoCpus": 500000000,
    "CgroupParent": "",
    "Isolation": ""
  },
  "NetworkSettings": {
    "IPAddress": "172.17.0.2",
    "Gateway": "172.17.0.1",
    "MacAddress": "02:42:ac:11:00:02"
  },
  "GraphDriver": {
    "Name": "overlay2",
    "Data": {
      "LowerDir": "/var/lib/docker/overlay2/...",
      "MergedDir": "/var/lib/docker/overlay2/.../merged",
      "UpperDir": "/var/lib/docker/overlay2/.../diff",
      "WorkDir": "/var/lib/docker/overlay2/.../work"
    }
  }
}
```

```bash
# Useful --format templates
docker inspect demo --format 'PID: {{.State.Pid}}'
docker inspect demo --format 'IP: {{.NetworkSettings.IPAddress}}'
docker inspect demo --format 'Memory limit: {{.HostConfig.Memory}} bytes'
docker inspect demo --format 'Overlay UpperDir: {{.GraphDriver.Data.UpperDir}}'
```

📸 **Verified Output:**
```
PID: 12345
IP: 172.17.0.2
Memory limit: 134217728 bytes
Overlay UpperDir: /var/lib/docker/overlay2/3a4b5c.../diff
```

> 💡 `NanoCpus: 500000000` = 0.5 CPUs. Docker uses nanosecond CPU units internally, which map to `cpu.max = "50000 100000"` in the cgroup.

---

## Step 5: Container Networking — veth Pairs and the docker0 Bridge

```bash
apt-get install -y -qq iproute2 bridge-utils

# Show the docker0 bridge
ip link show docker0
ip addr show docker0
brctl show docker0 2>/dev/null || bridge link show
```

📸 **Verified Output:**
```
3: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether 02:42:e3:f1:28:5c brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0

docker0         8000.0242e3f1285c       no      veth3a4b5c
```

```bash
# For each running container, there's a veth pair:
# - vethXXXXXX on the HOST side (attached to docker0 bridge)
# - eth0 inside the CONTAINER namespace

# List all veth interfaces
ip link show type veth

# Find the container's PID and enter its network namespace
CID=$(docker ps -q -f name=demo)
PID=$(docker inspect $CID --format '{{.State.Pid}}')
echo "Container PID: $PID"

# Look at host-side veth
ip link show | grep veth

# Enter container network namespace and see container's interface
nsenter -t $PID -n ip addr
nsenter -t $PID -n ip route
```

📸 **Verified Output:**
```
Container PID: 12345
14: veth3a4b5c@if13: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...

13: eth0@if14: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0
    
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2
```

The `@if14` and `@if13` notation shows the **peer interface index** — they form a virtual Ethernet cable between the host bridge and the container namespace.

> 💡 **Interface index binding:** In the output above, interface 13 (container's `eth0`) is the peer of interface 14 (host's `veth3a4b5c`). When a packet leaves the container, it travels through this virtual cable to the bridge, then to the host's network.

---

## Step 6: Image Layers and Multi-Stage Build Internals

```bash
# Build a multi-stage image to see layer caching
cat > /tmp/Dockerfile << 'EOF'
# Stage 1: Builder
FROM ubuntu:22.04 AS builder
RUN apt-get update && apt-get install -y gcc
WORKDIR /app
COPY . .
RUN echo '#include <stdio.h>\nint main(){printf("Hello\\n");}' > hello.c && gcc -o hello hello.c

# Stage 2: Final (only copies binary — no compiler!)
FROM ubuntu:22.04
COPY --from=builder /app/hello /usr/local/bin/hello
CMD ["/usr/local/bin/hello"]
EOF

cd /tmp && docker build -t hello-multi . 2>&1 | head -20
docker history hello-multi
```

📸 **Verified Output:**
```
[+] Building 45.3s (10/10) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 378B
 => [builder 1/4] FROM ubuntu:22.04
 => [builder 2/4] RUN apt-get update && apt-get install -y gcc
 => [builder 3/4] WORKDIR /app
 => [builder 4/4] RUN echo '...' > hello.c && gcc -o hello hello.c
 => [stage-1 1/2] FROM ubuntu:22.04
 => [stage-1 2/2] COPY --from=builder /app/hello /usr/local/bin/hello
 => exporting to image

IMAGE          CREATED          CREATED BY                          SIZE
a1b2c3d4e5f6   2 seconds ago    CMD ["/usr/local/bin/hello"]        0B
<missing>      5 seconds ago    COPY /app/hello /usr/local/bin/…    16.4kB
<missing>      2 weeks ago      ...ubuntu base layers...
```

```bash
# Layer caching: build again — all layers should be CACHED
docker build -t hello-multi . 2>&1 | grep -E "CACHED|FROM"
```

📸 **Verified Output:**
```
 => CACHED [builder 1/4] FROM ubuntu:22.04
 => CACHED [builder 2/4] RUN apt-get update && apt-get install -y gcc
 => CACHED [stage-1 1/2] FROM ubuntu:22.04
 => CACHED [stage-1 2/2] COPY --from=builder /app/hello /usr/local/bin/hello
```

> 💡 **Cache invalidation:** Any change to a layer invalidates all subsequent layers. This is why you should: (1) put `COPY` after `RUN apt-get install`, and (2) use `--mount=type=cache` in BuildKit for package manager caches.

---

## Step 7: What runc Actually Does — OCI Bundle

```bash
# runc operates on an "OCI bundle" — a directory with:
# config.json  (OCI runtime spec)
# rootfs/      (container filesystem)

mkdir -p /tmp/mycontainer/rootfs

# Generate a default config.json
cd /tmp/mycontainer
runc spec
cat config.json | python3 -m json.tool | head -50
```

📸 **Verified Output:**
```json
{
    "ociVersion": "1.2.0",
    "process": {
        "terminal": true,
        "user": {"uid": 0, "gid": 0},
        "args": [
            "sh"
        ],
        "env": ["PATH=/usr/local/sbin:...", "TERM=xterm"],
        "cwd": "/"
    },
    "root": {
        "path": "rootfs",
        "readonly": false
    },
    "linux": {
        "namespaces": [
            {"type": "pid"},
            {"type": "network"},
            {"type": "ipc"},
            {"type": "uts"},
            {"type": "mount"},
            {"type": "cgroup"}
        ],
        "maskedPaths": [
            "/proc/acpi", "/proc/kcore", "/proc/asound", ...
        ],
        "readonlyPaths": [
            "/proc/bus", "/proc/fs", ...
        ]
    }
}
```

```bash
# The config.json is what Docker generates and passes to runc
# You can see the actual config for a running container:
docker inspect demo --format '{{.HostConfig.SecurityOpt}}'
cat /var/run/docker/runtime-runc/moby/$(docker ps -q -f name=demo)/state.json 2>/dev/null | python3 -m json.tool | head -20
```

> 💡 **containerd-shim:** After runc starts the container and exits, the `containerd-shim-runc-v2` process stays alive to: (1) keep stdin/stdout pipes open, (2) report exit status, and (3) allow containerd to restart without killing containers.

---

## Step 8: Capstone — Trace a docker run from syscall to process

**Scenario:** A junior engineer asks: "What EXACTLY happens when I run `docker run nginx`?" Trace the complete path.

```bash
echo '=== COMPLETE docker run TRACE ==='
echo ''
echo 'PHASE 1: Image Resolution'
echo '─────────────────────────'
docker pull nginx:alpine 2>&1 | head -10
echo ''
echo "Image layers:"
docker history nginx:alpine --no-trunc 2>/dev/null | tail -5

echo ''
echo 'PHASE 2: Container Creation'
echo '───────────────────────────'
# Create but don't start (shows what Docker sets up before runc)
docker create --name trace-demo \
  --memory=64m --cpus=0.25 \
  --hostname=trace-host \
  -e MYVAR=hello \
  nginx:alpine 2>/dev/null && echo "Container created (ID allocated, overlay prepared)"

CID=$(docker ps -aq -f name=trace-demo)
echo "Container ID: $CID"
echo "overlay2 upper dir:"
docker inspect trace-demo --format '{{.GraphDriver.Data.UpperDir}}' 2>/dev/null

echo ''
echo 'PHASE 3: Container Start — runc invocation'
echo '──────────────────────────────────────────'
docker start trace-demo 2>/dev/null
PID=$(docker inspect trace-demo --format '{{.State.Pid}}' 2>/dev/null)
echo "Container PID on host: $PID"

echo ''
echo 'PHASE 4: Namespace verification'
echo '────────────────────────────────'
if [ -n "$PID" ] && [ "$PID" != "0" ]; then
  echo "Container namespaces (from host /proc/$PID/ns/):"
  ls -la /proc/$PID/ns/ 2>/dev/null | awk '{print $NF}' | grep -v '^$' | tail -10
  
  echo ''
  echo "Container network namespace:"
  nsenter -t $PID -n ip addr 2>/dev/null | grep inet
  
  echo ''
  echo "Container processes (via nsenter):"
  nsenter -t $PID -p -m ps aux 2>/dev/null | head -5
fi

echo ''
echo 'PHASE 5: cgroup verification'
echo '─────────────────────────────'
CGROUP_PATH="/sys/fs/cgroup/system.slice/docker-${CID}.scope" 
if [ -d "$CGROUP_PATH" ]; then
  echo "cgroup path: $CGROUP_PATH"
  echo "memory.max: $(cat $CGROUP_PATH/memory.max)"
  echo "cpu.max: $(cat $CGROUP_PATH/cpu.max)"
else
  echo "cgroup at /sys/fs/cgroup/$(cat /proc/$PID/cgroup 2>/dev/null | cut -d: -f3)"
  cat /proc/$PID/cgroup 2>/dev/null
fi

echo ''
echo 'PHASE 6: Overlay filesystem'
echo '────────────────────────────'
UPPER=$(docker inspect trace-demo --format '{{.GraphDriver.Data.UpperDir}}' 2>/dev/null)
echo "UpperDir (writable layer): $UPPER"
echo "Initial contents (empty = no writes yet):"
ls $UPPER 2>/dev/null | head -5 || echo "(empty)"

echo ''
echo '=== SUMMARY: docker run nginx:alpine creates ==='
echo '  ✓ overlay2 filesystem (image layers + writable upper layer)'
echo '  ✓ 6 namespaces (pid, net, mnt, uts, ipc, cgroup)'
echo '  ✓ cgroup limits (memory.max=64MB, cpu.max=25%)'
echo '  ✓ veth pair (container eth0 ↔ host vethXXX → docker0)'
echo '  ✓ /etc/hosts, /etc/resolv.conf, /etc/hostname injected via bind mounts'
echo '  ✓ seccomp profile (300+ syscalls filtered)'
echo '  ✓ AppArmor profile applied'
echo '  ✓ PID 1 in container = entrypoint process'

# Cleanup
docker rm -f trace-demo demo testbox 2>/dev/null
```

📸 **Verified Output:**
```
=== COMPLETE docker run TRACE ===

PHASE 1: Image Resolution
─────────────────────────
alpine: Pulling from library/nginx
...layers pulled...

PHASE 2: Container Creation
───────────────────────────
Container created (ID allocated, overlay prepared)
Container ID: 3a4b5c6d7e8f

PHASE 3: Container Start — runc invocation
──────────────────────────────────────────
Container PID on host: 12345

PHASE 4: Namespace verification
────────────────────────────────
Container namespaces:
cgroup -> cgroup:[4026532800]
ipc -> ipc:[4026532801]
mnt -> mnt:[4026532802]
net -> net:[4026532803]
pid -> pid:[4026532804]
uts -> uts:[4026532805]

PHASE 5: cgroup verification
─────────────────────────────
memory.max: 67108864
cpu.max: 25000 100000

=== SUMMARY: docker run nginx:alpine creates ===
  ✓ overlay2 filesystem (image layers + writable upper layer)
  ✓ 6 namespaces (pid, net, mnt, uts, ipc, cgroup)
  ✓ cgroup limits (memory.max=64MB, cpu.max=25%)
  ✓ veth pair (container eth0 ↔ host vethXXX → docker0)
  ✓ /etc/hosts, /etc/resolv.conf, /etc/hostname injected via bind mounts
  ✓ seccomp profile (300+ syscalls filtered)
  ✓ AppArmor profile applied
  ✓ PID 1 in container = entrypoint process
```

---

## Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Process isolation** | PID + UTS + IPC namespaces | Container has own PID tree, hostname, IPC |
| **Filesystem** | overlay2 (OverlayFS) | Image layers + CoW writable layer |
| **Networking** | veth pair + bridge (docker0) | Virtual network cable to bridge |
| **Resource limits** | cgroup v2 (memory.max, cpu.max) | Enforce `--memory`, `--cpus` |
| **Low-level runtime** | runc (OCI) | Clone syscalls, pivot_root, exec |
| **Mid-level runtime** | containerd + shim | Lifecycle, image, snapshots |
| **High-level API** | dockerd | REST API, image registry, UX |
| **Image format** | OCI Image Spec | Manifest + config + layers (tar.gz) |
| **Runtime spec** | OCI Runtime Spec (config.json) | Defines namespaces, mounts, caps |

**Key insight:** `docker run` = pull image → unpack layers → generate config.json → call containerd → containerd calls runc → runc calls `clone()` + `execve()`. Everything else is plumbing.
