# contributing

hey thanks for wanting to help out 👋

## found a bug?

open an issue. tell me:
- what happened
- how to reproduce it
- your OS and python version

that's it. no template needed, just be clear about what went wrong.

## got an idea?

same thing — open an issue. describe what you want and why it'd be useful. bonus points if you've thought about how it fits with what's already here.

## wanna submit code?

1. fork it
2. make a branch (`git checkout -b feature/whatever`)
3. do your thing
4. test it
5. commit with a message that actually says what you did
6. push and open a PR

## setting up for development

```bash
git clone https://github.com/arhanpratama5775-ux/prompt-mirror.git
cd prompt-mirror

python -m venv venv
source venv/bin/activate  # windows: venv\Scripts\activate

pip install -e .
pip install pytest black flake8

# run tests
pytest

# format
black prompt_mirror
```

## code style

- follow PEP 8 (or just run black, it does the thinking for you)
- add docstrings if the function isn't obvious
- keep functions small and focused

## adding a new platform

wanna support a new AI chat export? here's what you need to touch:

1. add detection logic in `parser.py`
2. add the parsing method in `parser.py`
3. add a test with sample data
4. update the docs

## questions?

just open an issue. no such thing as a dumb question.

---

all contributions welcome, no matter how small. even typo fixes count.
