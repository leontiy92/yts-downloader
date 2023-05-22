import configargparse
import dlmgr
import subtitles
import logging

p = configargparse.ArgParser(default_config_files=['downloader.conf'])
p.add('-c', '--config-file', is_config_file=True, help='config file path')
p.add('-l', '--log-file', help='log file path', default='downloader.log')
p.add('--log-level', help='log level (DEBUG, INFO, WARN, ERROR)', default=logging.INFO)

p.add('--mongodb', help="MogoDB connection string", default="mongodb://127.0.0.1:27017")
p.add('--mongodb-collection', help="MogoDB collection to use", default="yts")

p.add('--aria-host', help="aria2 host", default="127.0.0.1")
p.add('--aria-port', help="aria2 port", default=6800, type=int)
p.add('--aria-secret', help="aria2 secret", default="")

p.add('--max-con-dl', help="Maximum concurrent downloads", default=30, type=int)
p.add('-q', '--quality', help="Movie quality to download", default="1080p")

p.add('-d', '--download-dir', help="Download directory", default="movies")
p.add('-t', '--temp-dir', help="Directory for in-progress downloads", default="dl")

options = p.parse_args()

level = options.log_level
if isinstance(level, str):
  level = getattr(logging, level.upper())

logging.basicConfig(filename=options.log_file, level=level)

dlmgr.setup(options)
subtitles.setup(options)

logging.info("starting")
dlmgr.run()
