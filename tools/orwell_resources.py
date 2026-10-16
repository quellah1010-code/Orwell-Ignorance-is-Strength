"""Extract verified Orwell 5.6.3f1 dialogue fields without executing game code.

This intentionally supports only the supplied resources.assets build and three
confirmed FlowState subclasses. It is not a complete game localization tool.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import struct
from pathlib import Path

import UnityPy

SOURCE_SHA256 = '1bc553fdc10358d2a4f78de1e2079a61ee46dc993636403dcfbc7b052b607b78'
SCHEMAS = {
    825: ('NewChatMessageState', '_text'),
    730: ('NewCommentaryLineState', '_text'),
    493: ('NewObjectiveState', '_objectiveText'),
}


class Reader:
    def __init__(self, raw):
        self.raw = raw
        self.pos = 0

    def take(self, size):
        if size < 0 or self.pos + size > len(self.raw):
            raise ValueError(f'Invalid read at {self.pos} for {size} bytes')
        result = self.raw[self.pos:self.pos + size]
        self.pos += size
        return result

    def align(self):
        self.take((-self.pos) % 4)

    def number(self, fmt):
        return struct.unpack('<' + fmt, self.take(struct.calcsize('<' + fmt)))[0]

    def boolean(self):
        value = self.number('B')
        if value not in (0, 1):
            raise ValueError(f'Invalid boolean at {self.pos - 1}')
        self.align()
        return value

    def string(self):
        start = self.pos
        size = self.number('i')
        value = self.take(size).decode('utf-8')
        self.align()
        return {'value': value, 'start': start, 'end': self.pos}

    def pointer(self):
        return {'file_id': self.number('i'), 'path_id': self.number('q')}

    def pointers(self):
        count = self.number('i')
        if not 0 <= count <= (len(self.raw) - self.pos) // 12:
            raise ValueError('Invalid reference array')
        return [self.pointer() for _ in range(count)]

    def localized(self):
        count = self.number('i')
        if count != 2:
            raise ValueError(f'Expected DE and EN language slots, got {count}')
        return [self.string() for _ in range(count)]


def parse_state(raw):
    r = Reader(raw)
    game_object = r.pointer()
    r.boolean()
    script = r.pointer()
    if script['file_id'] != 1 or script['path_id'] not in SCHEMAS:
        raise ValueError('Unsupported script reference')
    kind, field = SCHEMAS[script['path_id']]
    name = r.string()['value']
    if not name.startswith(kind + ' ('):
        raise ValueError('Object name does not match the verified schema')
    object_id = r.number('q')
    state_name = r.string()['value']
    r.boolean()  # _ignoreSaveGameLoadingOrder
    r.number('i')  # _priority
    r.boolean()  # _wasExecuted
    r.boolean()  # _conditionsMet
    incoming = r.pointers()
    outgoing = r.pointers()
    speaker = ''
    parent = None
    if kind == 'NewChatMessageState':
        speaker = r.string()['value']
        texts = r.localized()
        parent = r.pointer()
        voice_id = r.string()['value']
        r.number('f')
        r.boolean()
    elif kind == 'NewCommentaryLineState':
        texts = r.localized()
        parent = r.pointer()
        r.pointer()  # _displayUntilStateDone
        r.boolean()  # CommentClicked
        speaker = r.string()['value']
        r.boolean()  # SkipDisplayUntilStateDone; _commentaryLine isn't serialized
        voice_id = ''
    else:
        speaker = r.string()['value']  # _targetPersonId
        texts = r.localized()
        voice_id = ''
    if r.pos != len(raw):
        raise ValueError(f'{kind}: consumed {r.pos} of {len(raw)} bytes')
    return {
        'kind': kind, 'field': field, 'name': name, 'state_name': state_name,
        'object_id': object_id, 'speaker': speaker, 'voice_id': voice_id,
        'parent': parent, 'incoming': incoming, 'outgoing': outgoing,
        'game_object': game_object, 'texts': texts,
    }


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_original(path):
    content = Path(path).read_bytes()
    if sha256(content) != SOURCE_SHA256:
        raise ValueError('Unsupported source build or already modified resources.assets')
    env = UnityPy.load(content)
    asset = next(iter(env.files.values()))
    if asset.unity_version != '5.6.3f1':
        raise ValueError('Unexpected Unity version')
    return env, asset


def records(asset):
    result = {}
    for obj in asset.objects.values():
        if obj.type.name != 'MonoBehaviour':
            continue
        raw = obj.get_raw_data()
        if len(raw) < 28:
            continue
        file_id, path_id = struct.unpack_from('<iq', raw, 16)
        if file_id == 1 and path_id in SCHEMAS:
            record = parse_state(raw)
            record['path_id'] = obj.path_id
            record['source_object_sha256'] = sha256(raw)
            result[obj.path_id] = record
    return result


def export(source, output):
    _, asset = load_original(source)
    data = records(asset)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for filename in ('dialogue-en-zh.csv', 'dialogue-manifest.json'):
        if (output / filename).exists():
            raise FileExistsError(f'Refusing to overwrite {output / filename}')
    columns = ['key', 'kind', 'path_id', 'field', 'speaker', 'state_name',
               'parent_path_id', 'voice_id', 'source', 'target']
    with (output / 'dialogue-en-zh.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for pid, rec in sorted(data.items()):
            writer.writerow({
                'key': f'resources.assets/{pid}/{rec["field"]}/en',
                'kind': rec['kind'], 'path_id': pid, 'field': rec['field'],
                'speaker': rec['speaker'], 'state_name': rec['state_name'],
                'parent_path_id': rec['parent']['path_id'] if rec['parent'] else '',
                'voice_id': rec['voice_id'], 'source': rec['texts'][1]['value'],
                'target': '',
            })
    manifest = {'source_sha256': SOURCE_SHA256, 'unity_version': asset.unity_version,
                'language_index': 1, 'records': list(data.values())}
    (output / 'dialogue-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    summary = {'records': len(data), 'nonempty_english': sum(bool(r['texts'][1]['value']) for r in data.values()),
               'by_kind': dict(collections.Counter(r['kind'] for r in data.values()))}
    print(json.dumps(summary, ensure_ascii=False))


def encode_string(text):
    data = text.encode('utf-8')
    return struct.pack('<i', len(data)) + data + b'\0' * ((-len(data)) % 4)


def patch(source, translations, output):
    _, asset = load_original(source)
    original = {pid: obj.get_raw_data() for pid, obj in asset.objects.items()}
    data = records(asset)
    changed = {}
    seen = set()
    placeholders = lambda s: collections.Counter(re.findall(r'\{[^{}]*\}', s))
    tags = lambda s: re.findall(r'<[^<>]*>', s)
    with Path(translations).open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            pid = int(row['path_id'])
            if pid in seen:
                raise ValueError(f'Duplicate translation row {pid}')
            seen.add(pid)
            rec = data[pid]
            if row['key'] != f'resources.assets/{pid}/{rec["field"]}/en':
                raise ValueError(f'Translation key mismatch for {pid}')
            field = rec['texts'][1]
            if row['source'] != field['value']:
                raise ValueError(f'Source mismatch for {pid}')
            text = row['target']
            if not text or text == field['value']:
                continue
            if '\0' in text or placeholders(text) != placeholders(field['value']) or tags(text) != tags(field['value']):
                raise ValueError(f'Changed placeholders or markup in {pid}')
            raw = original[pid]
            modified = raw[:field['start']] + encode_string(text) + raw[field['end']:]
            parsed = parse_state(modified)
            if parsed['texts'][1]['value'] != text:
                raise ValueError('Failed immediate text readback')
            for key in rec:
                if key not in ('texts', 'path_id', 'source_object_sha256') and parsed[key] != rec[key]:
                    raise ValueError(f'Unexpected state metadata change: {pid}/{key}')
            if parsed['texts'][0]['value'] != rec['texts'][0]['value']:
                raise ValueError('Modified the other language slot')
            asset.objects[pid].set_raw_data(modified)
            changed[pid] = {'text': text, 'raw': modified}
    if not changed:
        raise ValueError('No translated rows were provided')
    destination = Path(output)
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    serialized = asset.save()
    loaded = next(iter(UnityPy.load(serialized).files.values()))
    if set(loaded.objects) != set(original):
        raise ValueError('Asset object IDs changed during serialization')
    for pid, obj in loaded.objects.items():
        expected = changed[pid]['raw'] if pid in changed else original[pid]
        if obj.get_raw_data() != expected:
            raise ValueError(f'Object {pid} failed byte-for-byte verification')
    for pid, item in changed.items():
        if parse_state(loaded.objects[pid].get_raw_data())['texts'][1]['value'] != item['text']:
            raise ValueError('Failed final translation readback')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as f:
        f.write(serialized)
    print(json.dumps({'changed_objects': len(changed), 'unchanged_objects_verified': len(original) - len(changed),
                      'output_sha256': sha256(serialized), 'output': str(destination),
                      'runtime_tested': False, 'chinese_font_included': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    ex = sub.add_parser('extract')
    ex.add_argument('source')
    ex.add_argument('output')
    pa = sub.add_parser('patch')
    pa.add_argument('source')
    pa.add_argument('translations')
    pa.add_argument('output')
    args = parser.parse_args()
    if args.command == 'extract':
        export(args.source, args.output)
    else:
        patch(args.source, args.translations, args.output)
