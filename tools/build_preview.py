"""Rebuild the existing 14-entry preview from a local original game resource."""
import argparse
import csv
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

from build_preview_font import FONT_SHA256, build
from orwell_resources import SOURCE_SHA256, load_original, patch, records

ROOT = Path(__file__).resolve().parents[1]
FONT_URL = 'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf'
LICENSE_SHA256 = '6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2'
# Verified with explicit BASIC glyph layout, matching the Windows build.
EXPECTED_PREVIEW_SHA256 = 'f36dbcf44611734ca4e7c7b5ffa8fb31a9977ff1ec7f4cb705cb2dd4f8a0903f'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified_font(supplied):
    path = supplied if supplied else ROOT / '.cache/fonts/NotoSansCJKsc-Regular.otf'
    if path.exists():
        content = path.read_bytes()
    elif supplied:
        raise FileNotFoundError(path)
    else:
        print('Downloading the open CJK font with TLS and SHA-256 verification.')
        with urllib.request.urlopen(FONT_URL, timeout=60) as response:
            content = response.read()
    if digest(content) != FONT_SHA256:
        raise ValueError('Font checksum mismatch. Existing files have not been replaced.')
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(content)
    return path


def translation_rows(source):
    mapping = json.loads((ROOT / 'translations/preview.zh-CN.json').read_text(encoding='utf-8'))
    if mapping['schema_version'] != 1 or mapping['source_asset_sha256'] != SOURCE_SHA256 or mapping['source_language_index'] != 1:
        raise ValueError('Unsupported translation mapping version or source build.')
    _, asset = load_original(source)
    data = records(asset)
    rows = []
    seen = set()
    for entry in mapping['translations']:
        pid = entry['path_id']
        if pid in seen:
            raise ValueError(f'Duplicate translation mapping: {pid}')
        seen.add(pid)
        record = data[pid]
        text = record['texts'][1]['value']
        expected_key = f'resources.assets/{pid}/{record["field"]}/en'
        if entry['key'] != expected_key or entry['field'] != record['field'] or entry['source_text_sha256'] != digest(text.encode('utf-8')):
            raise ValueError(f'Source text verification failed for {pid}.')
        rows.append({
            'key': expected_key, 'kind': record['kind'], 'path_id': pid,
            'field': record['field'], 'speaker': record['speaker'],
            'state_name': record['state_name'],
            'parent_path_id': record['parent']['path_id'] if record['parent'] else '',
            'voice_id': record['voice_id'], 'source': text, 'target': entry['target'],
        })
    if len(rows) != 14:
        raise ValueError('This delivery reproduces the existing 14-entry preview only.')
    return rows


def deliver(source, font, output):
    if output.exists():
        raise FileExistsError(f'Output already exists; choose a new --output directory: {output}')
    rows = translation_rows(source)
    license_path = ROOT / 'licenses/Noto-OFL.txt'
    if digest(license_path.read_bytes()) != LICENSE_SHA256:
        raise ValueError('The bundled open font license checksum differs.')
    font = verified_font(font)
    output.mkdir(parents=True)
    table = output / 'translations-preview.csv'
    with table.open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    intermediate = output / 'text-only-internal.assets'
    patch(source, table, intermediate)
    package = output / 'package'
    patched = package / 'Ignorance_Data/resources.assets'
    build(source, intermediate, font, table, patched)
    if digest(patched.read_bytes()) != EXPECTED_PREVIEW_SHA256:
        raise ValueError('The rebuilt resource differs from the previously verified preview; no ZIP was produced.')
    shutil.copyfile(ROOT / 'docs/preview-install.txt', package / '先读我.txt')
    shutil.copyfile(license_path, package / 'FONT-LICENSE.txt')
    shutil.copyfile(table, package / '测试译文.csv')
    files = ['先读我.txt', 'FONT-LICENSE.txt', '测试译文.csv', 'validation.json', 'Ignorance_Data/resources.assets']
    archive_path = output / 'orwell-zh-preview-0.1.zip'
    with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in files:
            info = zipfile.ZipInfo('orwell-zh-preview-0.1/' + name, date_time=(2026, 10, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (package / name).read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC verification failed.')
        if digest(archive.read('orwell-zh-preview-0.1/Ignorance_Data/resources.assets')) != EXPECTED_PREVIEW_SHA256:
            raise ValueError('Archived resource hash verification failed.')
    print(f'Local ZIP: {archive_path}')
    print(f'ZIP SHA-256: {digest(archive_path.read_bytes())}')
    print('Resource bytes match the verified BASIC-layout preview. Windows gameplay remains untested.')
    print('Generated files contain game resources. Keep this build directory local.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--game-dir', type=Path, help='Installed game root containing Ignorance_Data.')
    inputs.add_argument('--resources', type=Path, help='A preserved original resources.assets file.')
    parser.add_argument('--font-file', type=Path, help='Optional local copy of the exact verified Noto font.')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/preview-0.1', help='A new local output directory.')
    args = parser.parse_args()
    resource = args.resources if args.resources else args.game_dir / 'Ignorance_Data/resources.assets'
    try:
        deliver(resource.resolve(), args.font_file.resolve() if args.font_file else None, args.output.resolve())
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Build failed: {exc}\n')
