# 🤝 Contributing to dotref

## No coding required
The most valuable contribution right now is data.
Add a `.toml` file for a subsystem you know well.

## Steps
1. Fork the repo
2. Create or edit a file in `data/<subsystem>/<category>.toml`
3. Follow the [Data format](README.md#️-data-format) section in the README — every knob is a `[knob.<id>]` table
4. Validate locally before pushing:
   ```bash
   python3 -c "import tomllib, pathlib; [tomllib.loads(p.read_text()) for p in pathlib.Path('data').rglob('*.toml')]"
   python3 dotref.py --data-dir ./data <subsystem> <category>
   ```
5. Open a PR with a link to your source (man page, official docs, etc.)

## Want to build the CLI?
Open an issue — let's talk about scope first.
