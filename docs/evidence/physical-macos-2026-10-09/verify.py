"""Check the recorded native evidence; this does not drive or accept UI actions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / (name + '.json')).read_text())


def views(snapshot):
    return {
        owner['id']: {
            editor['view']: (editor['document'], editor['text'], editor['path'])
            for editor in owner['editors']
        }
        for owner in snapshot['owners']
    }


for left, right in [
    ('final-before-restart', 'final-after-restart'),
    ('final-file-open-b', 'final-after-quit-relaunch'),
]:
    before, after = read(left), read(right)
    assert views(before) == views(after), (left, right)
    assert before['platform'] == after['platform'] == 'cocoa'
    assert not before['qmainwindow'] and not after['qmainwindow']
    for owner in before['owners']:
        restored = next(item for item in after['owners'] if item['id'] == owner['id'])
        old = {frame['id']: frame['geometry'] for frame in owner['frames']}
        for frame in restored['frames']:
            if frame['id'] in old:
                assert frame['geometry'] == old[frame['id']], frame['id']
        assert all(owner['name'] in frame['title'] for frame in restored['frames'])

before, after = read('final-b-float'), read('final-b-view-close')
for owner in before['owners']:
    other = next(item for item in after['owners'] if item['id'] == owner['id'])
    old = {editor['view'] for editor in owner['editors']}
    new = {editor['view'] for editor in other['editors']}
    assert not new - old
    assert len(old - new) == (1 if owner['name'] == 'Physical B' else 0)
    assert owner['shells'] == other['shells']
assert before['documents'] == after['documents']

before, after = read('final-before-frame-close'), read('final-frame-cancel')
assert views(before) == views(after)
for owner in before['owners']:
    other = next(item for item in after['owners'] if item['id'] == owner['id'])
    assert owner['shells'] == other['shells']
    assert owner['layout'] == other['layout']

for prefix in ['initial', 'final']:
    events = [json.loads(line) for line in (ROOT / (prefix + '-events.jsonl')).read_text().splitlines()]
    exits = [event for event in events if event['kind'] == 'process-returned']
    assert exits and all(event['errors'] == [] for event in exits)
print('Native identity/text/geometry/affiliation, cancellation, B-only close and clean-exit assertions pass.')
