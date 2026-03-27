# RELEASE

## Release Checklist

### Versioning

- Update `APP_VERSION` in `release_metadata.py`
- Add release notes in `release_metadata.py`
- Update `CHANGELOG.md`

### Validation

- Run `python -m unittest discover -s tests -v`
- Launch `python main.py`
- Check startup default target and segmented button state
- Check updater behavior on both direct and corporate-style networks if possible

### Packaging

- Run `pyinstaller "Gas Flow Calc V6.1.spec"`
- Verify output executable name includes the new version
- Smoke-test the packaged `.exe`

### Publishing

- Commit the release changes
- Tag the release as `v6.1.7`
- Push `main` and the tag
- Publish the GitHub release with the matching notes
