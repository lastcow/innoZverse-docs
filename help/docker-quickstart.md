# Docker Quick Start for Labs

## What You Need

- Docker installed and running
- A lab image name (e.g., `zchencow/innozverse-linux`, `zchencow/innozverse-ai`)

## Pull a Lab Image

```bash
docker pull zchencow/innozverse-{DOMAIN}:latest
```

**Examples:**

```bash
# Linux labs
docker pull zchencow/innozverse-linux:latest

# AI & ML labs
docker pull zchencow/innozverse-ai:latest

# Cybersecurity labs
docker pull zchencow/innozverse-cybersec:latest

# Networking labs
docker pull zchencow/innozverse-networking:latest
```

## Run a Lab Interactively

```bash
docker run -it --rm zchencow/innozverse-{DOMAIN}:latest bash
```

You're now inside the lab environment. Run commands, scripts, and experiments.

## Run with Volume Mount (Persist Files)

To keep files after exiting:

```bash
docker run -it --rm -v $(pwd):/work zchencow/innozverse-{DOMAIN}:latest bash
```

Your current directory is mounted to `/work` inside the container.

## Run a Specific Lab

```bash
docker run -it --rm zchencow/innozverse-{DOMAIN}:latest \
  bash /labs/foundations/lab-01/setup.sh
```

## Check Available Images

```bash
docker images | grep innozverse
```

## Stop a Running Container

Press `Ctrl+D` or type `exit` to exit the bash shell.

## Troubleshooting Docker

See [Troubleshooting Guide](troubleshooting.md#docker-image-not-found)

## Next Steps

- [Run Your First Lab](README.md#3-run-your-first-lab-with-openclaw)
- [Troubleshooting](troubleshooting.md)
- [Domain Guides](../README.md)
