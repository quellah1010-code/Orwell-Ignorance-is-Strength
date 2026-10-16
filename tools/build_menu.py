"""Build the 0.2 menu/profile preview from local original game files."""
import argparse
import csv
import json
import shutil
import zipfile
from pathlib import Path

from build_preview import ROOT, LICENSE_SHA256, translation_rows, verified_font
from build_preview_font import build as build_font
from menu_patch import digest, patch_assembly, patch_scene
from orwell_resources import patch


def deliver(game_dir, resources, font, output):
    if output.exists():
        raise FileExistsError(f'Output already exists; choose a new --output directory: {output}')
    data = game_dir / 'Ignorance_Data'
    source = resources if resources else data / 'resources.assets'
    rows = translation_rows(source)
    mapping = json.loads((ROOT / 'translations/menu.zh-CN.json').read_text(encoding='utf-8'))
    if mapping['schema_version'] != 1:
        raise ValueError('Unsupported UI mapping version.')
    # Validate and patch in memory before creating output or downloading a font.
    scene, scene_report = patch_scene((data / 'level1').read_bytes(), mapping)
    assembly, assembly_report = patch_assembly((data / 'Managed/Assembly-CSharp.dll').read_bytes(), mapping)
    license_path = ROOT / 'licenses/Noto-OFL.txt'
    if digest(license_path.read_bytes()) != LICENSE_SHA256:
        raise ValueError('Open font license checksum differs.')
    font = verified_font(font)
    output.mkdir(parents=True)
    table = output / 'dialogue-internal.csv'
    with table.open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    intermediate = output / 'text-only-internal.assets'
    patch(source, table, intermediate)
    package = output / 'package'
    patched = package / 'Ignorance_Data/resources.assets'
    texts = [row['target'] for group in ('scene', 'dll') for row in mapping[group]]
    build_font(source, intermediate, font, table, patched, extra_texts=texts, atlas_size=4096)
    (package / 'Ignorance_Data/level1').write_bytes(scene)
    dll = package / 'Ignorance_Data/Managed/Assembly-CSharp.dll'
    dll.parent.mkdir(parents=True)
    dll.write_bytes(assembly)
    report_path = package / 'validation.json'
    font_report = json.loads(report_path.read_text())
    files = ['Ignorance_Data/resources.assets', 'Ignorance_Data/level1', 'Ignorance_Data/Managed/Assembly-CSharp.dll']
    hashes = {name: digest((package / name).read_bytes()) for name in files}
    report = {
        'version': '0.2', 'scope': mapping['scope'], 'source_hashes': mapping['source_hashes'],
        'output_hashes': hashes, 'scene': scene_report, 'assembly': assembly_report,
        'font_and_dialogue': font_report, 'runtime_tested': False,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    shutil.copyfile(ROOT / 'docs/menu-install.txt', package / '先读我.txt')
    shutil.copyfile(license_path, package / 'FONT-LICENSE.txt')
    archive_path = output / 'orwell-zh-menu-0.2.zip'
    with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in [*files, 'validation.json', '先读我.txt', 'FONT-LICENSE.txt']:
            info = zipfile.ZipInfo('orwell-zh-menu-0.2/' + name, date_time=(2026, 10, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (package / name).read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC verification failed.')
        for name, expected in hashes.items():
            if digest(archive.read('orwell-zh-menu-0.2/' + name)) != expected:
                raise ValueError(f'Archived resource verification failed: {name}')
    print(f'Local ZIP: {archive_path}')
    print(f'ZIP SHA-256: {digest(archive_path.read_bytes())}')
    print('Menu/profile preview built. Back up all THREE original files before manual installation.')
    print('Windows rendering and gameplay remain untested. Keep generated game files local.')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, required=True)
    parser.add_argument('--resources', type=Path, help='Original resources.assets backup, if 0.1 is already installed.')
    parser.add_argument('--font-file', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/menu-0.2')
    args = parser.parse_args()
    try:
        deliver(args.game_dir.resolve(), args.resources.resolve() if args.resources else None,
                args.font_file.resolve() if args.font_file else None, args.output.resolve())
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Build failed: {exc}\nUse original game files; --resources can point to your original backup.\n')
