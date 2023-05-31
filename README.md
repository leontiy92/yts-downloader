# yts-downloader
Bulk downloader for YTS movies

How to use:
- Download this project:
```
git clone https://github.com/leontiy92/yts-downloader
```
- Install MongoDB
- Install [aria2](https://aria2.github.io/)
- Run aria2 with the supplied configuration file (edit as needed):
```
aria2c --conf-path=aria2.conf
```
- Install Python modules:
```
pip install -r requirements.txt
```
- Run 
```
python3 update-yts.py
```
to load YTS data to database
- Run:
```
python3 downloader.py
```

You can check the log (downloader.log) for progress.

You can supply a configuration file or modify parameters from command line
```
python3 downloader.py --help
```

PS: you can install:
```
pip install aria2p[tui]
```

and then run:
```
aria2p
```
to see progress

## Configuration
Configuration supplied in config file or command-line.
Run
```
python3 downloader.py --help
```
to see options:
```
usage: downloader.py [-h] [-c CONFIG_FILE] [-l LOG_FILE] [--log-level LOG_LEVEL] [--mongodb MONGODB] [--mongodb-collection MONGODB_COLLECTION] [--aria-host ARIA_HOST] [--aria-port ARIA_PORT]
                     [--aria-secret ARIA_SECRET] [--max-con-dl MAX_CON_DL] [-q QUALITY] [-d DOWNLOAD_DIR] [-t TEMP_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        config file path
  -l LOG_FILE, --log-file LOG_FILE
                        log file path
  --log-level LOG_LEVEL
                        log level (DEBUG, INFO, WARN, ERROR)
  --mongodb MONGODB     MogoDB connection string
  --mongodb-collection MONGODB_COLLECTION
                        MogoDB collection to use
  --aria-host ARIA_HOST
                        aria2 host
  --aria-port ARIA_PORT
                        aria2 port
  --aria-secret ARIA_SECRET
                        aria2 secret
  --max-con-dl MAX_CON_DL
                        Maximum concurrent downloads
  -q QUALITY, --quality QUALITY
                        Movie quality to download
  -d DOWNLOAD_DIR, --download-dir DOWNLOAD_DIR
                        Download directory
  -t TEMP_DIR, --temp-dir TEMP_DIR
                        Directory for in-progress downloads

Args that start with '--' (eg. -l) can also be set in a config file (downloader.conf or specified via -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax
at https://goo.gl/R74nmi). If an arg is specified in more than one place, then commandline values override config file values which override defaults.
```

Default configuration file is
```
downloader.conf
```
See https://pypi.org/project/ConfigArgParse/ for details
