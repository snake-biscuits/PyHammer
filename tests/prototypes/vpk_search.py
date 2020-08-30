import vpk
from io import open as fopen

class VPKSearchable(vpk.VPK):
    def __init__(self, vpk_path, read_header_only=True, path_enc='utf-8', fopen=fopen):
        super().__init__(vpk_path, read_header_only=read_header_only, path_enc=path_enc, fopen=fopen)

        # Path for Sound. Unless set, it will default to same path
        self.searchSoundPath = vpk_path

        # Filter for file name
        self.filefilter = []

        self.shaderfilter = []
        # List of shaders
        # Aftershock
        # Cable
        # Character
        # Core 
        # DecalModulate 
        # EyeRefract 
        # Eyes 
        # Infected 
        # JellyFish
        # Lightmapped_4wayBlend
        # LightmappedGeneric
        # LightmappedReflective
        # LightmappedTwoTexture
        # Modulate
        # MonitorScreen
        # MultiBlend
        # Patch
        # Pyro_vision
        # Refract
        # Sky
        # SplineRope
        # SpriteCard
        # Subrect
        # Teeth
        # UnlitGeneric
        # UnlitTwoTexture
        # VertexLitGeneric
        # VolumeCloud
        # VortWarp
        # Water
        # WindowImposter
        # Wireframe
        # WorldTwoTextureBlend
        # WorldVertexTransition

        #What kind of prop can the model be?
        self.modelFilter = []
        #---------------------------------------------------------------------------------
        #                   \   prop_detail    \   prop_static    \ prop_dynamic \    prop_physics    \   prop_ragdoll
        # $staticprop       \   Y              \   Y              \ Optional     \    Optional        \   N
        # prop_data         \   N              \   N              \ N            \    Y               \   Y
        # $collisionjoints  \   N              \   N              \ Optional     \    N               \   Y
        # $collsionmodel    \   N              \   Optional       \ Optional     \    Y               \   N

        # Notes: "Yes" or "No" means that the prop may be removed from the game, or otherwise not work if done incorrectly. 
        # "Optional" means that the code will work and is usually a good idea. 

        # mdl file format
        # int 
        # int 
        # int 
        # char 
        # int 
        # Vector (12 bytes each)
        # Vector 
        # Vector 
        # Vector 
        # Vector 
        # Vector 
        # int flags <--- Binary flags in little-endian order. 
		#               ex (00000001,00000000,00000000,11000000) means flags for position 0, 30, and 31 are set. 

        # model flags: int flag at 
        # $staticprop is 4th position of the flag in mdl. (positions starts from 0)

        # or just use https://github.com/maxdup/mdl-tools 

    def hasFilter(self):
        if (self.shaderfilter.length == 0) and ():
            return False
        else:
            return True

    def search(self, keyword):
        """Returns VPKFile array"""
        foundnames = []
        for filename in self:
            if (filename[-3:] in filefilter) and (keyword in filename):
                foundnames.append(filename)

        outputarray = []
        if hasFilter():
            pass

        for path in foundnames:
            outputarray.append(self.get_file(path))

    def setShaderFilter(self, *kwargs):
        """Sets filters for Material Searching"""
        self.filefilter = []
        self.filefilter.append(kwargs.get("types", None))
        self.shaderfilter = []
        self.shaderfilter.append(kwargs.get("shaders", None))

class MDLSimple:
    #Simple MDL parser just to check which type of prop it can be
    def __init__(self, vpkfile):
        #takes VPKFile class as parameter
        self.vpkfile = vpkfile
    
    def isStaticProp(self):
    # model flag byte location
    # 4*3 + 1*64 + 12*6 = 148
    #.seek(148)
    # flag is int
    #.read(4)
    # position for $staticprop is 4
        pass

    def isPropData(self):
        pass

    def isCollisionJoints(self):
        #Does ragdollconstraint in .phy define collision joint?
        pass

    def isCollisionModel(self):
        #does the model have .phy?
        #should this be determined here???
        pass

    def propTypes(self):
        propTypeList = []
        if self.isStaticProp() and not self.isPropData() and not self.isCollisionJoints() and not self.isCollisionModel():
            propTypeList.append("prop_detail")
        if not self.isStaticProp() and self.isPropData() and self.isCollisionJoints() and not self.isCollisionModel():
            propTypeList.append("prop_ragdoll")
        if self.isStaticProp() and not self.isPropData() and not self.isCollisionJoints():
            propTypeList.append("prop_static")
        if self.isPropData() and not self.isCollisionJoints() and self.isCollisionModel():
            propTypeList.append("prop_physics")
        if not self.isPropData():
            propTypeList.append("prop_dynamic")


def main():
    path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Team Fortress 2\\tf\\tf2_misc_dir.vpk"
    pak = VPKSearchable(path)
    pak.search("soldier")


if __name__ == "__main__":
    main()