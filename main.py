from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
from PIL import Image
import random

app = Ursina()


corner_text = Text(
    text="Minecraft in Python",
    font='Minecraft-Font.otf', # Specify the .otf font file name
    position=(-.88, .5), # Position near the top-left corner
    scale=0.8, # Adjust scale as needed
    origin=(-.5, .6), # Ensures alignment from the top-left point
    wordwrap=50 # Optional: wraps text after a certain number of characters for readability
)

# Block textures (Ursina + Pillow)
block_textures, block_images = {}, {}
names = ['grass','brick','cobblestone','diamond','oak_log','oak_planks','sand','stone']
for i, name in enumerate(names, start=1):
    block_textures[i] = load_texture(f'{name}.png')
    block_images[i] = Image.open(f'{name}.png').convert('RGBA')

current_block_type = 1
hotbar_textures = {i: load_texture(f'hotbar_{i}.png') for i in range(1,10)}
hotbar_bg = Entity(model='quad', texture=hotbar_textures[1], parent=camera.ui, scale=(0.55,0.07), position=(0,-0.45))

# --- Sounds ---
grass_sounds = [Audio(f'Grass_dig{i}.ogg', autoplay=False) for i in range(1,5)]
stone_sounds = [Audio(f'Stone_dig{i}.ogg', autoplay=False) for i in range(1,5)]
sand_sounds  = [Audio(f'Sand_dig{i}.ogg',  autoplay=False) for i in range(1,5)]
wood_sounds  = [Audio(f'Wood_dig{i}.ogg',  autoplay=False) for i in range(1,5)]

block_sounds = {
    1: grass_sounds,   # grass
    2: stone_sounds,   # brick
    3: stone_sounds,   # cobblestone
    4: stone_sounds,   # diamond
    5: wood_sounds,    # oak log
    6: wood_sounds,   # oak planks
    7: sand_sounds,    # sand
    8: stone_sounds,   # stone
}

# Cube mesh
def build_cube_mesh():
    verts, uvs, tris = [], [], []
    def add_face(v, uv):
        s = len(verts); verts.extend(v); uvs.extend(uv)
        tris.extend([(s,s+1,s+2),(s,s+2,s+3)])
    top_uvs=[(0,2/3),(1,2/3),(1,1),(0,1)]
    side_uvs=[(0,1/3),(1,1/3),(1,2/3),(0,2/3)]
    bottom_uvs=[(0,0),(1,0),(1,1/3),(0,1/3)]
    add_face([Vec3(-.5,.5,.5),Vec3(.5,.5,.5),Vec3(.5,.5,-.5),Vec3(-.5,.5,-.5)],top_uvs)
    add_face([Vec3(-.5,-.5,-.5),Vec3(.5,-.5,-.5),Vec3(.5,-.5,.5),Vec3(-.5,-.5,.5)],bottom_uvs)
    add_face([Vec3(-.5,-.5,.5),Vec3(.5,-.5,.5),Vec3(.5,.5,.5),Vec3(-.5,.5,.5)],side_uvs)
    add_face([Vec3(.5,-.5,-.5),Vec3(-.5,-.5,-.5),Vec3(-.5,.5,-.5),Vec3(.5,.5,-.5)],side_uvs)
    add_face([Vec3(-.5,-.5,-.5),Vec3(-.5,-.5,.5),Vec3(-.5,.5,.5),Vec3(-.5,.5,-.5)],side_uvs)
    add_face([Vec3(.5,-.5,.5),Vec3(.5,-.5,-.5),Vec3(.5,.5,-.5),Vec3(.5,.5,.5)],side_uvs)
    cube=Mesh(vertices=verts,uvs=uvs,triangles=tris,mode='triangle'); cube.generate(); return cube

hand_block = Entity(model=build_cube_mesh(), texture=block_textures[current_block_type],
                    parent=camera.ui, scale=(0.18,0.18,0.18), position=(0.65,-0.35), rotation=(30,-30,0))

def make_block(pos=(0,0,0), tex=block_textures[1]):
    return Entity(model=build_cube_mesh(), texture=tex, position=pos, parent=scene, collider='box', double_sided=True)

# Terrain
noise = PerlinNoise(octaves=3, seed=12345)
for x in range(20):
    for z in range(20):
        h = int(noise([x/10,z/10])*5+2)
        for y in range(h+1):
            make_block((x,y,z), block_textures[1] if y==h else block_textures[8])

player = FirstPersonController(); player.y=10

# Outline cube
def make_outline():
    edges=[((-0.5,-0.5,-0.5),(0.5,-0.5,-0.5)),((0.5,-0.5,-0.5),(0.5,-0.5,0.5)),((0.5,-0.5,0.5),(-0.5,-0.5,0.5)),
           ((-0.5,-0.5,0.5),(-0.5,-0.5,-0.5)),((-0.5,0.5,-0.5),(0.5,0.5,-0.5)),((0.5,0.5,-0.5),(0.5,0.5,0.5)),
           ((0.5,0.5,0.5),(-0.5,0.5,0.5)),((-0.5,0.5,0.5),(-0.5,0.5,-0.5)),((-0.5,-0.5,-0.5),(-0.5,0.5,-0.5)),
           ((0.5,-0.5,-0.5),(0.5,0.5,-0.5)),((0.5,-0.5,0.5),(0.5,0.5,0.5)),((-0.5,-0.5,0.5),(-0.5,0.5,0.5))]
    p=Entity(visible=False)
    for s,e in edges: Entity(model=Mesh(vertices=[Vec3(*s),Vec3(*e)],mode='line'),color=color.black,parent=p,scale=1.01)
    return p
outline_entity=make_outline()

# Clouds
clouds=[]; cloud_noise=PerlinNoise(octaves=2,seed=999)
for i in range(-5,6):
    for j in range(-5,6):
        v=cloud_noise([i/5,j/5])
        if v>0.2:
            clouds.append(Entity(model='quad',position=(i*10,20+v*10,j*10),scale=(8,4),rotation_x=90,color=color.white,alpha=0.6))

# Particles
particles=[]
def spawn_particles(block_entity):
    tex=block_entity.texture; bid=None
    for i,t in block_textures.items():
        if t==tex: bid=i; break
    if not bid: return
    img=block_images[bid]; w,h=img.size; px=img.load()
    for i in range(0,w,8):
        for j in range(0,h,8):
            r,g,b,a=px[i,j]
            if a==0: continue
            p=Entity(model='quad',color=color.rgba(r,g,b,a),position=block_entity.position,scale=0.05,double_sided=True)
            p.velocity=Vec3(random.uniform(-0.1,0.1),random.uniform(0.1,0.3),random.uniform(-0.1,0.1))
            particles.append(p)

def update():
    if mouse.hovered_entity and hasattr(mouse.hovered_entity,'texture'):
        outline_entity.position=mouse.hovered_entity.position; outline_entity.visible=True
    else: outline_entity.visible=False
    for c in clouds: c.x+=0.01; c.alpha=0.5+cloud_noise([c.x/50,c.z/50])*0.3
    camera.fog_color=color.rgb(200,220,255); camera.fog_density=0.02
    for p in particles[:]:
        p.position+=p.velocity; p.velocity*=0.95; p.alpha-=0.02
        if p.alpha<=0: destroy(p); particles.remove(p)

def input(key):
    global current_block_type, hand_block

    # Number keys still work
    if key in ['1','2','3','4','5','6','7','8','9']:
        current_block_type = int(key)

    # Scroll wheel support
    if key == 'scroll up':
        current_block_type += 1
        if current_block_type > 9:
            current_block_type = 1
    if key == 'scroll down':
        current_block_type -= 1
        if current_block_type < 1:
            current_block_type = 9

    # Update hotbar and hand block preview
    hotbar_bg.texture = hotbar_textures[current_block_type]
    if hand_block:
        destroy(hand_block)
    hand_block = None if current_block_type == 9 else Entity(
        model=build_cube_mesh(), texture=block_textures[current_block_type],
        parent=camera.ui, scale=(0.18,0.18,0.18),
        position=(0.65,-0.35), rotation=(30,-30,0)
    )

    # Mining and placing
    if mouse.hovered_entity:
        if key == 'left mouse down':
            spawn_particles(mouse.hovered_entity)
            bid = next((i for i,t in block_textures.items() if t == mouse.hovered_entity.texture), None)
            if bid and bid in block_sounds:
                random.choice(block_sounds[bid]).play()
            destroy(mouse.hovered_entity)

        if key == 'right mouse down' and current_block_type != 9:
            new_block = make_block(mouse.hovered_entity.position + mouse.normal,
                                   block_textures[current_block_type])
            if current_block_type in block_sounds:
                random.choice(block_sounds[current_block_type]).play()
sky = Sky(texture='skybox.png') 
app.run()

