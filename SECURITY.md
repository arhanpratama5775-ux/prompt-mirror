# security

## found a vulnerability?

**don't open a public issue.** seriously.

instead, go here:
https://github.com/arhanpratama5775-ux/prompt-mirror/security/advisories

click "Report a vulnerability" and tell me:
- what the vulnerability is
- how to reproduce it
- what the impact could be
- a fix if you have one

### what happens next

1. i'll confirm i got it (within 48 hours)
2. i'll look into it
3. i'll fix it and test the fix
4. we'll coordinate disclosure

---

## how this tool handles your data

this is the important part so i'm putting it up front:

- **everything runs locally.** no api calls. no servers. nothing leaves your machine.
- **no telemetry.** no analytics. no tracking. no account needed.
- **no persistent storage.** the tool reads your files, makes a report, and that's it.
- **you control the output.** reports go where you tell them to go. nowhere else.

## security measures

- file paths are validated (no directory traversal)
- files over 500MB are rejected
- all user input is validated before processing
- output filenames are sanitized

## tips for staying safe

### your export files are sensitive

treat them like a diary:

```bash
# lock it down
chmod 600 conversations.json

# delete when done
rm conversations.json

# or shred it on linux
shred -u conversations.json
```

### your reports contain your data too

```bash
# clean up after reading
rm -rf mirror-report.* charts/ *.pdf trends.*
```

### use a venv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### keep it updated

```bash
git pull origin main
pip install -e . --upgrade
```

## running in docker

if that's your thing:

```dockerfile
# don't run as root
RUN useradd -m -u 1000 mirror
USER mirror
```

```bash
# mount read-only
docker run -v /path/to/conversations.json:/tmp/conversations.json:ro ...

# don't persist
docker run --rm ...
```

## dependencies

- minimal dependencies on purpose
- versions are pinned with upper bounds
- run your own audit if you want:

```bash
pip install pip-audit
pip-audit
```

## supported versions

| version | supported |
| ------- | --------- |
| 0.3.x   | yes       |
| 0.2.x   | yes       |
| < 0.2   | no        |

---

questions? same thing — use the security advisories link above.
