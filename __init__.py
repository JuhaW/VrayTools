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
from bpy.props import FloatVectorProperty, BoolProperty, IntProperty, FloatProperty
Vray_MatList = []

#Clay render
#Shadow catcher

##################################################################################

def node_create(ntree, node):
	
	n = ntree.nodes.new(node)
	
	return n

	
def node_get_output(mntree):
	
	node, =[i for i in mntree.nodes if i.bl_idname == 'VRayNodeOutputMaterial']
	return node

def store_materials():
	materials = {}
	
	objs = [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE','SURFACE','META','FONT')]
		
	#store materials
	for o in objs:
		lst = []
		#if object has no materials, create one
		mats = [i for i in o.data.materials if i is not None]
		if not mats:
			o.data.materials.clear()
			mat = bpy.data.materials.new("Missing material")
			o.data.materials.append(mat)
			print ("===============")
			print ("new material created")
			print ("===============")
			input ()
			
		for i, slot in enumerate(o.material_slots):
			if slot.material:
				lst.append([i, slot.material.name, slot.link])
			else:
				lst.append([i, None, slot.link])
		materials[o.name] = lst

	return objs, materials

def vray_clay_render(b_clay,b_material_exclude):
	
	
	Clay = "Clay"
	Invisible = "Invisible"
	
	if b_clay:
		
		#find "Clay" material, create it if not exist, delete Clay nodetree nodes if exists
		#mat = bpy.data.materials.get(Clay)
		#if mat == None:
		clay_mat = bpy.data.materials.new(Clay)

		ntree = bpy.data.node_groups.get(clay_mat.name)
		if ntree:
			ntree.nodes.clear()
		else:	
			ntree = bpy.data.node_groups.new(clay_mat.name, 'VRayNodeTreeMaterial')
		clay_mat.vray.ntree = ntree
		print()
		print (clay_mat.name, ntree.name)
		print()
		#print ("new material created")
		#print ("material:", mat)

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
		#bpy.context.scene.vray.SettingsOptions.mtl_override_on = True
		#bpy.context.scene.vray.SettingsOptions.mtl_override = Clay
		clay_ntree = ntree
		
	if b_material_exclude:
		
		#find "Invisible" material, create it if not exist, delete Clay nodetree nodes if exists
		mat = bpy.data.materials.get(Invisible)
		if mat == None:
			mat = bpy.data.materials.new(Invisible)

		ntree = bpy.data.node_groups.get(Invisible)
		if ntree:
			ntree.nodes.clear()
		else:	
			ntree = bpy.data.node_groups.new(Invisible, 'VRayNodeTreeMaterial')
		mat.vray.ntree = ntree
		#print ("Invisible material created")
		#print ("material:", mat)

		#create output node and standard material node
		node_out = node_create(ntree, 'VRayNodeOutputMaterial')
		node_1 = node_create(ntree, 'VRayNodeMetaStandardMaterial')
		#set node links
		node_1.location = (node_out.location.x -200,0)
		ntree.links.new(node_out.inputs[0], node_1.outputs[0])
		#set diffuse color
		#node_1.inputs.get('Diffuse').value = (.214,.214,.214)
		node_1.inputs.get('Opacity').value = 0
		#clip mode
		node_1.BRDFVRayMtl.opacity_mode = '1'
		
		
	objs, materials = store_materials()
	#print ("stored materials", materials)
	#print ("Objekteja:", len(objs))
	#print ("Materiaaleja:", len(materials))
	#print ("Materials from subroutine:", materials)
	
	if b_clay or b_material_exclude:
		
		
		#objectname, 0 slotindex, 1 slot material name, 2 slot link
		for o_name in materials:
			
			for i in materials[o_name]:
				
				mat_name = i[1]
				if mat_name in Vray_MatList and b_material_exclude:
					#replace object materials
					#o.data.materials[i] = bpy.data.materials['Invisible']
					bpy.context.scene.objects[o_name].material_slots[i[0]].link = i[2]
					bpy.context.scene.objects[o_name].material_slots[i[0]].material = bpy.data.materials[Invisible]
				elif b_clay:
					#replace object materials
					bpy.context.scene.objects[o_name].material_slots[i[0]].link = i[2]
					bpy.context.scene.objects[o_name].material_slots[i[0]].material = clay_mat
			
		#print("========================")	
		#print ("excluded materials:", materials)
		#print("========================")
		#input ("enter to continue...")
	
	bpy.ops.render.render()
	
	#restore materials
	if b_clay or b_material_exclude:

		for o_name in materials.keys():
			for i in materials[o_name]:
				#input("Press Enter to continue...")
				print ("o_name:", o_name)
				print (":", i)
				bpy.context.scene.objects[o_name].material_slots[i[0]].link = i[2]
				if i[1] is not None:
					mat = bpy.data.materials.get(i[1])
				else:
					mat = None
				bpy.context.scene.objects[o_name].material_slots[i[0]].material = mat
				
			
	if b_clay:
		#bpy.context.scene.vray.SettingsOptions.mtl_override_on = False
		bpy.data.materials.remove(bpy.data.materials[clay_mat.name], do_unlink = True)
		bpy.data.node_groups.remove(bpy.data.node_groups[clay_ntree.name], do_unlink = True)
		

	if b_material_exclude:
		
		bpy.data.materials.remove(bpy.data.materials[Invisible], do_unlink = True)
		bpy.data.node_groups.remove(bpy.data.node_groups[Invisible], do_unlink = True)
		

		
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
		
	
class Vray_Mat_Exclude_Add(bpy.types.Operator):
	"""Add material to exclude list"""
	bl_idname = "vray.mat_exclude_add"
	bl_label = "Add material to exclude list"
	#bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.
	
	index = IntProperty(default = 0)
		
	def execute(self, context):
		
		mat = context.scene.vray_material_select
		if mat not in Vray_MatList and mat:
			Vray_MatList.append(context.scene.vray_material_select)
		
		return {'FINISHED'}
	
class Vray_Mat_Exclude_Delete(bpy.types.Operator):
	"""This material is not part of render"""
	bl_idname = "vray.mat_exclude_delete"
	bl_label = "Remove material from exclude list"
	#bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.
	
	index = IntProperty()
		
	def execute(self, context):
				
		Vray_MatList.pop(self.index)
		
		return {'FINISHED'}

class Vray_Clay_Render(bpy.types.Operator):
	"""Clay render"""
	bl_idname = "vray.clay_render"
	bl_label = "Render"
	#bl_options = {'REGISTER', 'UNDO'}	# enable undo for the operator.
	
		
	def execute(self, context):
	
		sce = context.scene
		vray_clay_render(sce.vray_clay, sce.vray_material_exclude)
		
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
		box = layout.box()
		row = box.row()
		row.prop(scene, "vray_shadow_catcher",icon="TRIA_DOWN" if scene.vray_shadow_catcher else "TRIA_RIGHT", icon_only=True, emboss=False)
		row.label("Shadow catcher:")
		if scene.vray_shadow_catcher:
			row = box.row()
			catcher = row.operator('vray.shadow_catcher_on', text = "On", icon = 'IMAGE_ZDEPTH')
			catcher.on = True
			catcher = row.operator('vray.shadow_catcher_on',  text = "Off", icon = 'IMAGE_ZDEPTH')
			catcher.on = False
			#row = layout.row()
			row.operator('vray.shadow_catcher_select', text ="Select", icon = 'HAND')
			
		row = layout.row()
		box = layout.box()
		row = box.row()
		row.prop(scene, "vray_material_convert",icon="TRIA_DOWN" if scene.vray_material_convert else "TRIA_RIGHT", icon_only=True, emboss=False)
		row.label("Convert materials from Blender Render:")
		if scene.vray_material_convert:
			row = box.row()
			row.operator('vray.material_convert', icon = 'MATERIAL')
		
		row = layout.row()
		box = layout.box()
		row = box.row()
		row.prop(scene, "vray_expand1",icon="TRIA_DOWN" if scene.vray_expand1 else "TRIA_RIGHT", icon_only=True, emboss=False)
		row.label("Render:")
		
		if scene.vray_expand1:
			row = box.row()
			
			row.operator('vray.clay_render', icon = "VRAY_LOGO_MONO")
			col = box.row()
			row = col.split(percentage = 0.7,align = True)
			#row = box.row()
			row.prop(scene, "vray_clay", text = "Clay render")
			row.prop(scene, "vray_clay_color", text = "")
			row = box.row()
			#row.label("Material exclude from render:")
			row = box.row()
			row.prop(scene, "vray_material_exclude", text = "Exclude materials from render")
			
			col = box.row()
			row = col.split(percentage = 0.8,align = True)
			row.enabled = scene.vray_material_exclude
			
			row.prop_search(scene, "vray_material_select", bpy.data, "materials", text = "")
			row.operator('vray.mat_exclude_add', text = "",  emboss = True, icon = 'ZOOMIN')
			
			
			
			for i, mat in enumerate(Vray_MatList):
				row = box.row()
				row.enabled = scene.vray_material_exclude
				list_index = row.operator('vray.mat_exclude_delete', text = mat, icon = 'MATERIAL')
				list_index.index = i
				
			
	
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
	bpy.types.Scene.vray_material_select = bpy.props.StringProperty(default = "")
	bpy.types.Scene.vray_clay = BoolProperty(default = False)
	bpy.types.Scene.vray_material_exclude = BoolProperty(default = True)
	bpy.types.Scene.vray_expand1 = BoolProperty(default = True)
	bpy.types.Scene.vray_shadow_catcher = BoolProperty(default = False)
	bpy.types.Scene.vray_material_convert = BoolProperty(default = False)
	
	#external modules
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
	del bpy.types.Scene.vray_material_select
	del bpy.types.Scene.vray_clay
	del bpy.types.Scene.vray_material_exclude
	del bpy.types.Scene.vray_shadow_catcher
	del bpy.types.Scene.vray_material_convert
	#external modules	
	bpy.utils.unregister_module(VrayDeleteMaterial)

if __name__ == "__main__":
	register()
