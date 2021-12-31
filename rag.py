"""Register access code generator"""

from sys import argv
from typing import Tuple
from cmsis_svd.parser import SVDParser, SVDPeripheral, SVDRegister, SVDField
from subprocess import call

# FIXME: Brittle
# Returns list of str
def clean(elem: str):
    return elem.replace("[", "").replace("]", "").split("_")

def snake(*elems: Tuple[str]):
    return '_'.join([elem.lower() for elem in elems])

def camel(*elems: Tuple[str]):
    elems = [elem.capitalize() for elem in elems]
    elems[0] = elems[0].lower()
    return ''.join(elems)

# Necessary to avoid newline in expression part of f-string
def clean_desc(desc: str):
    return ' '.join(desc.replace('\n', '').split())

def title(*elems: Tuple[str]):
    return ''.join([elem.capitalize() for elem in elems])

if __name__ == '__main__':
    svd = SVDParser.for_xml_file(f'{argv[1]}/nrf51.svd')
    
    for p in svd.get_device().peripherals:
        p: SVDPeripheral = p
    
        with open(f'util.zig', 'w') as w:
            w.write("""pub fn isBitSet(val: u32, idx: usize) bool {
        if (idx > 31) {
            @panic("Bit index too large");
        }
        return (val >> idx) & 1 == 1;
    }""")
    
        with open(f'{snake(*clean(p.name))}.zig', 'w') as w:
            w.write(f'// Peripheral: {snake(*clean(p.name))}\n')
            w.write(f'// {clean_desc(p._description)}\n')
            w.write(f'const base_address = 0x{p._base_address:x};\n')
            w.write('\n')
    
            for r in p.registers:
                r: SVDRegister = r
    
                #if type(r.name) == str: # Somehow registers are being iterated over twice. Could be due to shared registers of periph with same ID?
                #    if r.name.startswith('TASK') or r.name.startswith('EVENT'):
                #        r.name = r.name.split('_')
    
                w.write(f'// {snake(*clean(r.name))}\n')
                w.write(f'// {clean_desc(r.description)}\n')
                w.write(f'const {snake(*clean(r.name))}_offset = 0x{r.address_offset:x};\n')
    
                if r._access != 'write-only':
                    w.write(f'pub inline fn {camel("read", *clean(r.name))}() u32 {{return @intToPtr(*volatile u32, base_address + {snake(*clean(r.name))}_offset).*;}}\n')
                if r._access != 'read-only':
                    w.write(f'pub inline fn {camel("write", *clean(r.name))}(val: u32) void {{@intToPtr(*volatile u32, base_address + {snake(*clean(r.name))}_offset).* = val;}}\n')
    
                
                w.write('\n')
    
                if len(r._fields) != 1: # If there are actually meaningful fields
                    for f in r._fields:
                        f: SVDField = f
    
                        w.write(f'// {snake(*clean(r.name))} -> {snake(*clean(f.name))}\n')
                        w.write(f'// {clean_desc(f.description)}\n')
                        w.write(f'const {snake(*clean(r.name), *clean(f.name))}_offset = 0x{f.bit_offset:x};\n')
    
                        # FIXME: Read usage field to disambiguate values
                        """
                        if field.enumerated_values is not None:
                            enum_name = field_label.replace('_', ' ').title().replace(' ', '')
    
                            w.write(f'const {enum_name} = enum {{\n')
                            for value in field.enumerated_values:
                                value: SVDEnumeratedValue = value
    
                                w.write(f'{value.name.lower()} = {value.value},\n')
    
                            w.write('};\n')
                        """
    
    
                        if r._access != 'write-only' and f.access != 'write-only':
                            w.write(f'pub inline fn {camel("read", *clean(r.name), *clean(f.name))}() u{f.bit_width} {{return @intToPtr(*volatile u{f.bit_width}, base_address + {snake(*clean(r.name))}_offset + {snake(*clean(r.name), *clean(f.name))}_offset).*;}}\n')
                        if r._access != 'read-only' and f.access != 'read-only':
                            w.write(f'pub inline fn {camel("write", *clean(r.name), *clean(f.name))}(val: u{f.bit_width}) void {{@intToPtr(*volatile u{f.bit_width}, base_address + {snake(*clean(r.name))}_offset + {snake(*clean(r.name), *clean(f.name))}_offset).* = val;}}\n')
    
                        w.write('\n')
    
        call(['zig', 'fmt', f'{snake(*clean(p.name))}.zig'])