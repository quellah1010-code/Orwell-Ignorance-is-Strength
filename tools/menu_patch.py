"""Patch verified UI strings without executing or redistributing game code."""
import collections
import hashlib
import re
import struct

import dnfile
import UnityPy

from orwell_resources import encode_string


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_text(source, entry):
    if digest(source.encode('utf-8')) != entry['source_text_sha256']:
        raise ValueError('UI source text differs from the verified mapping.')
    target = entry['target']
    if not target or '\0' in target:
        raise ValueError('Empty or invalid UI translation.')
    if collections.Counter(re.findall(r'\{[^{}]*\}', source)) != collections.Counter(re.findall(r'\{[^{}]*\}', target)):
        raise ValueError('UI translation changed placeholders.')
    if re.findall(r'<[^<>]*>', source) != re.findall(r'<[^<>]*>', target):
        raise ValueError('UI translation changed markup or link order.')
    return target


def patch_scene(content, mapping, filename='level1'):
    if digest(content) != mapping['source_hashes'][filename]:
        raise ValueError(f'{filename} differs from the supported original game build.')
    asset = next(iter(UnityPy.load(content).files.values()))
    original = {pid: obj.get_raw_data() for pid, obj in asset.objects.items()}
    expected = dict(original)
    changed = set()
    for entry in mapping['scene']:
        pid, start, span = entry['path_id'], entry['offset'], entry['span']
        if pid in changed:
            raise ValueError('Duplicate scene object mapping.')
        raw = original[pid]
        if digest(raw) != entry['source_object_sha256'] or start % 4:
            raise ValueError('UI object or field offset differs.')
        size = struct.unpack_from('<i', raw, start)[0]
        if size < 0 or span != (size + 7) // 4 * 4 or start + span > len(raw):
            raise ValueError('Invalid UI string field bounds.')
        source = raw[start + 4:start + 4 + size].decode('utf-8')
        replacement = encode_string(verify_text(source, entry))
        expected[pid] = raw[:start] + replacement + raw[start + span:]
        asset.objects[pid].set_raw_data(expected[pid])
        changed.add(pid)
    serialized = asset.save()
    check = next(iter(UnityPy.load(serialized).files.values()))
    if set(check.objects) != set(original):
        raise ValueError('Scene object IDs changed.')
    for pid, obj in check.objects.items():
        if obj.get_raw_data() != expected[pid]:
            raise ValueError(f'Scene object verification failed: {pid}')
    if [(x.path, x.guid, x.type) for x in asset.externals] != [(x.path, x.guid, x.type) for x in check.externals]:
        raise ValueError('Scene external references changed.')
    return serialized, {'translated_objects': len(changed), 'unchanged_objects': len(original) - len(changed)}


def encode_user_string(text):
    # ECMA-335 II.24.2.4: compressed byte length, UTF-16LE, terminal flag.
    data = text.encode('utf-16-le')
    units = struct.unpack('<' + 'H' * (len(data) // 2), data)
    special = any(u > 0xff or (u & 0xff) in (*range(1, 9), *range(14, 32), 0x27, 0x2d, 0x7f) for u in units)
    data += bytes([int(special)])
    size = len(data)
    if size < 0x80:
        prefix = bytes([size])
    elif size < 0x4000:
        prefix = bytes([0x80 | (size >> 8), size & 0xff])
    else:
        raise ValueError('UI string exceeds supported heap entry size.')
    return prefix + data


def patch_assembly(content, mapping):
    if digest(content) != mapping['source_hashes']['Managed/Assembly-CSharp.dll']:
        raise ValueError('Assembly-CSharp.dll differs from the supported original game build.')
    pe = dnfile.dnPE(data=content)
    heap = pe.net.user_strings
    result = bytearray(content)
    ranges, seen = [], set()
    for entry in mapping['dll']:
        token = entry['token']
        if token in seen:
            raise ValueError('Duplicate user-string mapping.')
        seen.add(token)
        item = heap.get(token)
        replacement = encode_user_string(verify_text(item.value, entry))
        start = heap.file_offset + token
        old = item.raw_data
        if content[start:start + len(old)] != old or len(replacement) > len(old):
            raise ValueError('UI translation does not fit its verified string-heap slot.')
        # Keep every token/address stable. Spare bytes become unused zero entries.
        result[start:start + len(old)] = replacement + bytes(len(old) - len(replacement))
        ranges.append((start, start + len(old)))
    cursor = 0
    for start, end in sorted(ranges):
        if start < cursor or result[cursor:start] != content[cursor:start]:
            raise ValueError('Assembly changed outside selected string entries.')
        cursor = end
    if len(result) != len(content) or result[cursor:] != content[cursor:]:
        raise ValueError('Assembly layout changed.')
    check = dnfile.dnPE(data=bytes(result))
    for entry in mapping['dll']:
        if check.net.user_strings.get(entry['token']).value != entry['target']:
            raise ValueError('Managed string readback failed.')
    pe.close()
    check.close()
    return bytes(result), {'translated_strings': len(seen), 'unchanged_outside_selected_heap_entries': True}
