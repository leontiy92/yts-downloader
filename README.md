# yts-downloader
Bulk downloader for YTS movies

How to use:
- Download this project:
`git clone https://github.com/leontiy92/yts-downloader`
- Install MongoDB
- Install aria2
- Run aria2 with the supplied configuration file (edit as needed):
`aria2c --conf-path=aria2.conf`
- Install Python modules:
`pip install -r requirements.txt`
- Run `python3 update-yts.py` to load YTS data to database
- Run:
`python3 downloader.py`

You can check the log (downloader.log) for progress.

You can supply a configuration file or modify parameters from command line
`python3 downloader.py --help`
