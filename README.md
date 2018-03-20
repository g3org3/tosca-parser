# tosca-parser

## Usage

### Clone or fork the repo
```sh
git clone https://github.com/g3org3/tosca-parser
cd tosca-parser

# If you fork, you might want to add this for fetching updates.
git remote add upstream https://github.com/g3org3/tosca-parser

# fetch an update
git fetch upstream
git rebase upstream/master
```

### Lazy-way
```sh
# Only the First Time 
make install

# Every time to build and replace
make
```

### Don't like lazy-way then...

Install dependencies
```sh
cd tosca-parser # to this repo
pip install -r requirements.txt
```
Build & install the tool
```sh
python setup.py install
```


Helpful Links
- [How to install pip](https://pip.pypa.io/en/stable/installing/)
- [How to mange python versions?](https://github.com/pyenv/pyenv#homebrew-on-mac-os-x)

Ready to use! 🔥
```sh
tosca-parser -h
```
