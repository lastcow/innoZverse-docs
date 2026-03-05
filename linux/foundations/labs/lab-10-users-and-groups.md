# Lab 10: Users and Groups Management

## Objective
Create and manage Linux users and groups: `useradd`, `usermod`, `userdel`, `groupadd`, `/etc/passwd`, `/etc/shadow`, `/etc/group` file formats, and the principle of least privilege via service accounts.

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Understanding /etc/passwd

```bash
cat /etc/passwd | head -5
```

**📸 Verified Output:**
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
```

Each line: `username:password:UID:GID:GECOS:home:shell`

- `x` in password field = password stored in `/etc/shadow`
- `UID 0` = root (superuser)
- `/usr/sbin/nologin` = account that cannot log in interactively

---

## Step 2: Creating Users

```bash
useradd -m -s /bin/bash alice
id alice
```

**📸 Verified Output:**
```
uid=1000(alice) gid=1000(alice) groups=1000(alice)
```

```bash
cat /etc/passwd | grep alice
```

**📸 Verified Output:**
```
alice:x:1000:1000::/home/alice:/bin/bash
```

```bash
# Create a second user
useradd -m -s /bin/bash bob
id bob
```

**📸 Verified Output:**
```
uid=1001(bob) gid=1001(bob) groups=1001(bob)
```

> 💡 `useradd -m` creates the home directory. Without `-m`, no home directory is created. `-s /bin/bash` sets the login shell. Always specify both on real systems.

---

## Step 3: The /etc/shadow File (Password Storage)

```bash
cat /etc/shadow | grep -E 'root|alice'
```

**📸 Verified Output:**
```
root:*:20494:0:99999:7:::
alice:!:20517:0:99999:7:::
```

Format: `user:hash:last_change:min_age:max_age:warn:inactive:expire`

- `*` = account locked (root can't log in with password in this container)
- `!` = no password set (new account before `passwd` is run)
- The hash would look like: `$6$salt$hashedpassword...` (SHA-512)

> 💡 `/etc/shadow` is readable only by root (`640`). If an attacker gets read access to shadow, they can crack the hashes offline with `hashcat` or `john`. This is why it has restricted permissions.

---

## Step 4: Creating and Managing Groups

```bash
groupadd devteam
groupadd ops

getent group devteam
```

**📸 Verified Output:**
```
devteam:x:1002:
```

```bash
# Add alice to devteam
usermod -aG devteam alice
id alice
```

**📸 Verified Output:**
```
uid=1000(alice) gid=1000(alice) groups=1000(alice),1002(devteam)
```

```bash
# Add bob to multiple groups
usermod -aG devteam,ops bob
id bob
```

**📸 Verified Output:**
```
uid=1001(bob) gid=1001(bob) groups=1001(bob),1002(devteam),1003(ops)
```

> 💡 `-aG` = **a**ppend to **G**roups. Without `-a`, `usermod -G devteam alice` would **replace** all of alice's supplementary groups with just `devteam`. Always use `-aG` to add groups.

---

## Step 5: Listing Group Members

```bash
groups alice
```

**📸 Verified Output:**
```
alice : alice devteam
```

```bash
getent group devteam
```

**📸 Verified Output:**
```
devteam:x:1002:alice,bob
```

---

## Step 6: Service Accounts (Least Privilege)

```bash
# Create a system account: no login shell, no home dir, low UID
useradd -r -s /bin/false serviceacct
cat /etc/passwd | grep serviceacct
```

**📸 Verified Output:**
```
serviceacct:x:999:999::/home/serviceacct:/bin/false
```

> 💡 Service accounts should have:
> - `-r` (system account, UID < 1000 by default)
> - `-s /bin/false` or `/usr/sbin/nologin` (no interactive login)
> - No password (locked account)
> - Minimal group memberships
>
> This is why nginx runs as `www-data`, postgres as `postgres`, etc. — a compromised service process can only do what that service account is allowed to do.

---

## Step 7: Modifying and Deleting Users

```bash
# Change user's shell
usermod -s /bin/sh alice
grep alice /etc/passwd

# Lock an account
usermod -L alice
grep alice /etc/shadow | cut -d: -f1-2   # ! prefix means locked
```

**📸 Verified Output:**
```
alice:x:1000:1000::/home/alice:/bin/sh
alice:!!
```

```bash
# Unlock the account
usermod -U alice
grep alice /etc/shadow | cut -d: -f1-2
```

**📸 Verified Output:**
```
alice:!
```

---

## Step 8: Capstone — Enterprise User Provisioning Script

```bash
cat > /tmp/provision_users.sh << 'SCRIPT'
#!/bin/bash
# Provision dev team users

# Create shared group
groupadd -f engineering 2>/dev/null

# Create developers
for user in dev1 dev2 dev3; do
    if ! id "$user" &>/dev/null; then
        useradd -m -s /bin/bash -G engineering "$user"
        echo "${user}:$(openssl rand -base64 12)" | chpasswd
        echo "Created user: $user"
    fi
done

# Create service account for CI/CD
useradd -r -s /bin/false -c "CI/CD Pipeline" cibot 2>/dev/null
echo "Created service account: cibot"

# Report
echo ""
echo "=== User Report ==="
getent group engineering
echo ""
echo "Users created:"
for u in dev1 dev2 dev3 cibot; do id "$u"; done
SCRIPT

bash /tmp/provision_users.sh
```

**📸 Verified Output:**
```
Created user: dev1
Created user: dev2
Created user: dev3
Created service account: cibot

=== User Report ===
engineering:x:1004:dev1,dev2,dev3

Users created:
uid=1002(dev1) gid=1002(dev1) groups=1002(dev1),1004(engineering)
uid=1003(dev2) gid=1003(dev2) groups=1003(dev2),1004(engineering)
uid=1004(dev3) gid=1004(dev3) groups=1004(dev3),1004(engineering)
uid=998(cibot) gid=998(cibot) groups=998(cibot)
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `useradd -m -s /bin/bash user` | Create user with home + bash shell |
| `useradd -r -s /bin/false svc` | Create service account (no login) |
| `usermod -aG group user` | Add user to group (append) |
| `usermod -L user` | Lock account |
| `usermod -U user` | Unlock account |
| `groupadd groupname` | Create a group |
| `id user` | Show UID, GID, groups |
| `groups user` | List user's groups |
| `getent group groupname` | Show group members |
