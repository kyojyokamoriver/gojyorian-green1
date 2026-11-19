"""Add a circular feathered floor shadow with no rectangular texture plane."""
from pathlib import Path
import tempfile,zipfile,math
from pxr import Usd,UsdGeom,UsdShade,UsdUtils,Sdf
asset=Path(__file__).resolve().parents[1]/'dist/assets/alien-ar.usdz'
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder)
 with zipfile.ZipFile(asset) as archive:archive.extractall(root)
 stage=Usd.Stage.Open(str(root/'Alien.usdc'))
 stage.RemovePrim('/Alien/SoftShadow');stage.RemovePrim('/Alien/Materials/SoftShadow')
 UsdGeom.Xform.Define(stage,'/Alien/SoftShadow')
 for band in range(24):
  inner=band/24;outer=(band+1)/24
  # Low-opacity black rings feather to transparent. No image or white surface.
  opacity=.29*math.exp(-((inner+outer)/2/.47)**2)*(1-outer**6)
  material=UsdShade.Material.Define(stage,f'/Alien/Materials/SoftShadow/Band{band}')
  shader=UsdShade.Shader.Define(stage,f'/Alien/Materials/SoftShadow/Band{band}/Surface')
  shader.CreateIdAttr('UsdPreviewSurface')
  shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set((0,0,0))
  shader.CreateInput('specularColor',Sdf.ValueTypeNames.Color3f).Set((0,0,0))
  shader.CreateInput('useSpecularWorkflow',Sdf.ValueTypeNames.Int).Set(1)
  shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(1)
  shader.CreateInput('opacity',Sdf.ValueTypeNames.Float).Set(opacity)
  material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
  points=[];indices=[]
  for r in [inner,outer]:
   for i in range(64):
    a=i*2*math.pi/64;points.append((.29*r*math.cos(a),.001,.235*r*math.sin(a)))
  for i in range(64):
   j=(i+1)%64
   indices.extend([i,j,64+j,i,64+j,64+i])
  mesh=UsdGeom.Mesh.Define(stage,f'/Alien/SoftShadow/Band{band}')
  mesh.CreatePointsAttr(points);mesh.CreateFaceVertexCountsAttr([3]*(len(indices)//3))
  mesh.CreateFaceVertexIndicesAttr(indices);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateDoubleSidedAttr(True)
  mesh.CreateExtentAttr(UsdGeom.PointBased.ComputeExtent(points))
  UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
 stage.GetRootLayer().Save()
 output=root/'soft-shadow.usdz'
 assert UsdUtils.CreateNewUsdzPackage(str(root/'Alien.usdc'),str(output))
 check=Usd.Stage.Open(str(output))
 assert len(check.GetPrimAtPath('/Alien/SoftShadow').GetChildren())==24
 assert check.GetPrimAtPath('/Alien/Floating/Lid0/Shape')
 assert check.GetPrimAtPath('/Alien/Floating').GetAttribute('xformOp:translate').Get(0)[1]==.38
 assert not check.GetPrimAtPath('/Alien/Shadow')
 assert check.GetEndTimeCode()==144
 asset.write_bytes(output.read_bytes())
 print('Validated feathered oval shadow, no rectangular mesh/texture, hover and blink retained')
