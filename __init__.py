bl_info = {
	"name": "Vray Tools",
	"author": "JuhaW",
	"version": (1, 0, 0, 0),
	"blender": (2, 7, 9, 0),
	"api": 44539,
	"category": "Tools",
	"location": "Tools ",
	"description": "Various tools for V-Ray",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "", }


import importlib as imp

submodules =  ('VrayMaterialConvert', 'VrayDeleteMaterial',)

if "bpy" in locals():
	glob = globals()
	
	for sub in submodules:
		imp.reload(glob[sub])

	print("Vray tools: reload ready")

else:
	glob = globals()
	for sub in submodules:
		glob[sub] = imp.import_module("." + sub, __package__)
	
	print("Vray tools: ready")
	
	
import bpy
from bpy.props import FloatVectorProperty, BoolProperty, FloatProperty

#Clay render
#Shadow catcher

##################################################################################

def node_create(ntree, node):
	
	n = ntree.nodes.new(node)
	
	return n

	
def node_get_output(mntree):
	
	node, =[i for i in mntree.nodes if i.bl_idname == 'VRayNodeOutputMaterial']
	return node


def vray_clay_render():
	Clay = "Clay"
	#find "Clay" material, create it if not exist, delete Clay nodetree nodes if exists
	mat = bpy.data.materials.get(Clay)
	if mat == None:
		mat = bpy.data.materials.new(Clay)

	ntree = bpy.data.node_groups.get(Clay)
	if ntree:
		ntree.nodes.clear()
	else:	
		ntree = bpy.data.node_groups.new(Clay, 'VRayNodeTreeMaterial')
	mat.vray.ntree = ntree
	print ("new material created")
	print ("material:", mat)

	#create output node and standard material node
	node_out = node_create(ntree, 'VRayNodeOutputMaterial')
	node_1 = node_create(ntree, 'VRayNodeMetaStandardMaterial')
	#set node links
	node_1.location = (node_out.location.x -200,0)
	ntree.links.new(node_out.inputs[0], node_1.outputs[0])
	#set diffuse color
	#node_1.inputs.get('Diffuse').value = (.214,.214,.214)
	node_1.inputs.get('Diffuse').value = (bpy.context.scene.vray_clay_color)
	#set material overwrite on
	bpy.context.scene.vray.SettingsOptions.mtl_override_on = True
	bpy.context.scene.vray.SettingsOptions.mtl_override = Clay
	bpy.ops.render.render()
	bpy.context.scene.vray.SettingsOptions.mtl_override_on = False

	#'VRayNodeTreeMaterial'
	#'VRayNodeMetaStandardMaterial'
	#'VRayNodeOutputMaterial'
	#'VRayNodeMtlRoundEdges'

def vray_shadow_catcher(on):

	matte = 'Shadow catcher '
	objs =[o for o in bpy.context.selected_objects if o.type in ('MESH', 'CURVE','SURFACE','META','FONT')]
	for o in objs:
		if not on:
			o.vray.MtlWrapper.use = False
			o.name = o.name[len(matte):] if o.name[:len(matte)] == matte else o.name
			o.draw_type = 'TEXTURED'

		else:    
			o.vray.MtlWrapper.use = True
			o.vray.MtlWrapper.matte_surface = True
			o.vray.MtlWrapper.affect_alpha = True
			o.vray.MtlWrapper.shadows = True
			o.vray.MtlWrapper.alpha_contribution = -1
			o.name = matte + o.name if o.name[:len(matte)] != matte else o.name
			o.draw_type = 'WIRE'
			
##################################################################################

class Vray_Material_Convert(bpy.types.Operator):
	"""Convert materials from Blender Render, Supported with image textures: diffuse,specular, alpha, emit, bump, normal
Supported without image textures: diffuse, alpha, emit"""
	bl_idname = "vray.material_convert"
	bl_label = "Material Convert"
	#bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.
	
		
	def execute(self, context):
	
		VrayMaterialConvert.textures_image()
		
		return {'FINISHED'}

		
class Vray_Shadow_Catcher(bpy.types.Operator):
	"""Set selected objects shadow catcher"""
	bl_idname = "vray.shadow_catcher_on"
	bl_label = "Shadow catcher on"
	#bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.
	
	on = BoolProperty(default = True)
		
	def execute(self, context):
				
		vray_shadow_catcher(self.on)
		
		return {'FINISHED'}

class Vray_Shadow_Catcher_Select(bpy.types.Operator):
	"""Selected shadow catcher objects"""
	bl_idname = "vray.shadow_catcher_select"
	bl_label = "Select Shadow catcher objects"
	#bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.
	
	#on = BoolProperty(default = True)
		
	def execute(self, context):
				
		bpy.ops.object.select_all(action='DESELECT')
		objs =[o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE','SURFACE','META','FONT')]

		for o in objs:
			if o.vray.MtlWrapper.use:
				o.select = True
				context.scene.objects.active = o
		
		return {'FINISHED'}
		
	


class Vray_Clay_Render(bpy.types.Operator):
	"""Clay render"""
	bl_idname = "vray.clay_render"
	bl_label = "Clay render"
	#bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.
	
		
	def execute(self, context):
	
		vray_clay_render()
		
		return {'FINISHED'}

##################################################################################

class Vray_Tools_Panel(bpy.types.Panel):
	"""Creates a Panel in the scene context of the properties editor"""
	bl_label = "Vray Tools"
	bl_idname = "vray.tools_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	#bl_context = "scene"
			
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		
		row = layout.row()
		row.operator('vray.clay_render', icon = "VRAY_LOGO_MONO")
		row.prop(scene, "vray_clay_color", text = "")
		
		row = layout.row()
		row.label("Shadow catcher:")
		row = layout.row()
		catcher = row.operator('vray.shadow_catcher_on', text = "On", icon = 'IMAGE_ZDEPTH')
		catcher.on = True
		catcher = row.operator('vray.shadow_catcher_on',  text = "Off", icon = 'IMAGE_ZDEPTH')
		catcher.on = False
		#row = layout.row()
		row.operator('vray.shadow_catcher_select', text ="Select", icon = 'HAND')
		
		row = layout.row()
		row.label("Convert materials from Blender Render:")
		row = layout.row()
		row.operator('vray.material_convert', icon = 'MATERIAL')
		
		
	
##################################################################################
		
def register():

	bpy.utils.register_module(__name__)
	"""
	bpy.utils.register_class(Vray_Material_Convert)
	bpy.utils.register_class(Vray_Shadow_Catcher)
	bpy.utils.register_class(Vray_Clay_Render)
	bpy.utils.register_class(Vray_Tools_Panel)
	"""
	bpy.types.Scene.vray_clay_color = bpy.props.FloatVectorProperty(name = "Clay_color", description = "Clay color", 
                                 subtype = "COLOR", size = 3, min = 0.0, max = 1.0, default = (.214,.214,.214))
			
#external modules
	#VrayMaterialConvert.register()
	VrayDeleteMaterial.register()
	
	
def unregister():
	bpy.utils.unregister_module(__name__)
	"""
	bpy.utils.unregister_class(Vray_Material_Convert)
	bpy.utils.unregister_class(Vray_Shadow_Catcher)
	bpy.utils.unregister_class(Vray_Clay_Render)
	bpy.utils.unregister_class(Vray_Tools_Panel)
	"""
	
	del bpy.types.Scene.vray_clay_color
	
	#bpy.utils.unregister_module(VrayMaterialConvert)
	#bpy.utils.unregister_module(VrayDeleteMaterial)

if __name__ == "__main__":
	register()
