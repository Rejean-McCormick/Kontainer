# Usage

All commands end with a JSON object. Secrets are entered via `getpass` or explicit descriptors for automation. There is no `--password value` argument or environment variable for supplying passwords. `--password` is only an interactive input flag.

## Commands

| Command | Action |
|---|---|
| `capabilities` | Versions, actually supported features, absence of independent audit |
| `plan SOURCE` | List selected files and sizes; no writes |
| `keygen TYPE OUTPUT` | Generate a secret or key pair |
| `pack SOURCE OUTPUT --mode MODE` | Create a file after snapshot validation |
| `inspect FILE` | Unverified public header |
| `verify FILE` | Full verification, including decryption when required |
| `list FILE` | List members only after complete verification |
| `export FILE MEMBER OUTPUT --allow-plaintext` | Explicit plaintext export of one file |
| `extract FILE DIRECTORY --allow-plaintext` | Full export into a new directory |
| `rewrap FILE OUTPUT --mode MODE` | New protection for the same inner ZIP |

Exit codes: 0 success; 2 format/integrity/access/policy error; 3 environment/operational error; 130 cancellation. Argparse errors also use code 2 but are shown as plain argparse text. The CLI does not display tracebacks or sensitive paths for common OS errors.

## Data selection

Without `--include`, regular files in the directory are selected recursively. The engine **rejects** rather than silently omits common development/secret paths (`.git`, `.env*`, private keys, `.venv`, etc.). This name-based filter is not an exhaustive secret scanner.

```sh
python -m kristal_container plan mon-dossier --include state/snapshot.json --include docs/README.md
python -m kristal_container pack mon-dossier sortie.kristal --mode open --include state/snapshot.json --include docs/README.md
```

Each `--include` refers to one exact file, not a glob or directory. The Local Kit API is preferred for an official projection. `--allow-sensitive` explicitly permits blocked names without disabling path, link, resource-limit or integrity checks.

Empty directories, original permissions, ACLs, timestamps and extended attributes are not preserved. The format is a **portable content** container, not a filesystem backup image. External blobs are never downloaded automatically.

## Password and second secret

```sh
python -m kristal_container keygen factor facteur.ksecret
python -m kristal_container keygen recovery secours.ksecret
python -m kristal_container pack mon-dossier protege.kristal --mode password-factor --factor-key facteur.ksecret --recovery-key secours.ksecret
python -m kristal_container verify protege.kristal --password --unlock-factor facteur.ksecret
```

This cryptographically requires two secrets for normal access. A copyable factor file is not a FIDO/TPM key and must not be described as a hardware factor. The recovery secret is an alternative access path that can unlock the file alone.

## Recipients

```sh
python -m kristal_container keygen identity alice.kkey --public alice-public.json
python -m kristal_container keygen identity bob.kkey --public bob-public.json
python -m kristal_container pack mon-dossier partage.kristal --mode recipient --recipient alice-public.json --recipient bob-public.json
python -m kristal_container verify partage.kristal --identity alice.kkey
```

Private identities are protected with a key-file password. Each recipient can open the file independently. Public keys must be authenticated through an external channel. X25519 is not a post-quantum profile.

## Signatures

```sh
python -m kristal_container keygen signing auteur.kkey --public auteur-public.json
python -m kristal_container pack mon-dossier signe.kristal --mode open --signing-key auteur.kkey
python -m kristal_container verify signe.kristal --trust auteur-public.json
```

Providing `--trust` requires a signature from that trust list. Without `--trust`, an embedded signature is not automatically trusted. `--require-signature` without a trusted key deliberately rejects all signers.

## Rewrapping and loss of access

```sh
python -m kristal_container rewrap ancien.kristal nouveau.kristal --password --mode password
```

Two prompts: existing password, then new password with confirmation. `--new-password-fd` distinguishes the new passphrase in a script. Existing recovery/recipient slots are **not** implicitly retained: supply them explicitly in the new protection.

Removing encryption requires `--mode open --allow-plaintext`. Overwriting a file requires `--overwrite`. These options are independent. Old copies remain accessible; see RECOVERY.md.

## Automation and Windows GUI flows

Call the library directly from Manager for dialogs and hidden processes rather than injecting passwords into a command line. For child processes, use `subprocess` with an argument list, `shell=False`, explicit inherited pipes for passwords and an exit-code check before parsing JSON. Inherited-descriptor mechanisms differ between POSIX and Windows; prefer the Python API in Windows Manager.

Descriptors must carry UTF-8 and reach EOF. Only one final LF or CRLF is stripped for automation. Passwords are never silently truncated.

There is no separate graphical reader in this repository: Manager/Konstellation own the interface. No `.kristal` file association is installed.
