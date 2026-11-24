"""Readable JSON: one grid row per line rather than one cell per line."""
import json

def config_text(data):
    if not isinstance(data,dict) or not isinstance(data.get('grid'),list):
        return json.dumps(data,indent=2)
    grid=',\n'.join('    '+json.dumps(row) for row in data['grid'])
    others=',\n'.join('  '+json.dumps(k)+': '+json.dumps(v) for k,v in data.items() if k!='grid')
    return '{\n  "grid": [\n'+grid+'\n  ]'+(',\n'+others if others else '')+'\n}'
