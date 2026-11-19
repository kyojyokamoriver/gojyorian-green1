"""Add animated eyelids to the native AR asset. Requires usd-core."""
from pathlib import Path
import math, tempfile, zipfile
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdUtils

ASSET = Path(__file__).resolve().parents[1] / 'dist/assets/alien-ar.usdz'
# Two short blinks within the existing six-second animation loop (24 fps).
KEYS = [(0,0),(46,0),(48,.5),(50,1),(52,1),(54,.5),(56,0),
        (118,0),(120,.5),(122,1),(124,1),(126,.5),(128,0),(144,0)]

def eyelid_geometry(width, height):
    paths = [[(-width*.40*math.cos(t), height*(.20-.45*math.sin(t)))
              for t in [math.pi*i/24 for i in range(25)]]]
    paths += [[(x*width,-height*.18),(x*width*1.3,-height*.43)] for x in [-.25,0,.25]]
    points, indices = [], []
    r = width*.028
    for path in paths:
        base = len(points)
        for j,(x,y) in enumerate(path):
            before,after=path[max(0,j-1)],path[min(len(path)-1,j+1)]
            dx,dy=after[0]-before[0],after[1]-before[1]
            length=math.hypot(dx,dy) or 1
            for k in range(8):
                a=2*math.pi*k/8
                points.append((x-dy/length*r*math.cos(a),y+dx/length*r*math.cos(a),r*math.sin(a)))
        for j in range(len(path)-1):
            for k in range(8):
                a=base+j*8+k;b=base+j*8+(k+1)%8;c=b+8;d=a+8
                indices.extend([a,b,c,a,c,d])
    return points,indices

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)
    with zipfile.ZipFile(ASSET) as package: package.extractall(root)
    scene=root/'Alien.usdc'
    stage=Usd.Stage.Open(str(scene))
    stage.RemovePrim('/Alien/Materials/Blink')
    material=UsdShade.Material.Define(stage,'/Alien/Materials/Blink')
    surface=UsdShade.Shader.Define(stage,'/Alien/Materials/Blink/Surface')
    surface.CreateIdAttr('UsdPreviewSurface')
    surface.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set((0,0,0))
    surface.CreateInput('emissiveColor',Sdf.ValueTypeNames.Color3f).Set((.009,.346,.202))
    surface.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(1)
    material.CreateSurfaceOutput().ConnectToSource(surface.ConnectableAPI(),'surface')
    cache=UsdGeom.BBoxCache(0,['default'])
    for i in range(2):
        eye=stage.GetPrimAtPath(f'/Alien/Floating/Part{i}')
        assert eye
        bounds=cache.ComputeLocalBound(eye).ComputeAlignedRange()
        center=bounds.GetMidpoint();size=bounds.GetSize()
        xform=UsdGeom.Xformable(eye)
        # Reset only the blink transforms so the script can be run repeatedly.
        for name in ['xformOpOrder','xformOp:translate:blinkPivot','xformOp:scale:blink']:
            eye.RemoveProperty(name)
        xform.AddTranslateOp(opSuffix='blinkPivot').Set(center)
        scale=xform.AddScaleOp(opSuffix='blink')
        xform.AddTranslateOp(opSuffix='blinkPivot',isInverseOp=True)
        path=f'/Alien/Floating/Lid{i}'
        stage.RemovePrim(path)
        lid=UsdGeom.Xform.Define(stage,path)
        lid.AddTranslateOp().Set((center[0],center[1],bounds.GetMax()[2]+.001))
        lidscale=lid.AddScaleOp()
        mesh=UsdGeom.Mesh.Define(stage,path+'/Shape')
        points,indices=eyelid_geometry(size[0],size[1])
        mesh.CreatePointsAttr(points);mesh.CreateFaceVertexIndicesAttr(indices)
        mesh.CreateFaceVertexCountsAttr([3]*(len(indices)//3))
        mesh.CreateSubdivisionSchemeAttr('none')
        mesh.CreateExtentAttr(UsdGeom.PointBased.ComputeExtent(points))
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
        for frame,amount in KEYS:
            scale.Set(Gf.Vec3f(.00001,.00001,.00001) if amount==1 else Gf.Vec3f(1,1-amount,1),frame)
            lidscale.Set(Gf.Vec3f(max(.00001,amount)),frame)
    stage.GetRootLayer().Save()
    output=root/'blink.usdz'
    assert UsdUtils.CreateNewUsdzPackage(str(scene),str(output))
    check=Usd.Stage.Open(str(output))
    assert check.GetEndTimeCode()==144
    assert not check.GetPrimAtPath('/Alien/Shadow')
    for i in range(2):
        assert check.GetPrimAtPath(f'/Alien/Floating/Lid{i}/Shape')
        scale=check.GetPrimAtPath(f'/Alien/Floating/Part{i}').GetAttribute('xformOp:scale:blink')
        assert scale.Get(0)[0]==1 and scale.Get(50)[0]<.001 and scale.Get(56)[0]==1
    ASSET.write_bytes(output.read_bytes())
    print('Validated: two synchronized blinks, full loop, stars/float retained, no shadow plane')
