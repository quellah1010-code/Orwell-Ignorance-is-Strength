"""Build an experimental static CJK fallback for the supplied TMP 1.x assets."""
import argparse
import collections
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

import attrs
import numpy as np
import UnityPy
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt

from orwell_resources import Reader, encode_string, parse_state, SOURCE_SHA256

FONT_SHA256 = '2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b'
FACE_FIELDS = ['LineHeight', 'Baseline', 'Ascender', 'CapHeight', 'Descender',
               'CenterLine', 'SuperscriptOffset', 'SubscriptOffset', 'SubSize',
               'Underline', 'UnderlineThickness', 'strikethrough',
               'strikethroughThickness', 'TabWidth', 'Padding', 'AtlasWidth', 'AtlasHeight']


def pointer(path_id=0, file_id=0):
    return struct.pack('<iq', file_id, path_id)


def parse_font(raw):
    r = Reader(raw)
    r.pointer(); r.boolean(); script = r.pointer()
    name = r.string()['value']
    r.number('i'); material = r.pointer(); r.number('i'); font_type = r.number('i')
    face = {'Name': r.string()['value'], 'PointSize': r.number('f'),
            'Scale': r.number('f'), 'CharacterCount': r.number('i')}
    face.update({key: r.number('f') for key in FACE_FIELDS})
    atlas = r.pointer()
    count = r.number('i')
    if not 0 < count < 65536:
        raise ValueError('Invalid glyph count')
    glyphs = [(r.number('i'), *[r.number('f') for _ in range(8)]) for _ in range(count)]
    kerning_count = r.number('i')
    if not 0 <= kerning_count < 100000:
        raise ValueError('Invalid kerning count')
    r.take(12 * kerning_count)
    r.take(12)
    fallbacks = r.pointers()
    r.string()
    r.take(8 * 4)
    r.number('f'); r.number('i'); r.boolean()
    weights = r.number('i')
    if weights != 10:
        raise ValueError('Unexpected TMP font weight table')
    r.take(24 * weights)
    styles = [r.number('f') for _ in range(4)]
    r.number('B'); r.align(); r.number('B'); r.align()
    if r.pos != len(raw) or len({g[0] for g in glyphs}) != count:
        raise ValueError('Font structure did not validate')
    return {'name': name, 'script': script, 'material': material, 'font_type': font_type,
            'face': face, 'atlas': atlas, 'glyphs': glyphs, 'fallbacks': fallbacks, 'styles': styles}


def font_bytes(template, face, glyphs, material_id, atlas_id):
    # Keep the Unity MonoBehaviour header including its existing script reference.
    raw = bytearray(template[:28])
    raw += encode_string('Orwell Chinese Preview SDF')
    raw += struct.pack('<i', 0) + pointer(material_id) + struct.pack('<ii', 0, 1)
    raw += encode_string('Orwell Chinese Preview')
    raw += struct.pack('<ffi', face['PointSize'], 1.0, len(glyphs))
    raw += struct.pack('<17f', *[face[key] for key in FACE_FIELDS])
    raw += pointer(atlas_id) + struct.pack('<i', len(glyphs))
    for glyph in glyphs:
        raw += struct.pack('<i8f', *glyph)
    raw += struct.pack('<i', 0)  # Empty kerning table.
    raw += struct.pack('<iif', 0, 0, 0.0)  # Serialized editor kerning pair.
    raw += struct.pack('<i', 0)  # No recursive fallbacks.
    raw += encode_string('')  # Editor font source path.
    raw += bytes(44)  # Eight ints, float style modifier, render mode, aligned bool.
    raw += struct.pack('<i', 10) + bytes(10 * 24)  # Ten regular/italic font pairs.
    raw += struct.pack('<4f', 0, 0, 0.75, 7.0)
    raw += bytes((35, 0, 0, 0, 10, 0, 0, 0))
    parse_font(bytes(raw))
    return bytes(raw)


def settings_fallback_span(raw):
    r = Reader(raw)
    r.pointer(); r.boolean(); r.pointer(); r.string()
    for _ in range(5):
        r.boolean()
    r.number('i'); r.boolean(); r.pointer(); r.string()
    r.take(7 * 4)  # Font size, two autosize ratios, two Vector2s.
    r.boolean()
    start = r.pos
    fallbacks = r.pointers()
    end = r.pos
    r.boolean(); r.pointer(); r.string(); r.boolean()
    r.pointer(); r.pointer(); r.pointer()
    if r.pos != len(raw):
        raise ValueError('Unexpected TMP Settings layout')
    return start, end, fallbacks


def make_atlas(font_path, chars, atlas_size=2048, point_size=64, padding=9):
    tt = TTFont(font_path)
    cmap = tt.getBestCmap()
    missing = [c for c in chars if ord(c) not in cmap]
    if missing:
        raise ValueError(f'Font lacks codepoints: {missing!r}')
    units = tt['head'].unitsPerEm
    ascent = tt['hhea'].ascent * point_size / units
    descent = tt['hhea'].descent * point_size / units
    cap = tt['OS/2'].sCapHeight * point_size / units
    face = {
        'PointSize': float(point_size), 'LineHeight': ascent - descent,
        'Baseline': 0., 'Ascender': ascent, 'CapHeight': cap, 'Descender': descent,
        'CenterLine': 0., 'SuperscriptOffset': ascent, 'SubscriptOffset': descent / 2,
        'SubSize': .5, 'Underline': -point_size * .12, 'UnderlineThickness': point_size * .05,
        'strikethrough': cap * .4, 'strikethroughThickness': point_size * .05,
        'TabWidth': point_size * 2.5, 'Padding': float(padding),
        'AtlasWidth': float(atlas_size), 'AtlasHeight': float(atlas_size),
    }
    tt.close()
    scale = 4
    regular = ImageFont.truetype(str(font_path), point_size)
    highres = ImageFont.truetype(str(font_path), point_size * scale)
    atlas = Image.new('L', (atlas_size, atlas_size), 0)
    glyphs = []
    cursor_x = cursor_y = 0
    row_height = 0
    border = padding + 2
    for char in sorted(chars, key=ord):
        left, top, right, bottom = regular.getbbox(char, anchor='ls')
        width, height = right - left, bottom - top
        advance = float(regular.getlength(char))
        if height == 0 or width == 0:
            glyphs.append((ord(char), 0., 0., 0., 0., 0., ascent, advance, 1.))
            continue
        cell_w, cell_h = width + 2 * border, height + 2 * border
        if cursor_x + cell_w > atlas_size:
            cursor_x = 0
            cursor_y += row_height
            row_height = 0
        if cursor_y + cell_h > atlas_size:
            raise ValueError('Preview glyph atlas is full')
        mask = Image.new('L', (cell_w * scale, cell_h * scale), 0)
        ImageDraw.Draw(mask).text(((border - left) * scale, (border - top) * scale),
                                 char, font=highres, anchor='ls', fill=255)
        inside = np.asarray(mask) >= 128
        signed = (distance_transform_edt(inside) - distance_transform_edt(~inside)) / scale
        sdf = np.clip(127.5 + signed * 127.5 / (padding + 1), 0, 255).astype(np.uint8)
        tile = Image.fromarray(sdf).resize((cell_w, cell_h), Image.Resampling.BOX)
        atlas.paste(tile, (cursor_x, cursor_y))
        glyphs.append((ord(char), float(cursor_x + border), float(cursor_y + border),
                       float(width), float(height), float(left), float(-top), advance, 1.))
        cursor_x += cell_w
        row_height = max(row_height, cell_h)
    return atlas, face, glyphs


def build(source, translated, font_path, translations, output):
    source = Path(source)
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('Original game build differs')
    font_path = Path(font_path)
    if hashlib.sha256(font_path.read_bytes()).hexdigest() != FONT_SHA256:
        raise ValueError('Font checksum differs')
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    original_file = next(iter(UnityPy.load(str(source)).files.values()))
    original = {pid: o.get_raw_data() for pid, o in original_file.objects.items()}
    asset = next(iter(UnityPy.load(str(translated)).files.values()))
    expected = {pid: o.get_raw_data() for pid, o in asset.objects.items()}
    rows = list(csv.DictReader(Path(translations).open(encoding='utf-8-sig', newline='')))
    translated_rows = {int(row['path_id']): row for row in rows if row['target']}
    for pid, raw in original.items():
        if pid in translated_rows:
            if parse_state(expected[pid])['texts'][1]['value'] != translated_rows[pid]['target']:
                raise ValueError('Translation CSV differs from the input asset')
        elif raw != expected[pid]:
            raise ValueError('Unexpected input asset changes')
    chars = set(chr(i) for i in range(32, 127))
    for row in rows:
        chars.update(c for c in row['target'] if c.isprintable())
    atlas_image, face, glyphs = make_atlas(font_path, chars)
    font_id, material_id, atlas_id = [max(asset.objects) + i for i in (1, 2, 3)]
    additions = []
    for old_id, new_id in ((5003, font_id), (23, material_id), (178, atlas_id)):
        clone = attrs.evolve(asset.objects[old_id], path_id=new_id, data=None)
        asset.objects[new_id] = clone
        additions.append(new_id)
    asset.objects[font_id].set_raw_data(font_bytes(asset.objects[5003].get_raw_data(), face, glyphs, material_id, atlas_id))
    material = asset.objects[23].read_typetree()
    material['m_Name'] = 'Orwell Chinese Preview SDF Material'
    for key, value in material['m_SavedProperties']['m_TexEnvs']:
        if key == '_MainTex':
            value['m_Texture'] = {'m_FileID': 0, 'm_PathID': atlas_id}
    floats = {'_GradientScale': face['Padding'] + 1, '_TextureWidth': face['AtlasWidth'],
              '_TextureHeight': face['AtlasHeight'], '_FaceDilate': 0.0}
    material['m_SavedProperties']['m_Floats'] = [[k, floats.get(k, v)] for k, v in material['m_SavedProperties']['m_Floats']]
    asset.objects[material_id].save_typetree(material)
    texture = asset.objects[atlas_id].read()
    texture.m_Name = 'Orwell Chinese Preview SDF Atlas'
    rgba_atlas = Image.new('RGBA', atlas_image.size, (255, 255, 255, 0))
    rgba_atlas.putalpha(atlas_image)
    texture.set_image(rgba_atlas, target_format=1, mipmap_count=1)
    texture.save()
    settings = asset.objects[5007].get_raw_data()
    start, end, fallbacks = settings_fallback_span(settings)
    new_fallbacks = struct.pack('<i', len(fallbacks) + 1)
    for entry in fallbacks:
        new_fallbacks += pointer(entry['path_id'], entry['file_id'])
    new_fallbacks += pointer(font_id)
    settings = settings[:start] + new_fallbacks + settings[end:]
    asset.objects[5007].set_raw_data(settings)
    expected[5007] = settings
    for pid in additions:
        expected[pid] = asset.objects[pid].data
    serialized = asset.save()
    check = next(iter(UnityPy.load(serialized).files.values()))
    if set(check.objects) != set(expected):
        raise ValueError('Unexpected object IDs after font insertion')
    for pid, obj in check.objects.items():
        if obj.get_raw_data() != expected[pid]:
            raise ValueError(f'Unexpected serialized bytes in object {pid}')
    loaded_font = parse_font(check.objects[font_id].get_raw_data())
    if {g[0] for g in loaded_font['glyphs']} != {ord(c) for c in chars}:
        raise ValueError('Glyph coverage check failed')
    settings_after = settings_fallback_span(check.objects[5007].get_raw_data())[2]
    if settings_after != fallbacks + [{'file_id': 0, 'path_id': font_id}]:
        raise ValueError('Fallback reference check failed')
    loaded_atlas = check.objects[atlas_id].read().image.getchannel('A')
    if loaded_atlas.tobytes() != atlas_image.tobytes():
        raise ValueError('Texture encoding/decoding roundtrip failed')
    if len(check.externals) != len(original_file.externals) or any(a.path != b.path for a,b in zip(check.externals,original_file.externals)):
        raise ValueError('External file references changed')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as f:
        f.write(serialized)
    atlas_image.save(output.parent.parent / 'font-atlas.png')
    report = {
        'original_sha256': SOURCE_SHA256, 'font_source_sha256': FONT_SHA256,
        'patched_sha256': hashlib.sha256(serialized).hexdigest(),
        'translated_entries': len(translated_rows), 'new_font_codepoints': len(chars),
        'new_cjk_codepoints': sum(0x4e00 <= ord(c) <= 0x9fff for c in chars),
        'new_objects': additions, 'modified_existing_objects': sorted([*translated_rows, 5007]),
        'unchanged_objects_byte_verified': len(original) - len(translated_rows) - 1,
        'font_references_verified': True, 'atlas_roundtrip_verified': True,
        'runtime_tested': False, 'scope': 'Introduction commentary and three early objectives only',
    }
    (output.parent.parent / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'translated', 'font', 'translations', 'output'):
        p.add_argument(name)
    a = p.parse_args()
    build(a.source, a.translated, a.font, a.translations, a.output)
