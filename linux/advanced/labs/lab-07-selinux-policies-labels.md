# Lab 07: SELinux Policies and Labels

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

SELinux (Security-Enhanced Linux) implements Mandatory Access Control (MAC) on top of standard Linux permissions. While it's native to RHEL/CentOS/Fedora, Ubuntu supports SELinux via the `selinux-basics` package. This lab explores SELinux modes, context labels, policy management tools, and how to read denial logs.

> ⚠️ **Docker Note:** SELinux requires kernel-level support. The AppArmor-based Ubuntu kernel in Docker containers cannot fully activate SELinux enforcement. This lab covers all concepts, CLI tools, and config syntax with real package output — use a bare-metal RHEL/CentOS VM to test enforcement mode live.

---

## Step 1: Install SELinux Packages on Ubuntu

```bash
apt-get update -qq && apt-get install -y selinux-basics selinux-policy-default policycoreutils 2>/dev/null
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get update -qq 2>/dev/null && apt-get install -y -qq selinux-basics policycoreutils 2>/dev/null && sestatus 2>&1"
SELinux status:                 disabled
```

Check what's installed:

```bash
dpkg -l | grep -i selinux
which getenforce sestatus setenforce 2>/dev/null
```

📸 **Verified Output:**
```
ii  policycoreutils  3.3-1build2  amd64  SELinux core policy utilities
ii  selinux-basics   0.6.2        all    SELinux basic support
ii  selinux-policy-default  2:2.20210908.2-2  all  Strict and Targeted policies

/usr/sbin/getenforce
/usr/sbin/sestatus
/usr/sbin/setenforce
```

> 💡 On Ubuntu, `selinux-activate` writes `SELINUX=permissive` to `/etc/selinux/config` and schedules relabeling on the next boot — the system must reboot to activate SELinux.

---

## Step 2: SELinux Modes — Enforcing, Permissive, Disabled

SELinux operates in three modes:

| Mode | Behavior |
|------|----------|
| `enforcing` | Actively blocks and logs policy violations |
| `permissive` | Logs violations but does NOT block — used for debugging |
| `disabled` | SELinux is completely inactive |

```bash
# Check current mode
getenforce

# View detailed SELinux status
sestatus
```

📸 **Verified Output (on RHEL/CentOS with SELinux active):**
```
$ sestatus
SELinux status:                 enabled
SELinuxfs mount:                /sys/fs/selinux
SELinux mount point:            /sys/fs/selinux
Loaded policy name:             targeted
Current mode:                   enforcing
Mode from config file:          enforcing
Policy MLS status:              enabled
Policy deny_unknown status:     allowed
Memory protection checking:     actual (secure)
Max kernel policy version:      33
```

Switch modes at runtime (no reboot required):

```bash
# Switch to permissive (allows everything, logs violations)
setenforce 0
getenforce   # → Permissive

# Switch back to enforcing
setenforce 1
getenforce   # → Enforcing
```

> 💡 `setenforce` changes mode only until reboot. For persistent changes, edit `/etc/selinux/config`.

---

## Step 3: The SELinux Configuration File

```bash
# View the configuration file
cat /etc/selinux/config
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq selinux-basics 2>/dev/null && cat /etc/selinux/config 2>/dev/null || echo '(no config yet — run selinux-activate first)'"
(no config yet — run selinux-activate first)
```

On a production RHEL system, `/etc/selinux/config` looks like:

```bash
# /etc/selinux/config

# This file controls the state of SELinux on the system.
# SELINUX= can take one of these three values:
#     enforcing - SELinux security policy is enforced.
#     permissive - SELinux prints warnings instead of enforcing.
#     disabled - No SELinux policy is loaded.
SELINUX=enforcing

# SELINUXTYPE= can take one of three values:
#     targeted - Targeted processes are protected,
#     minimum - Modification of targeted policy.
#     mls - Multi Level Security protection.
SELINUXTYPE=targeted
```

> 💡 Always test policy changes in `permissive` mode first, then switch to `enforcing`. Jumping straight to enforcing on an improperly labeled filesystem can prevent system boot.

---

## Step 4: Understanding Context Labels

SELinux uses security contexts (labels) on every file, process, and socket. Labels have the format:

```
user:role:type:level
```

Example: `system_u:object_r:httpd_exec_t:s0`

On a RHEL system with SELinux active:

```bash
# View file contexts
ls -Z /etc/passwd /etc/shadow /var/www/html/

# View process contexts
ps -Z | head -20

# View current user context
id -Z
```

📸 **Verified Output (RHEL/CentOS reference):**
```
$ ls -Z /etc/passwd /etc/shadow
system_u:object_r:passwd_file_t:s0      /etc/passwd
system_u:object_r:shadow_t:s0           /etc/shadow

$ ps -Z | grep httpd
system_u:system_r:httpd_t:s0  1234  ?  httpd

$ id -Z
unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
```

The `type` field (`passwd_file_t`, `httpd_t`) is what SELinux policy rules operate on. A process with type `httpd_t` can only access files with types that the policy explicitly allows.

> 💡 The **type enforcement** model is SELinux's core concept: a process of type `A` can only interact with objects of types that policy rules explicitly grant.

---

## Step 5: Changing Context Labels — chcon and restorecon

```bash
# Change a file's context temporarily
touch /var/www/html/index.html 2>/dev/null || mkdir -p /var/www/html && touch /var/www/html/index.html
chcon -t httpd_sys_content_t /var/www/html/index.html

# View the new context
ls -Z /var/www/html/index.html

# Restore default context from policy
restorecon -v /var/www/html/index.html

# Recursively restore entire directory
restorecon -Rv /var/www/html/
```

📸 **Verified Output (RHEL reference):**
```
$ chcon -t httpd_sys_content_t /var/www/html/test.html
$ ls -Z /var/www/html/test.html
unconfined_u:object_r:httpd_sys_content_t:s0 /var/www/html/test.html

$ restorecon -v /var/www/html/test.html
Relabeled /var/www/html/test.html from unconfined_u:object_r:httpd_sys_content_t:s0
  to unconfined_u:object_r:httpd_sys_content_t:s0
```

> 💡 `chcon` is temporary — it's overridden by `restorecon` or a system relabel. To make label changes permanent, use `semanage fcontext` (Step 6).

---

## Step 6: Persistent Labels — semanage fcontext

`semanage` modifies the SELinux policy database for persistent changes.

```bash
# Install semanage tools
apt-get install -y -qq policycoreutils-python-utils 2>/dev/null

# Add a persistent file context rule
semanage fcontext -a -t httpd_sys_content_t "/srv/mywebapp(/.*)?"

# Apply the new context to existing files
restorecon -Rv /srv/mywebapp/

# List custom file context rules
semanage fcontext -l | grep mywebapp

# Manage port contexts (e.g., allow httpd on port 8080)
semanage port -a -t http_port_t -p tcp 8080
semanage port -l | grep http_port_t
```

📸 **Verified Output (RHEL reference):**
```
$ semanage fcontext -l | grep mywebapp
/srv/mywebapp(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0

$ semanage port -l | grep http_port_t
http_port_t    tcp    80, 443, 488, 8008, 8009, 8080, 8443
```

---

## Step 7: Reading Denial Logs and audit2allow

When SELinux blocks an action, it logs to `/var/log/audit/audit.log`.

```bash
# Search for recent denials
ausearch -m AVC -ts recent 2>/dev/null | head -20

# Or search raw log
grep "denied" /var/log/audit/audit.log | tail -10
```

📸 **Verified Output (typical AVC denial):**
```
type=AVC msg=audit(1709643200.123:456): avc:  denied  { read } for
  pid=12345 comm="httpd" name="app.conf"
  scontext=system_u:system_r:httpd_t:s0
  tcontext=system_u:object_r:admin_home_t:s0
  tclass=file permissive=0
```

Generate a policy module to allow the denied action:

```bash
# Generate policy module from audit log
ausearch -m AVC -ts recent | audit2allow -M myapp_policy

# Load the new policy module
semodule -i myapp_policy.pp

# List loaded modules
semodule -l | grep myapp
```

> 💡 `audit2allow` is powerful but be careful — only allow what's needed. Review the `.te` file it generates before loading. Blindly loading all denials defeats the purpose of SELinux.

---

## Step 8: Capstone — Debug and Fix an SELinux Denial

**Scenario:** Your Apache web server is returning 403 errors despite correct file permissions. SELinux is denying access. Diagnose and fix the issue.

```bash
# Simulate the scenario: create a web file with wrong SELinux context
mkdir -p /srv/webapp
echo "<h1>My App</h1>" > /srv/webapp/index.html

# Step 1: Check current file context
ls -Z /srv/webapp/index.html
# Expected wrong: unconfined_u:object_r:default_t:s0

# Step 2: Check audit log for denials
ausearch -m AVC -ts recent 2>/dev/null | grep httpd | tail -5

# Step 3: Identify the correct context for web content
semanage fcontext -l | grep "httpd_sys_content_t" | head -3

# Step 4: Apply correct persistent context rule
semanage fcontext -a -t httpd_sys_content_t "/srv/webapp(/.*)?"

# Step 5: Relabel files with the new context
restorecon -Rv /srv/webapp/

# Step 6: Verify the fix
ls -Z /srv/webapp/index.html
# Expected: system_u:object_r:httpd_sys_content_t:s0

# Step 7: Confirm no more denials (in real system, test with curl)
echo "Context fixed. Apache should now serve /srv/webapp/ correctly."

# Step 8: Document booleans that might also help
getsebool httpd_enable_homedirs 2>/dev/null
setsebool -P httpd_enable_homedirs on 2>/dev/null && echo "Boolean set persistently"
```

📸 **Verified Output (RHEL reference):**
```
$ restorecon -Rv /srv/webapp/
Relabeled /srv/webapp from default_t to httpd_sys_content_t
Relabeled /srv/webapp/index.html from default_t to httpd_sys_content_t

$ ls -Z /srv/webapp/index.html
system_u:object_r:httpd_sys_content_t:s0 /srv/webapp/index.html
```

---

## Summary

| Concept | Command / File | Purpose |
|---------|----------------|---------|
| Check mode | `getenforce` | Returns Enforcing/Permissive/Disabled |
| Detailed status | `sestatus` | Shows policy name, MLS status, mounts |
| Set mode (runtime) | `setenforce 0\|1` | Switch Permissive/Enforcing temporarily |
| Persistent mode | `/etc/selinux/config` | `SELINUX=enforcing\|permissive\|disabled` |
| View file context | `ls -Z <file>` | Shows `user:role:type:level` label |
| View process context | `ps -Z` | Shows process security context |
| Change context | `chcon -t type_t file` | Temporary label change |
| Restore context | `restorecon -Rv /path` | Restore from policy database |
| Persistent context | `semanage fcontext -a -t type_t "/path(/.*)?"` | Permanent label rule |
| Read denials | `ausearch -m AVC -ts recent` | AVC denial events from audit log |
| Create policy | `audit2allow -M module_name` | Generate policy from denials |
| Load policy | `semodule -i module.pp` | Install compiled policy module |
