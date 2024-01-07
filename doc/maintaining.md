# Information for Project Maintainers

This information is for **project maintainers**. If you are simply
contributing to the project, then you don't need to know this, and you
don't need to perform any of these steps.

## Merging into `master`

Merging into `master` uses Git's default merging mechanism. We don't use
rebase-merges or squash-merges. Fast-forward merges are allowed, however,
and encouraged when applicable.

Merging should always be performed locally on the maintainer's system,
and then pushed directly to the `master` branch on GitHub. If the merge
was sufficiently complicated that it would be beneficial to run the
GitHub actions again on the merged result, then merge first into a
temporary test branch, make a new pull request from that, and finally
fast-forward `master` when the result is acceptable.

Note that updating `master` on GitHub _does not_ automatically imply a
release must be made and published to PyPI, but the converse does hold:
releases are only made from the tip of `master`.

## Making a new release

Making a release is a fairly manual process, but it's not too onerous and
doesn't happen very often, so there isn't much impetus to automate it.

Releases are always made from the `master` branch. Thus, begin by checking
out the tip of `master` from GitHub.

### Pre-release checks

The following conditions must be met before the release can be made.

- The code is in a releasable state:
    - unit tests pass,
    - linting reports no violations, and
    - the documentation is up to date.
- The change log (`CHANGELOG.md`) is up to date.

If necessary, make additional commits on `master` until the conditions
are met. The steps that follow assume that the pre-release conditions
are satisfied on the tip of `master`.

### Increment the version

Incrementing the version is done via a small tagged commit. The
information in this section can be summarized succinctly by looking at
one of these commits:

```bash
git show v0.8.1
```

We'll also briefly describe all the steps here.

#### Select a new version

Make sure to follow [PEP-440](https://peps.python.org/pep-0440/).
In this example, `v0.8` is the old version, and `v0.8.1` is the new
version.

Currently, we don't publish alpha or beta releases to PyPI, with the
understanding that prereleases can be checked out directly from GitHub.

#### Update the version in `pyproject.toml`

One line is changed:

```diff
diff --git a/pyproject.toml b/pyproject.toml
index d079b17..5c42074 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -3,7 +3,7 @@
 
 [project]
 name = "plyfile"
-version = "0.8"
+version = "0.8.1"
 description = "PLY file reader/writer"
 authors = [
```

#### Update `CHANGELOG.md`

This should be pretty self-explanatory:

```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 03dba5f..22ee9a5 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -3,6 +3,8 @@
 All notable changes to this project will be documented here.
 
 ## [Unreleased]
+
+## [0.8.1] - 2023-03-18
 ### Changed
 - Package metadata management via PDM, rather than `setuptools`.

@@ -117,7 +119,8 @@ All notable changes to this project will be documented here.
 - Rudimentary test setup.
 - Basic installation script.

-[Unreleased]: https://github.com/dranjan/python-plyfile/compare/v0.8...HEAD
+[Unreleased]: https://github.com/dranjan/python-plyfile/compare/v0.8.1...HEAD
+[0.8.1]: https://github.com/dranjan/python-plyfile/compare/v0.8...v0.8.1
 [0.8]: https://github.com/dranjan/python-plyfile/compare/v0.7.4...v0.8
 [0.7.4]: https://github.com/dranjan/python-plyfile/compare/v0.7.3...v0.7.4
 [0.7.3]: https://github.com/dranjan/python-plyfile/compare/v0.7.2...v0.7.3
```

A new heading containing a link is added. No content is added.

#### Make the commit

```bash
git add pyproject.toml
git add CHANGELOG.md
git commit -m "Bump version"
```

The commit message is exactly as above.

#### Tag the commit

```bash
git tag -a v0.8.1
```

The tag annotation should look like this, with only the `0.8.1` string
changing from version to version:

```none
Version 0.8.1

See CHANGELOG.md for details.
```

### Publish the new version

Prerequisite: generate a API token on PyPI and save it somewhere.
This example will assume the file is saved as `token.txt`.
(PyPI no longer supports normal username/password authentication,
so this step must be performed.)

```bash
pdm publish -u __token__ -P $(< token.txt)
```

To use the test server, add the arguments `-r testpypi`. Note that
a separate API token will be required, generated from your account
on the test server.

### Publish the code to GitHub

```bash
git push origin master v0.8.1
```

(Don't forget to push both the branch and the tag, as shown above!)
