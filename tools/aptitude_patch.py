"""Verified aptitude text and name-input layout changes; no game execution."""
import collections
import re
import struct
from xml.sax.saxutils import escape

import UnityPy

from menu_patch import digest, verify_text
from orwell_resources import encode_string


def load(content):
    asset = next(iter(UnityPy.load(content).files.values()))
    return asset, {pid: obj.get_raw_data() for pid, obj in asset.objects.items()}


def save_checked(asset, expected):
    result = asset.save()
    check = next(iter(UnityPy.load(result).files.values()))
    if set(check.objects) != set(expected):
        raise ValueError('Unexpected object IDs after aptitude/layout patch.')
    for pid, raw in expected.items():
        if check.objects[pid].get_raw_data() != raw:
            raise ValueError(f'Unexpected object changes: {pid}')
    if [(x.path, x.guid, x.type) for x in check.externals] != [(x.path, x.guid, x.type) for x in asset.externals]:
        raise ValueError('External references changed.')
    return result


def patch_resources(content, mapping):
    asset, expected = load(content)
    grouped = collections.defaultdict(list)
    for entry in mapping['resource_strings']:
        grouped[entry['path_id']].append(entry)
    for pid, entries in grouped.items():
        original = expected[pid]
        modified = original
        previous_start = len(original)
        for entry in sorted(entries, key=lambda row: row['offset'], reverse=True):
            if digest(original) != entry['source_object_sha256']:
                raise ValueError(f'Unsupported original aptitude object: {pid}')
            start, span = entry['offset'], entry['span']
            if start < 0 or start % 4 or start + span > previous_start:
                raise ValueError('Overlapping or invalid aptitude fields.')
            size = struct.unpack_from('<i', original, start)[0]
            if size < 0 or span != (size + 7) // 4 * 4:
                raise ValueError('Invalid aptitude string span.')
            source = original[start + 4:start + 4 + size].decode('utf-8')
            target = verify_text(source, entry)
            modified = modified[:start] + encode_string(target) + modified[start + span:]
            previous_start = start
        asset.objects[pid].set_raw_data(modified)
        expected[pid] = modified
    resx = mapping['resx']
    obj = asset.objects[resx['path_id']]
    if digest(expected[obj.path_id]) != resx['source_object_sha256']:
        raise ValueError('Unsupported original language table.')
    tree = obj.read_typetree()
    xml = tree['m_Script']
    for entry in resx['entries']:
        pattern = r'(<data name="' + re.escape(entry['key']) + r'"[^>]*>\s*<value>)(.*?)(</value>)'
        hits = list(re.finditer(pattern, xml, re.S))
        if len(hits) != 1:
            raise ValueError('Language table key is absent or duplicated.')
        match = hits[0]
        target = verify_text(match.group(2), entry)
        xml = xml[:match.start(2)] + escape(target) + xml[match.end(2):]
    tree['m_Script'] = xml
    obj.save_typetree(tree)
    expected[obj.path_id] = obj.data
    result = save_checked(asset, expected)
    return result, {'answer_and_bookmark_strings': len(mapping['resource_strings']),
                    'task_labels': len(resx['entries']), 'modified_objects': sorted([*grouped, obj.path_id])}


def patch_layout(content, mapping):
    asset, expected = load(content)
    seen = set()
    for entry in mapping['objects']:
        pid = entry['path_id']
        original = expected[pid]
        if pid in seen or digest(original) != entry['source_object_sha256']:
            raise ValueError('Input layout source differs or mapping is duplicated.')
        seen.add(pid)
        modified = bytearray(original)
        end = 0
        for edit in entry['edits']:
            start = edit['offset']
            before, after = bytes.fromhex(edit['before_hex']), bytes.fromhex(edit['after_hex'])
            if not before or len(before) != len(after) or start < end or original[start:start + len(before)] != before:
                raise ValueError('Invalid or overlapping layout field edit.')
            end = start + len(before)
            modified[start:end] = after
        asset.objects[pid].set_raw_data(bytes(modified))
        expected[pid] = bytes(modified)
    return save_checked(asset, expected), {'adjusted_objects': sorted(seen), 'runtime_tested': False}
