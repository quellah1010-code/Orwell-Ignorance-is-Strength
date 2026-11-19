"""Let TMP lay out the aptitude highlights with the translated option text."""
import re
import struct

import attrs

from aptitude_patch import load, save_checked
from orwell_resources import encode_string


OPTION = re.compile(r'<link="([^"]+)"><color=#[0-9a-fA-F]{6}>([^<>]+)</color></link>')


def pointer(pid):
    return {'m_FileID': 0, 'm_PathID': pid}


def component(pid):
    return {'component': pointer(pid)}


def owner(raw):
    return struct.unpack_from('<q', raw, 4)[0]


def stretch(rect, parent, obj, children, pivot):
    rect.update(m_GameObject=pointer(obj), m_Father=pointer(parent), m_Children=children,
                m_AnchorMin={'x': 0., 'y': 0.}, m_AnchorMax={'x': 1., 'y': 1.},
                m_Pivot=pivot, m_AnchoredPosition={'x': 0., 'y': 0.},
                m_LocalPosition={'x': 0., 'y': 0., 'z': 0.}, m_SizeDelta={'x': 0., 'y': 0.})
    return rect


def scene_text(raw, offset, old, new):
    field = encode_string(old)
    if raw[offset:offset + len(field)] != field:
        raise ValueError('Option label does not contain the translated text.')
    return raw[:offset] + encode_string(new) + raw[offset + len(field):]


def background_label(raw, old_id, new_id, new_owner):
    # TMP 1.x serializes a reference to itself in TMP_TextInfo and an eight-slot
    # cache of submeshes. A new label must build its own fallback-font meshes.
    result = bytearray(raw)
    self_ref = struct.pack('<iq', 0, old_id)
    if result[-208:-196] != self_ref or struct.unpack_from('<i', result, len(result)-128)[0] != 8:
        raise ValueError('Unexpected TMP label cache layout.')
    struct.pack_into('<q', result, 4, new_owner)
    result[-208:-196] = struct.pack('<iq', 0, new_id)
    result[-124:-28] = bytes(96)
    if result[60] != 1:
        raise ValueError('Expected a raycastable source label.')
    result[60] = 0
    return bytes(result)


def task_buttons(asset, game_object, links):
    buttons = {}
    for item in game_object['m_Component']:
        obj = asset.objects[item['component']['m_PathID']]
        raw = obj.get_raw_data()
        if obj.type.name != 'MonoBehaviour' or struct.unpack_from('<iq', raw, 16) != (1, 650):
            continue
        names = [name for name in links if encode_string(name) in raw]
        if len(names) != 1 or names[0] in buttons:
            raise ValueError('Unexpected or duplicate aptitude link ID.')
        # The final serialized field is a Button list, one entry per original
        # English line fragment. TMP can render all wrapped lines in one mark.
        end = len(raw)
        selected = []
        while end >= 12:
            file_id, pid = struct.unpack_from('<iq', raw, end - 12)
            candidate = asset.objects.get(pid)
            if (file_id or candidate is None or candidate.type.name != 'MonoBehaviour'
                    or struct.unpack_from('<iq', candidate.get_raw_data(), 16) != (1, 73)):
                break
            selected.append(pid)
            end -= 12
        if not selected or struct.unpack_from('<i', raw, end - 4)[0] != len(selected):
            raise ValueError('Invalid aptitude background button list.')
        buttons[names[0]] = (obj.path_id, end - 4, selected[::-1])
    if set(buttons) != set(links):
        raise ValueError('Link and button IDs differ.')
    return buttons


def patch_highlights(content, aptitude):
    asset, expected = load(content)
    objects = asset.objects

    def clone(template):
        pid = max(objects) + 1
        objects[pid] = attrs.evolve(objects[template], path_id=pid, data=None)
        return pid

    def write(pid, raw):
        expected[pid] = raw
        objects[pid].set_raw_data(raw)

    def write_tree(pid, tree):
        write(pid, objects[pid].save_typetree(tree))

    report = {}
    for entry in aptitude['scene']:
        label = entry['path_id']
        original = entry['target']
        if '<link=' not in original:
            continue
        lines = original.split('\r\n')
        matches = [OPTION.fullmatch(line) for line in lines]
        if not all(matches):
            raise ValueError('Unexpected layout markup in the aptitude options.')
        links = {match[1]: match[2] for match in matches}
        if len(links) != len(lines):
            raise ValueError('Duplicate aptitude option.')
        raw = expected[label]
        text_go = owner(raw)
        go = objects[text_go].read_typetree()
        rect_id, renderer = [item['component']['m_PathID'] for item in go['m_Component'][:2]]
        rect = objects[rect_id].read_typetree()
        parent = rect['m_Father']['m_PathID']
        siblings = objects[parent].read_typetree()
        buttons = task_buttons(asset, go, links)
        group_go, group_rect = clone(text_go), clone(rect_id)
        group_children = []
        foreground = '<size=125%>' + original + '</size>'
        write(label, scene_text(raw, entry['offset'], original, foreground))

        for name, (chunk, list_offset, cached_buttons) in buttons.items():
            button = cached_buttons[0]
            for redundant in cached_buttons[1:]:
                old_box = objects[owner(expected[redundant])].read_typetree()
                if old_box['m_IsActive']:
                    raise ValueError('Expected an inactive cached line fragment.')
            write(chunk, expected[chunk][:list_offset] + struct.pack('<iiq', 1, 0, button))
            button_raw = expected[button]
            box_go = owner(button_raw)
            box = objects[box_go].read_typetree()
            box_rect = box['m_Component'][0]['component']['m_PathID']
            box_transform = objects[box_rect].read_typetree()
            if box_transform['m_Father'] != pointer(parent) or box_transform['m_Children']:
                raise ValueError('Unexpected background button hierarchy.')
            image_file, old_image = struct.unpack_from('<iq', button_raw, len(button_raw)-12)
            if image_file or old_image not in [x['component']['m_PathID'] for x in box['m_Component']]:
                raise ValueError('Background button has an unexpected target graphic.')

            # Each selectable tints just its own mark, rebuilding with the same
            # font, text, line breaks and parent rectangle as the visible label.
            layer_go, layer_rect = clone(text_go), clone(rect_id)
            layer_renderer, layer_text = clone(renderer), clone(label)
            spans = ['<mark=#FFFFFFFF>' + text + '</mark>' if key == name else text
                     for key, text in links.items()]
            markup = '<size=125%><color=#FFFFFF00>' + '\r\n'.join(spans) + '</color></size>'
            layer = background_label(raw, label, layer_text, layer_go)
            write(layer_text, scene_text(layer, entry['offset'], original, markup))
            write(layer_renderer, struct.pack('<iq', 0, layer_go))
            write_tree(layer_go, dict(go, m_Name='Highlight ' + name, m_IsActive=True,
                                      m_Component=[component(i) for i in (layer_rect, layer_renderer, layer_text)]))
            write_tree(layer_rect, stretch(dict(rect), box_rect, layer_go, [], rect['m_Pivot']))
            write_tree(box_rect, stretch(box_transform, group_rect, box_go, [pointer(layer_rect)], rect['m_Pivot']))
            image = bytearray(expected[old_image])
            image[12] = 0  # Disable the precomputed English rectangle.
            write(old_image, bytes(image))
            write(button, button_raw[:-12] + struct.pack('<iq', 0, layer_text))
            siblings['m_Children'].remove(pointer(box_rect))
            group_children.append(pointer(box_rect))

        index = siblings['m_Children'].index(pointer(rect_id))
        siblings['m_Children'][index] = pointer(group_rect)
        write_tree(parent, siblings)
        write_tree(group_go, dict(go, m_Name='Aptitude options layout', m_IsActive=True,
                                  m_Component=[component(group_rect)]))
        write_tree(group_rect, dict(rect, m_GameObject=pointer(group_go), m_Children=group_children+[pointer(rect_id)]))
        write_tree(rect_id, stretch(dict(rect), group_rect, text_go, rect['m_Children'], rect['m_Pivot']))
        report[str(label)] = list(links)
    return save_checked(asset, expected), {'text_mesh_highlights': report, 'runtime_tested': False}
