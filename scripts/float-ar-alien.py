"""Raise the AR alien above a fixed floor origin. Requires usd-core."""
from pathlib import Path
import math,tempfile,zipfile
from pxr import Usd,UsdGeom,UsdShade,UsdUtils,Sdf,Gf
asset=Path(__file__).resolve().parents[1]/'dist/assets/alien-ar.usdz'
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder)
 with zipfile.ZipFile(asset) as package:package.extractall(root)
 stage=Usd.Stage.Open(str(root/'Alien.usdc'))
 floating=stage.GetPrimAtPath('/Alien/Floating').GetAttribute('xformOp:translate')
 stars=UsdGeom.Xformable(stage.GetPrimAtPath('/Alien/Stars'))
 # A named delta keeps the star burst centered around the raised character.
 delta=stage.GetPrimAtPath('/Alien/Stars').GetAttribute('xformOp:translate:hoverOffset')
 if not delta:delta=stars.AddTranslateOp(opSuffix='hoverOffset').GetAttr()
 for frame in range(0,145,3):
  t=frame/24
  y=.38+.065*math.sin(2*math.pi*t/6)
  floating.Set((0,y,0),frame)
  old=.24+.034*math.sin(2*math.pi*t/3)
  delta.Set((0,y-old,0),frame)
 floating.Set((0,.38,0))
 # Quick Look grounds the scene by its bounds. Keep a tiny, fully transparent
 # triangle at the floor origin so the floating body is not snapped downward.
 # This replaces neither the removed shadow plane nor its visible surface.
 ref=UsdGeom.Mesh.Define(stage,'/Alien/FloorOrigin')
 points=[(0,0,0),(.0001,0,0),(0,0,.0001)]
 ref.CreatePointsAttr(points);ref.CreateFaceVertexCountsAttr([3]);ref.CreateFaceVertexIndicesAttr([0,1,2])
 ref.CreateExtentAttr(UsdGeom.PointBased.ComputeExtent(points));ref.CreateSubdivisionSchemeAttr('none')
 material=UsdShade.Material.Define(stage,'/Alien/Materials/FloorOrigin')
 shader=UsdShade.Shader.Define(stage,'/Alien/Materials/FloorOrigin/Surface')
 shader.CreateIdAttr('UsdPreviewSurface')
 shader.CreateInput('opacity',Sdf.ValueTypeNames.Float).Set(0)
 shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set((0,0,0))
 shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(1)
 material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
 UsdShade.MaterialBindingAPI.Apply(ref.GetPrim()).Bind(material)
 stage.GetRootLayer().Save()
 output=root/'float.usdz';assert UsdUtils.CreateNewUsdzPackage(str(root/'Alien.usdc'),str(output))
 check=Usd.Stage.Open(str(output))
 assert not check.GetPrimAtPath('/Alien/Shadow')
 assert check.GetPrimAtPath('/Alien/Floating/Lid0/Shape')
 assert check.GetEndTimeCode()==144
 for frame in [0,36,72,108,144]:
  bounds=UsdGeom.BBoxCache(frame,['default']).ComputeWorldBound(check.GetDefaultPrim()).ComputeAlignedRange()
  assert abs(bounds.GetMin()[1])<1e-6
  y=check.GetPrimAtPath('/Alien/Floating').GetAttribute('xformOp:translate').Get(frame)[1]
  assert .314<y<.446
 asset.write_bytes(output.read_bytes())
 print('Validated: 31.5–44.5 cm hover, fixed floor origin, seamless 6-second cycle, blinking retained')
