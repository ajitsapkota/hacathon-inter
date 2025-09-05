import xml.etree.ElementTree as ET


def load_tmx_map(tmx_file):
    tree = ET.parse(tmx_file)
    root = tree.getroot()
    map_width = int(root.get('width'))
    map_height = int(root.get('height'))
    tile_width = int(root.get('tilewidth'))
    tile_height = int(root.get('tileheight'))

    layers = []
    for layer in root.findall('layer'):
        layer_data = {
            'name': layer.get('name'),
            'width': int(layer.get('width')),
            'height': int(layer.get('height')),
            'data': []
        }
        data_elem = layer.find('data')
        if data_elem is not None:
            csv_data = data_elem.text.strip()
            layer_data['data'] = [int(x) for x in csv_data.split(',') if x.strip()]
        layers.append(layer_data)

    return {
        'width': map_width,
        'height': map_height,
        'tilewidth': tile_width,
        'tileheight': tile_height,
        'layers': layers  # list of dicts
    }
def extract_ground_layer(map_data):
    """Merge 'ground' and 'ground1' into one solid ground layer."""
    width = map_data['width']
    height = map_data['height']
    layers = map_data['layers']
    solid_layer_names = ['ground', 'ground1']

    solid_grid = [[0 for _ in range(width)] for _ in range(height)]

    for name in solid_layer_names:
        if name in layers:
            for y in range(height):
                for x in range(width):
                    if layers[name][y][x] != 0:
                        solid_grid[y][x] = 1

    return solid_grid

def extract_background_layer(map_data):
    """Merge 'background' and 'background1' into one background layer."""
    width = map_data['width']
    height = map_data['height']
    layers = map_data['layers']
    background_names = ['background', 'background1']

    bg_grid = [[0 for _ in range(width)] for _ in range(height)]

    for name in background_names:
        if name in layers:
            for y in range(height):
                for x in range(width):
                    if layers[name][y][x] != 0:
                        bg_grid[y][x] = 1

    return bg_grid
