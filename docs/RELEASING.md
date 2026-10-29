# Releasing LibrePrint

Every tag `vX.Y.Z` pushed to GitHub makes the CI workflow:

1. run the tests and build `libreprint_X.Y.Z_all.deb`,
2. attach it to a GitHub Release (also as `libreprint_all.deb`),
3. publish the signed APT repository and `install.sh` on GitHub Pages
   (`https://YOUR-USERNAME.github.io/libreprint`).

Users who added the repository get the new version with `sudo apt upgrade`.

## One-time setup

### 1. Create the signing key

APT only trusts repositories signed with a GPG key. Create one just for LibrePrint, without a
passphrase so CI can use it:

```sh
gpg --batch --passphrase '' --quick-gen-key "LibrePrint APT <you@example.com>" ed25519 sign never
gpg --list-secret-keys "LibrePrint APT"          # note the key id (long hex string)
gpg --armor --export-secret-keys "LibrePrint APT" > libreprint-apt-private.asc
```

Keep a backup of `libreprint-apt-private.asc` somewhere safe and **never commit it**. If the key is
lost, users have to install a new public key; if it leaks, anyone can sign packages they trust.

### 2. Add it to GitHub

In the repository: **Settings → Secrets and variables → Actions → New repository secret**

- Name: `APT_GPG_PRIVATE_KEY`
- Value: the whole content of `libreprint-apt-private.asc`

Then delete the local `.asc` file (the key stays in your gpg keyring).

### 3. Turn on GitHub Pages

**Settings → Pages → Build and deployment → Source: GitHub Actions.**

## Making a release

1. Set the version in `src/libreprint/__init__.py` (`__version__ = "X.Y.Z"`) and commit.
2. Tag and push:

   ```sh
   git tag vX.Y.Z
   git push origin main vX.Y.Z
   ```

3. Watch the **Actions** tab. When it is green, the release page has the `.deb` and
   `https://YOUR-USERNAME.github.io/libreprint` serves the repository.

The tag and `__version__` must match; otherwise APT sees the old version number.

## Testing the repository locally

```sh
bash packaging/build-deb.sh
bash packaging/build-apt-repo.sh /tmp/libreprint-repo dist/libreprint_*_all.deb
```

`build-apt-repo.sh` signs with your default gpg key, or with `APT_SIGNING_KEY=<key id>`.
