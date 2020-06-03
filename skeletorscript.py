
#!BPY
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Skeletor_S3O SpringRTS (.s3o)",
    "author": "Beherith  <mysterme@gmail.com>",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "3D View > Side panel",
    "description": "Create a Skeleton and a BOS for a SpringRTS",
    "warning": "",
    "wiki_url": "https://github.com/Beherith/Skeletor_S3O",
    "tracker_url": "http://springrts.com",
    "support": "COMMUNITY",
    "category": "Rigging",
}
import bpy
from math import pi, degrees
from mathutils import Vector, Euler, Matrix
import os
import sys

piecehierarchy = None

class Skelepanel(bpy.types.Panel):
    bl_label = "Skeletor S30"
    bl_idname = "PT_Skelepanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SkeletorS30"
    
    def draw(self,context):
        layout = self.layout

        row = layout.row()
        row.operator("skele.skeletorrotator",text = '1. Correctly rotate S3O')

        row = layout.row()
        row.operator('skele.skeletoroperator',text = '2. Create Skeleton')
        
        row = layout.row()
        row.operator('skele.skeletorbosmaker',text = '3. Create BOS')
        
class S3opiece:
    def __init__(self, name, object, mesh, xoff,yoff,zoff):
        self.name = name
        self.parent = None
        self.children = []
        self.object = object
        self.mesh = mesh
        self.xoff = xoff
        self.yoff = yoff
        self.zoff = zoff
        self.loc = Vector((xoff,yoff,zoff))
        self.bone = None
        self.bonename = ""
        self.meshcopy = None
        self.worldpos = Vector((0,0,0))
        self.iktarget = None
        self.ikpole = None
        self.ikpoleangle = 0
        self.isafoot = False
        self.isAimXY = False
        
    def __repr__(self):
        return ('S3opiece:%s parent = %s children = [%s], offsets = %s object=%s mesh=%s worldpos = %s'%(
            self.name, 
            self.parent.name if self.parent is not None else None, 
            ','.join([child.name for child in self.children]), 
            self.loc, self.object,self.mesh, self.worldpos))
    
    def recursefixworldpos(self,parentpos): #note: doesnt work
        self.worldpos = self.loc+parentpos
        for child in self.children:
            child.recursefixworldpos(self.worldpos)
            
    def recurseleftrightbones(self,tag = None):
        
        def nolrname(n):
            return n.lower().replace("l","_").replace('r','_')
        
        if tag is None:
            for i,child in enumerate(self.children):  
                isLR = False
                for k, sibling in enumerate(self.children):
                    if i!=k and nolrname(child.name)==nolrname(sibling.name):
                        isLR = True
                        print (self.name, self.worldpos)
                        if self.worldpos[0]>0 : #LEFT
                            child.recurseleftrightbones(tag = '.L')
                        else:
                            child.recurseleftrightbones(tag = '.R')
                if not isLR:
                    child.recurseleftrightbones()
                        
        else:
            self.bonename = self.name+tag
            for child in self.children:
                child.recurseleftrightbones(tag = tag)
    
    def getmeshboundingbox(self):
        minz = 1000
        maxz = -1000
        miny = 1000
        maxy = -1000
        minx = 1000
        maxx = -1000
        if self.mesh is not None:
            for vertex in self.mesh.vertices:
                minz = min(minz,vertex.co[2])
                maxz = max(maxz,vertex.co[2])
                miny = min(miny,vertex.co[1])
                maxy = max(maxy,vertex.co[1])
                minx = min(minx,vertex.co[0])
                maxx = max(maxx,vertex.co[0])
        return (minx,maxx,miny,maxy,minz,maxz)
    

        
        
    
def getmeshbyname(name):
    for mesh in bpy.data.meshes:
        if mesh.name == name:
            return mesh
    return None

def getS3ORootObject():
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    rootobject = None
    rootname = ""
    for object in bpy.data.objects:
        if object.parent is None:
            for child in bpy.data.objects:
                if child.parent and child.parent == object:
                    print ("We have a root!", object)
                    rootobject = object
                    rootname = object.name
                    return rootobject,rootname
                    break

class SkeletorRotator(bpy.types.Operator):
    bl_idname = "skele.skeletorrotator"
    bl_label = "skeletor_rotate"
    bl_description = "Create a skeleton"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self,context):
        self.s3orotate(context = context)
        return {'FINISHED'}
        
    @staticmethod
    def s3orotate(context):
        scene = context.scene
        for obj in scene.objects:
            obj.select_set(True)
            obj.rotation_mode = 'ZXY'
        bpy.ops.object.select_all(action='DESELECT')

        rootobject, rootname = getS3ORootObject()
        bpy.ops.object.select_all(action='DESELECT')
        rootobject.select_set(True)
        
        #bpy.ops.transform.rotate(value=-pi/2, orient_axis='Z', orient_type='VIEW', orient_matrix=((0, -1, 0), (0, 0, -1), (-1, 0, 0)), orient_matrix_type='VIEW', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.context.object.rotation_euler[0] = pi/2

        
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        
        #return 
        bpy.ops.object.select_all(action='DESELECT')
        rootobject.select_set(True)
        oldz = bpy.context.object.location[2] 
        oldy = bpy.context.object.location[1] 
        #bpy.context.object.location[1] = oldz 
        #bpy.context.object.location[2] = oldy
        bpy.ops.object.select_all(action='SELECT')
        
        bpy.ops.transform.translate(value=(0, -10.9483, 13.9935), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        
        bpy.ops.object.select_all(action='DESELECT')
        
        rootobject.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        
        
        bpy.ops.object.select_all(action='DESELECT')

class SkeletorOperator(bpy.types.Operator):
    bl_idname = "skele.skeletoroperator"
    bl_label = "skeletize"
    bl_description = "Create a skeleton"
    bl_options = {'REGISTER','UNDO'}

    def execute(self,context):
        hier = None # piecehierarchy
        piecehierarchy = self.skeletize(context = context, hier = hier)
        return {'FINISHED'}
        
    @staticmethod
    def skeletize(context, hier):
        print ("skeletizing, very happy", hier)
        
        #debug delete all armatures and bones!
        #bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        for object in bpy.context.scene.objects:
            if object.name == "Armature":
                print (object)
                bpy.data.objects['Armature'].select_set(True)
                bpy.ops.object.delete({"selected_objects":[object]})
        
        
        pieces = {} #"name":s3opiece
        
        # collect the data we need:
        # object of each piece
        # root object
        # the offsets of each object
        # the children of each object
        # the amount of geometry each object has. 

        #find the object with no parents, but has children (root)
        rootobject,rootname = getS3ORootObject()

        #got the root!
        rootpiece = S3opiece(rootobject.name,rootobject, getmeshbyname(rootobject.name), rootobject.location[0], rootobject.location[1], rootobject.location[2]) 

        print (rootpiece)

        print ("====Collecting Pieces====")
        pieces[rootname] = rootpiece
        for object in bpy.data.objects:
            if object.parent is not None:
                newpiece = S3opiece(object.name, object, getmeshbyname(object.name), object.location[0], object.location[1], object.location[2])
                print (newpiece)

                pieces[newpiece.name] = newpiece
        for piece in pieces.values():
            print (piece)
            print (piece.object)
            if piece.object.parent is not None:
                piece.parent = pieces[piece.object.parent.name]
                piece.parent.children.append(piece)
                print (piece.name,'->', piece.parent.name)
        
        rootpiece.recursefixworldpos(Vector((0,0,0)))
        
        visited = set() # Set to keep track of visited nodes.
        opennodes = set()
        opennodes.add(rootpiece)
        dfs_piece_order = [rootpiece.name]
        
        while(len(opennodes)>0):
            nodelist = list(opennodes)
            for node in nodelist:
                dfs_piece_order.append(node.name)
                print ('nodename', node.name)
                opennodes.remove(node)
                for child in node.children:
                    opennodes.add(child)
        print (dfs_piece_order)    
                

                
        print ("====ReParenting pieces to avoid AimX and AimY====")
        # if the parent of an object is called aimx* or aimy*, then reparent the piece to the parent of aimx or aimy actual parent
        for piece in pieces.values():
            if piece.object.parent is not None and piece.object.parent.name[0:4].lower() in ['aimx','aimy']:
                print("Reparenting ",piece.name, "from", piece.parent.name,'to', piece.parent.parent.name)
                piece.parent.isAimXY = True
                try:
                    piece.parent.children.remove(piece)

                    piece.parent = pieces[piece.object.parent.parent.name]
                    piece.parent.children.append(piece)        
                except:
                    print ("piece", piece)
                    print ("parent", piece.parent)
                    print ("GP", piece.parent.parent)
                    
                    raise
        
        #final check that we have all set:

        print ("----------Sanity check:-----------")
        for k,v in pieces.items():
            print (k,v)
        
        #set the cursor to origin:
        bpy.ops.transform.translate(value=(0, 0, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, cursor_transform=True, release_confirm=True)

        print ("====Setting rotation modes to Euler ZXY====")
        scene = context.scene
        for obj in scene.objects:
            obj.select_set(False)
            obj.rotation_mode = 'ZXY'
        
        #add an armature!
        
        
        print ("====Creating Armature====")
        arm_data = bpy.data.armatures.new("Armature")
        
        armature_object =  bpy.data.objects.new("Armature", arm_data)
        armature_object.location=Vector((0,0,0)) #rootpiece.loc
        armature_object.show_in_front = True
        armature_object.data.show_axes = True
        armature_object.data.show_names = True

        armature_object.rotation_mode = 'ZXY'
        
        context.collection.objects.link(armature_object)
        
        armature_object.select_set(True)
        
        context.view_layer.objects.active = armature_object
        
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        print ("====Looking for mirrorable pieces===")
        #to enable : https://blender.stackexchange.com/questions/43720/how-to-mirror-a-walk-cycle
        #rootpiece.recurseleftrightbones()
        for name, piece in pieces.items():
            piece.bonename = name
            for name2, piece2 in pieces.items():
                if name == name2:
                    continue
                if name.lower().replace('l','').replace('r','') == name2.lower().replace('l','').replace('r',''):
                    if piece.worldpos[0]>0:
                        piece.bonename = piece.bonename + '.R'
                    else:
                        piece.bonename = piece.bonename + '.L'
        print ("====Adding Bones=====")
        # NEEDS DEPTH FIRST SEARCH!!!
        
        
        NOTAIL = True
        for name in dfs_piece_order:
            piece = pieces[name]
            if piece.isAimXY:
                continue
            if piece.bonename in arm_data.edit_bones:
                newbone = arm_data.edit_bones[piece.bonename]
            else:
                newbone = arm_data.edit_bones.new(piece.bonename)
            newbone.name = piece.bonename
            
            #TODO CHANGE TO POSE MODE TO SET THESE!
            #newbone.rotation_mode = 'ZXY'
            
            newbone.head = piece.worldpos 
            if NOTAIL:
                newbone.tail = newbone.head + Vector((0,5,0)) 
            
            tailpos =  piece.loc+Vector((0,0,10))
            if len(piece.children)>=1:
                tailpos = Vector((0,0,0))
                for child in piece.children:
                    tailpos = tailpos + child.worldpos
                tailpos = tailpos /len(piece.children)
                newbone.tail = tailpos
                if NOTAIL:
                    newbone.tail = newbone.head + Vector((0,5,0)) #TODO fixeme
                #TODO: Something is an arm if it has only nomesh children
                #thus we add a forward pointing IK target to its tailpos
                onlyemptychildren = True
                for child in piece.children:
                    if child.mesh is not None:
                        onlyemptychildren = False
                if onlyemptychildren:
                    print ("LOOKS LIKE AN ARM:",piece.name)
                    ikbone = arm_data.edit_bones.new('iktarget.'+piece.bonename)
                    ikbone.head = newbone.tail
                    ikbone.tail = newbone.tail + Vector((0,5,2))
                    piece.iktarget = ikbone  

                
                
            else: #end piece
                #TODO: CHECK FOR GEOMETRY, is it a foot or an arm or a tentacle ? 
                #TODO: multiple branches for multiple toes give too many IK targets :/
                if piece.mesh is not None and piece.parent.iktarget is None:
                    boundingbox = piece.getmeshboundingbox()
                    
                    print ("LOOKS LIKE A FOOT:", piece.name,piece.worldpos,  boundingbox)
                    if piece.worldpos[2] + boundingbox[4] <= 2.0: 
                        #this looks like a foot
                        tailpos = piece.worldpos + Vector((0, boundingbox[3], boundingbox[4]))
                        #better add the heel IK thing too XD
                        heelbone = arm_data.edit_bones.new('iktarget.'+piece.parent.bonename)
                        heelbone.head = piece.parent.bone.tail #newbone.head
                        heelbone.tail = newbone.head + Vector((0,boundingbox[4],0))
                        if NOTAIL:
                            heelbone.tail =  heelbone.head + Vector((0,5,2))
                        piece.parent.iktarget = heelbone
                    else:
                        #todo this is not a foot
                        #guess if it points forward or up or down?
                        if (boundingbox[5] > boundingbox[3] and boundingbox[5]> -1*boundingbox[2]): # points forward
                            tailpos = piece.worldpos + Vector((0, boundingbox[5], 0))
                        else:
                            if (boundingbox[3] > -1*boundingbox[2]):
                                tailpos = piece.worldpos + Vector((0, 0, boundingbox[3])) #up
                            else:
                                tailpos = piece.worldpos + Vector((0, 0, boundingbox[2])) #down
                                
                    # TODO we are also kind of a foot if we only have children with no meshes.
                else:
                    tailpos =  piece.worldpos+Vector((0,5,0))
            newbone.tail = tailpos 
            #TODO: easier rotations like this?
            if NOTAIL:
                newbone.tail = newbone.head + Vector((0,5,0))
            
            
            print ("trying to add bone to %s\nat head:%s \ntail:%s"%(piece,newbone.head,newbone.tail))
            piece.bone = newbone
        #return
        print ("=====Reparenting Bone-Bones=======")
        
        for name,piece in pieces.items():
            
            if piece.parent is not None and not piece.isAimXY:
                piece.bone.parent = piece.parent.bone      
  
        bpy.ops.object.editmode_toggle() # i have no idea what im doing
        bpy.ops.object.posemode_toggle()
        
        
        print ("=====Setting IK Targets=======")
        
        for name,piece in pieces.items():
            #break
            if not piece.isAimXY:
                armature_object.pose.bones[piece.bonename].rotation_mode = 'ZXY'

            if piece.iktarget is not None:
                
                chainlength = 1
                chainpos = piece.parent
                while(len(chainpos.children) ==1  and chainpos.parent is not None):
                    chainlength +=1
                    chainpos = chainpos.parent
                print ('Adding iktarget to ',piece.name,'chain_length = ',chainlength)
                constraint = armature_object.pose.bones[piece.bonename].constraints.new('IK')
                constraint.target = armature_object
                constraint.subtarget = 'iktarget.'+piece.bonename
                constraint.chain_count = chainlength
                armature_object.pose.bones[piece.bonename].ik_stiffness_z = 0.99 #avoids having to create knee poles

        print ("=====Parenting meshes to bones=======")
        #getting desperate here: https://blender.stackexchange.com/questions/77465/python-how-to-parent-an-object-to-a-bone-without-transformation
        for name,piece in pieces.items():
            if piece.isAimXY:
                continue
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            ob = piece.object
            bpy.ops.object.select_all(action = 'DESELECT')
            armature_object.select_set(True)
            bpy.context.view_layer.objects.active = armature_object
            bpy.ops.object.mode_set(mode='EDIT')
            parent_bone = piece.bonename
            armature_object.data.edit_bones.active = armature_object.data.edit_bones[parent_bone]
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action = 'DESELECT')
            ob.select_set(True)
            armature_object.select_set(True)
            bpy.context.view_layer.objects.active = armature_object
            
            bpy.ops.object.parent_set(type = 'BONE', keep_transform = True)
  
            
        print ("done")  
        
class SimpleBoneAnglesPanel(bpy.types.Panel):
    bl_label = "Bone Angles"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        #print ("DrawSimpleBonesAnglesPanel")
        if 'Armature' not in context.scene.objects:
            return
        arm = context.scene.objects['Armature']
        props = {"location":"move", "rotation_euler":"turn"} 
        
        selectednames = []
        for o in bpy.context.selected_pose_bones:
            selectednames.append(o.name)
        print (selectednames)
        for bone in arm.pose.bones:
            
            if 'iktarget' in bone.name:
                continue
            #row = self.layout.row()
            #row.label(text = bone.name)
            bname = bone.name

            mat = bone.matrix.copy()
            
            currbone = bone
            if currbone.parent is not None:         
                pmat = currbone.parent.matrix.copy()
                pmat.invert()
                mat = mat @ pmat
                currbone = currbone.parent
  
            
            rot = mat.to_euler('ZXY')
            row = self.layout.row()
            rottext = '%s X:%.1f Y:%.1f Z:%.1f'%(bname,degrees(rot.x),degrees(rot.y),degrees(rot.z))
            #print (rottext)
            if bname in selectednames:
                rottext = '  '+rottext.upper()
            row.label(text=rottext)
            #row = self.layout.row()
            #row.label(text='X%.1f'%(mat[0][3]))
            #row.label(text='Y%.1f'%(mat[1][3]))
            #row.label(text='Z%.1f'%(mat[2][3]))

class SkeletorBOSMaker(bpy.types.Operator):
    bl_idname = "skele.skeletorbosmaker"
    bl_label = "skeletor_bosmaker"
    bl_description = "Writes .bos to console"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self,context):
        self.tobos(context = context)
        return {'FINISHED'}
    
    def __init__(self):
        super().__init__()
        print ("SkeletorBOSMaker.init")
        self.whichframe = 0
        
    #@staticmethod
    def tobos(self,context):
        print ("MAKING BOS, BOSS")
        scene = context.scene
        if 'Armature' not in context.scene.objects:
            return
        arm = context.scene.objects['Armature']
        print ("whichframe",self.whichframe)
        self.whichframe +=1
        props = {"location":"move", "rotation_euler":"turn"} 
        
        
        #things I know:
        # curves contain the needed location data
        # pose bones matrices contain the needed rotation data
        # ignore all rots and pos's of iktargets
        # remove .L and .R monikers
        
        #required structure:
        # a dict of keyframes indexed by their frame number
        animframes = {}
        #the values of which is another dict, of piece names
        #each piece name has a turn and a move op, with xzy coords
        
        #in each frame, each 'real piece' should have its position and location stored
        if arm.animation_data is not None:
            if arm.animation_data.action is not None:
                curves = arm.animation_data.action.fcurves;
                print ("Animdata:",curves, arm.animation_data)
                for c in curves:
                    keyframes = c.keyframe_points
                    bname = c.data_path.split('"')[1]
                    if bname.startswith('iktarget.'):
                        continue
                    if bname.endswith('.R') or bname.endswith('.L'):
                        bname = bname[:-2]
                    
                    ctarget = c.data_path.rpartition('.')[2]
                    if ('euler' in ctarget or 'quaternion' in ctarget or 'scale' in ctarget) and 'location' not in ctarget:
                        continue
                    
                    axis = str(c.array_index)
                    
                    
                    for i,k in enumerate(keyframes):    
                        
                        frameidx = int(k.co[0])
                        value = float(k.co[1])
                        #if abs(value)<0.1:
                        #    continue
                        
                        if frameidx not in animframes:
                            animframes[frameidx] = {}
                        if bname not in animframes[frameidx]:
                            animframes[frameidx][bname] = {}
                            
                        animframes[frameidx][bname][ctarget+axis] = value
        
        print (animframes)
        #return(None)
        for frameidx in sorted(animframes.keys()):
            print ("SETTING FRAMETIME",frameidx)
            bpy.context.scene.frame_set(frameidx)
            #return (None)
            for bone in arm.pose.bones:
                
                if 'iktarget' in bone.name:
                    continue
                #row = self.layout.row()
                #row.label(text = bone.name)
                bname = bone.name
                if bname.endswith('.R') or bname.endswith('.L'):
                    bname = bname[:-2]
                mat = bone.matrix.copy()
                
                currbone = bone
                if currbone.parent is not None:  
                    pmat = currbone.parent.matrix.copy()
                    pmat.invert()
                    if 'lfoot' in bname:
                        pass 
                        #print (currbone.name,'->',currbone.parent.name, mat, pmat)
                    mat = mat @ pmat
                    currbone = currbone.parent
 
                
                rot = mat.to_euler('ZXY')
                rottext = '%s X:%.1f Y:%.1f Z:%.1f'%(bname,degrees(rot.x),degrees(rot.y),degrees(rot.z))
                print (rottext)
                
                for axis,value  in enumerate(rot[0:3]):                        
                    if frameidx not in animframes:
                        animframes[frameidx] = {}
                    if bname not in animframes[frameidx]:
                        animframes[frameidx][bname] = {}
                    print ('adding',frameidx,bname,'rot'+str(axis),value)
                    animframes[frameidx][bname]['rot'+str(axis)] = degrees(value)
                    
        print ("animframes:",animframes)        
        fps = 30.0
        startframe = 7
        interval = 6
        endframe = 55
        movethres = 0.5
        rotthres = 0.5 #degrees
        sleepperframe = 1.0/fps
        #conversion time:
        #output a bos script
        #simplify mini rots and mini moves
        #the first frame can be ignored
        frameidxs = sorted(animframes.keys())
       
        filepath = bpy.data.filepath
        directory = os.path.dirname(filepath)
        print(directory,filepath)
        AXES = 'XZY'
        BOSAXIS = ['x-axis','z-axis','y-axis']
        newfile_name = filepath + ".bos_export.txt"
        outf = open(newfile_name,'w')
        outf.write("// Generated for %s\n// Using https://github.com/Beherith/Skeletor_S3O \n"%filepath)
        outf.write("// this animation uses the static-var animSpeed which contains how many frames each keyframe takes\n")
        
        animSpeed = [frameidxs[i] - frameidxs[i-1] for i in range(2,len(frameidxs))]
        animFPK = 4
        if len(animSpeed) == 0:
            print ("SUPER WARNING, NO DETECTABLE FRAMES!")
            return
        else:
            animFPK = float(sum(animSpeed))/(len(frameidxs)-2)
            if (animFPK- round(animFPK) > 0.00001):
                warn = "//Animframes spacing is %f, THIS SHOULD BE AN INTEGER, SPACE YOUR KEYFRAMES EVENLY!\n"%animFPK
                outf.write(warn)
                print(warn)
            
        stopwalking_maxspeed = {} #dict of of bos commands, with max velocity in it to define the stopwalking func
        outf.write("Walk() {\n")
        
        firststep = True
        for i, frameidx in enumerate(frameidxs):

            if i == 0:
                continue
            
            thisframe = animframes[frameidxs[i]]
            prevframe = animframes[frameidxs[i-1]]
            
            sleeptime = sleepperframe * (frameidxs[i] - frameidxs[i-1])
            
            
            
            if firststep:
                outf.write("\tif (bMoving) {\n")
            else:
                outf.write("\t\tif (bMoving) {\n")
                
            for bname in sorted(thisframe.keys()):
                motions = thisframe[bname]
                for axis, value in motions.items():
                    #find previous value
                    prevvalue = 0
                    foundprev = False
                    for p in range(i-1,-1,-1):
                        if bname in animframes[frameidxs[p]] and axis in animframes[frameidxs[p]][bname]:
                            prevvalue = animframes[frameidxs[p]][bname][axis]
                            foundprev = True
                            break
                    if not foundprev:
                        print ("Failed to find previous position for bone",bname,'axis',axis)                  
  
                    axidx = AXES[int(axis[-1])]
                    ax = int(axis[-1])
                    axmul = [-1.0,-1.0,1.0]
                    if abs(value-prevvalue)<0.1: 
                        print ("Ignored %s %s of %.6f delta"%(bname,axis,value-prevvalue))
                        continue
                    else:
                        
                        stopwalking_cmd = 'turn %s to %s'
                        boscmd =  '\t\t\tturn %s to %s <%.6f> speed <%.6f>;\n'
                        if axis.startswith('location'):
                            
                            axmul = [1.0,1.0,1.0]
                            boscmd =  '\t\t\tmove %s to %s [%.6f] speed [%.6f];\n'
                            stopwalking_cmd = 'move %s to %s'
                        
                        stopwalking_cmd = stopwalking_cmd % (bname,BOSAXIS[ax])
                        maxvelocity = abs(value-prevvalue) /sleeptime
                        if stopwalking_cmd in stopwalking_maxspeed:
                            if maxvelocity > stopwalking_maxspeed[stopwalking_cmd]:
                                stopwalking_maxspeed[stopwalking_cmd] = maxvelocity
                        else:
                            stopwalking_maxspeed[stopwalking_cmd] = maxvelocity
                        BOS = boscmd %(
                                bname,
                                BOSAXIS[ax],
                                value * axmul[ax],
                                abs(value-prevvalue) /sleeptime
                        )
                        outf.write(BOS)     
                           
   
            
            if firststep:
                outf.write('\t\tsleep %i;\n'%(1000*sleeptime -1))
            else:
                outf.write('\t\tsleep %i;\n'%(1000*sleeptime -1))
            
        
            if firststep:
                outf.write("\t}\n")
                outf.write("\twhile(bMoving) {\n")
                firststep = False
            else:
                outf.write('\t\t}\n')
                        
        outf.write('\t}\n')

        outf.write('}\n')
        
        outf.write('// Call this from MotionControl()!\nStopWalking() {\n')
        for restore in sorted(stopwalking_maxspeed.keys()):
            if restore.startswith('turn'):
                outf.write('\t'+restore+ ' <0> speed <%.6f>;\n'%stopwalking_maxspeed[restore])
            if restore.startswith('move'):
                outf.write('\t'+restore+ ' [0] speed [%.6f];\n'%stopwalking_maxspeed[restore])
        outf.write('}\n')
        
        
        '''UnitSpeed()
            {     
                moveSpeed = get MAX_SPEED; // this returns cob units per frame i think
                //we need to calc the frames per keyframe value, from the known anim
                while(TRUE)
                {
                    currentSpeed = (get CURRENT_SPEED)*20/moveSpeed;
                    if (currentSpeed<4) currentSpeed=4;
                    animSpeed = 1250 / currentSpeed;
                    sleep 142;
                }
            }'''
        
        outf.close()
        print ("Done writing bos!")

def register():
    bpy.utils.register_class(SkeletorOperator)
    bpy.utils.register_class(SkeletorRotator)
    bpy.utils.register_class(SkeletorBOSMaker)
    bpy.utils.register_class(Skelepanel)
    bpy.utils.register_class(SimpleBoneAnglesPanel)
    
def unregister():
    bpy.utils.unregister_class(SkeletorOperator)
    bpy.utils.unregister_class(SkeletorRotator)
    bpy.utils.unregister_class(SkeletorBOSMaker)
    bpy.utils.unregister_class(Skelepanel)
    bpy.utils.unregister_class(SimpleBoneAnglesPanel)
    
if __name__ == "__main__":
    register()
    
    
    
