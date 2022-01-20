#script to make rigify compatible with unity humanoid
#HOWTO: right after generating rig using rigify
#	press armature -> Rigify To Unity Converter -> (Prepare rig for unity) button
bl_info = {
    "name": "Rigify to Unity",
    "category": "Rigging",
    "description": "Change Rigify rig into Mecanim-ready rig for Unity",
    "location": "At the bottom of Rigify rig data/armature tab",
    "blender":(2,80,0)
}

import bpy
import re


class UnityMecanim_Panel(bpy.types.Panel):
    bl_label = "Rigify to Unity converter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(self, context):
        return context.object.type == 'ARMATURE' and "DEF-upper_arm.L.001" in bpy.context.object.data.bones
    
    def draw(self, context):
        self.layout.operator("rig4mec.convert2unity")
        
        
class UnityMecanim_Convert2Unity(bpy.types.Operator):
    bl_idname = "rig4mec.convert2unity"
    bl_label = "Prepare rig for Unity"
    
    def execute(self, context):
        # expecting ob to the armature
        ob = bpy.context.object

        # enter edit mode to access bone manipulation
        bpy.ops.object.mode_set(mode='EDIT')
        
        # reparent bones to their proper bones
        # tuple: (bone, new_parent, new_tail)
        bones_relationships = [
            ('DEF-shoulder.L' , 'DEF-spine.003'  , None),
            ('DEF-shoulder.R' , 'DEF-spine.003'  , None),
            ('DEF-upper_arm.L', 'DEF-shoulder.L' , 'DEF-upper_arm.L.001'),
            ('DEF-upper_arm.R', 'DEF-shoulder.R' , 'DEF-upper_arm.R.001'),
            ('DEF-thigh.L'    , 'DEF-spine'      , 'DEF-thigh.L.001'),
            ('DEF-thigh.R'    , 'DEF-spine'      , 'DEF-thigh.R.001'),
            ('DEF-forearm.L'  , 'DEF-upper_arm.L', 'DEF-forearm.L.001'),
            ('DEF-forearm.R'  , 'DEF-upper_arm.R', 'DEF-forearm.R.001'),
            ('DEF-hand.L'     , 'DEF-forearm.L'  , None),
            ('DEF-hand.R'     , 'DEF-forearm.R'  , None),
            ('DEF-shin.L'     , 'DEF-thigh.L'    , 'DEF-shin.L.001'),
            ('DEF-shin.R'     , 'DEF-thigh.R'    , 'DEF-shin.R.001'),
            ('DEF-foot.L'     , 'DEF-shin.L'     , None),
            ('DEF-foot.R'     , 'DEF-shin.R'     , None)
        ]
        for bone, parent, new_tail in bones_relationships:
            if bone not in ob.data.edit_bones: continue
            if parent not in ob.data.edit_bones: continue
            
            ob.data.edit_bones[bone].parent = ob.data.edit_bones[parent]
            if new_tail and new_tail in ob.data.edit_bones:
                ob.data.edit_bones[bone].tail = ob.data.edit_bones[new_tail].tail

        # relinking bones that are linked to certain bones (spine, head, thighs, upper_arm)
        # tuple: (bone_to_scan, new_parent)
        bones_relink = [
            ('ORG-spine'      , 'DEF-spine'      ),
            ('ORG-spine.006'  , 'DEF-spine.006'  ),
            ('ORG-thigh.L'    , 'DEF-thigh.L'    ),
            ('ORG-thigh.R'    , 'DEF-thigh.R'    ),
            ('ORG-upper_arm.L', 'DEF-upper_arm.L'),
            ('ORG-upper_arm.R', 'DEF-upper_arm.R')
        ]
        for bone, parent in bones_relink:
            if bone not in ob.data.edit_bones: continue
            if parent not in ob.data.edit_bones: continue
            for child in ob.data.edit_bones[bone].children:
                child.parent = ob.data.edit_bones[parent]

        # remove unnecessary bones or to-be-merged bones
        bones_to_remove = [
            'DEF-breast.L', 'DEF-breast.R',
            'DEF-pelvis.L', 'DEF-pelvis.R',
            'DEF-upper_arm.L.001', 'DEF-upper_arm.R.001',
            'DEF-forearm.L.001', 'DEF-forearm.R.001',
            'DEF-thigh.L.001', 'DEF-thigh.R.001',
            'DEF-shin.L.001', 'DEF-shin.R.001'
        ]
        for bone in bones_to_remove:
            if bone not in ob.data.edit_bones: continue
            ob.data.edit_bones.remove(ob.data.edit_bones[bone])

        # exiting bone manipulation
        bpy.ops.object.mode_set(mode='OBJECT')

        # rename certain bones (old_name, new_name)
        namelist = [
            ("DEF-spine.006", "DEF-head"),
            ("DEF-spine.005", "DEF-neck")
        ]
        for name, newname in namelist:
            if name not in ob.pose.bones: continue
            ob.pose.bones[name].name = newname

        # ending of the first phase
        self.report({'INFO'}, 'Removed incompatible bones.')

        # second phase
        # Merge vertex groups of deleted or deactivated bones into their original parents
        for child in ob.children:
            if child.type != 'MESH':
                print('Skipped ' + child.name + ' (not a mesh)')
                continue
            
            valid_child = False
            for modifier in child.modifiers:
                if modifier.type != 'ARMATURE': continue
                if modifier.object == ob:
                    valid_child = True
                    break
            
            if valid_child == False:
                print('Skipped ' + child.name + ' (no armature modifier or not relevant)')
                continue
            
            transfer_list = [
                ('DEF-forearm.L', 'DEF-forearm.L.001'),
                ('DEF-upper_arm.L', 'DEF-upper_arm.L.001'),
                ('DEF-forearm.R', 'DEF-forearm.R.001'),
                ('DEF-upper_arm.R', 'DEF-upper_arm.R.001'),
                ('DEF-thigh.L', 'DEF-thigh.L.001'),
                ('DEF-shin.L', 'DEF-shin.L.001'),
                ('DEF-thigh.R', 'DEF-thigh.R.001'),
                ('DEF-shin.R', 'DEF-shin.R.001'),

                ('DEF-spine', 'DEF-pelvis.L'),
                ('DEF-spine', 'DEF-pelvis.R'),
                ('DEF-spine.003', 'DEF-breast.L'),
                ('DEF-spine.003', 'DEF-breast.R')
            ]
            
            print('> Started on ' + child.name)
            bpy.context.view_layer.objects.active = child
            for dst, src in transfer_list:    
                print('\t' + src + ' -> ' + dst)

                # check if src/dst vertex group exists
                if (src in child.vertex_groups) and (dst not in child.vertex_groups):
                    child.vertex_groups[src].name = dst
                    pass
                elif (src not in child.vertex_groups):
                    continue

                vertex_weight_edit_mod = child.modifiers.new(name='tmp_vertex_weight_edit', type='VERTEX_WEIGHT_MIX')
                vertex_weight_edit_mod.mix_set = 'ALL'
                vertex_weight_edit_mod.mix_mode = 'ADD'
                vertex_weight_edit_mod.vertex_group_a = dst
                vertex_weight_edit_mod.vertex_group_b = src

                bpy.ops.object.modifier_apply(modifier='tmp_vertex_weight_edit')
                
            print('> Finished ' + child.name)

        bpy.context.view_layer.objects.active = ob

        self.report({'INFO'}, 'Merged vertex groups.')

        return{'FINISHED'}

def register():
    #classes     
    bpy.utils.register_class(UnityMecanim_Panel)
    bpy.utils.register_class(UnityMecanim_Convert2Unity)
    
    
def unregister():
    #classes
    bpy.utils.unregister_class(UnityMecanim_Panel)
    bpy.utils.unregister_class(UnityMecanim_Convert2Unity)
