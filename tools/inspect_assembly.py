"""Read managed metadata and CIL; never execute the input assembly."""
import argparse
import re

import dnfile
from dncil.cil.body.reader import read_method_body_from_bytes
from dncil.clr.token import Token

parser = argparse.ArgumentParser()
parser.add_argument('assembly')
parser.add_argument('pattern')
args = parser.parse_args()
pe = dnfile.dnPE(args.assembly)
pattern = re.compile(args.pattern, re.I)
owners = {}
for t in pe.net.mdtables.TypeDef.rows:
    owner = str(t.TypeNamespace) + '.' + str(t.TypeName)
    for m in t.MethodList:
        owners[(6, m.row_index)] = owner
    for f in t.FieldList:
        owners[(4, f.row_index)] = owner


def resolve(value):
    if not isinstance(value, Token):
        return str(value)
    token = value.value
    table, index = token >> 24, token & 0xffffff
    if table == 0x70:
        return repr(pe.net.user_strings.get(index).value)
    try:
        row = pe.net.mdtables.tables[table].rows[index - 1]
        if table in (1, 2):
            return str(row.TypeNamespace) + '.' + str(row.TypeName)
        if table in (4, 6):
            return owners[(table, index)] + '::' + str(row.Name)
        if table == 10:
            parent = row.Class.row
            cls = getattr(parent, 'TypeName', getattr(parent, 'Name', '?'))
            return str(cls) + '::' + str(row.Name)
        if table == 43:
            return str(row.Method.row.Name) + '<generic>'
        return f'token({token:#x})'
    except (KeyError, AttributeError, IndexError):
        return f'token({token:#x})'


for t in pe.net.mdtables.TypeDef.rows:
    name = str(t.TypeNamespace) + '.' + str(t.TypeName)
    if not pattern.search(name):
        continue
    print('\nTYPE', name)
    print('FIELDS', ', '.join(str(f.row.Name) for f in t.FieldList))
    for m in t.MethodList:
        method = m.row
        if not method.Rva:
            continue
        print('\nMETHOD', name + '::' + str(method.Name), f'index={m.row_index}')
        try:
            body = read_method_body_from_bytes(pe.get_data(method.Rva))
            for instruction in body.instructions:
                print(f'  {instruction.offset:04x}: {instruction.opcode.name:14} {resolve(instruction.operand) if instruction.operand is not None else ""}')
        except Exception as exc:
            print('  ERROR', type(exc).__name__, str(exc))
