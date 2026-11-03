import json,sys
from pathlib import Path
Path('/tmp/pyzo-association-started.log').open('a').write(repr(sys.argv)+'\n')
sys.path.insert(0, '/home/luna/src/toas-rhizome-pyzo-ui-smashup-linux-arm64-cee88feb/deps/pyzo/pyzo')
from yoton.clientserver import do_request
reply=do_request('localhost:pyzo-association-2026-11-03', 'open '+sys.argv[1], 3)
Path('/tmp/pyzo-association-receipt.json').write_text(json.dumps(dict(argv=sys.argv,reply=reply),indent=2))
