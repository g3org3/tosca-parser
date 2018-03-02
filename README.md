# tosca-parser

## Usage

Clone or fork the repo
```sh
git clone https://github.com/g3org3/tosca-parser
cd tosca-parser

# If you fork, you might want to add this for fetching updates.
git remote add upstream https://github.com/g3org3/tosca-parser

# fetch an update
git fetch upstream
git rebase upstream/master
```

Install dependencies
```sh
cd tosca-parser # to this repo
pip install -r requirements.txt
```
Build & install the tool
```sh
python setup.py install
```

Ready to use! 🔥
```sh
tosca-parser -h
```
