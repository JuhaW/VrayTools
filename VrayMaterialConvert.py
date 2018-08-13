import bpy
from collections import OrderedDict

#rgb to hsV
def rgb_to_hsV(rgb):
	return (rgb/1)**(1/2.2)

#NODE
def node_position(nodes):
	
	x = 0
	y = 0
	for node in nodes:
		node.location.xy = (x,y)
		x -= 200
			
def nodetree_create(nodetreetype, name):
	#type ='VRayNodeTreeMaterial')
	
	return bpy.data.node_groups.new(name,nodetreetype)

def node_create(ntree, nodetype):
	#type="VRayNodeOutputMaterial"
	#type="VRayNodeMetaStandardMaterial"
	#type="VRayNodeMetaImageTexture"
	
	return ntree.nodes.new(type=nodetype)
	
def node_inputs_get(node, socketname):
	
	if node.type == 'CUSTOM':
		for input in node.inputs:
			if input.name == socketname:
				return input
	return None

def node_outputs_get(node, socketname):
	
	if node.type == 'CUSTOM':
		for output in node.outputs:
			if output.name == socketname:
				return output
	return None

def node_connect_2(ntree, nodeout,outstring, nodein, instring):

	socketout = node_outputs_get(nodeout, outstring)
	socketin = node_inputs_get(nodein, instring)
	#link sockets
	ntree.links.new(socketout, socketin)
	return socketout, socketin
	
def node_connect(ntree, socketout, socketin):
	
	#link sockets
	ntree.links.new(socketout, socketin)
	
def object_materials_get(o):
	
	#get object materials
	l = list(OrderedDict.fromkeys(o.data.materials))
	return list(filter(None.__ne__, l))

def object_texture_images(mat):
	#get object material image textures
	t = list(filter(None.__ne__, mat.texture_slots))
	#for i in t:
	#	print ("text slots filtered:", i.name)
	imagetextures = [i for i in t if i.texture.type =='IMAGE' and i.use and i.texture.image]
	#return only diffuse, alpha,  emit, bump, normal
	imagetextures = [i for i in imagetextures if 
		i.use_map_color_diffuse or
		i.use_map_color_spec or
		i.use_map_alpha or
		i.use_map_emit or
		i.use_map_normal]
	non_imagetextures = [i for i in t if i.texture.type != 'IMAGE' and i.use]
	return imagetextures, non_imagetextures
			

def textures_image():
	
	#mats = object_materials_get(bpy.context.object)
	mats = bpy.data.materials
	for mat in mats:
		
		ntree = nodetree_create('VRayNodeTreeMaterial',mat.name)
		mat.vray.ntree = ntree
		nodeout = node_create(ntree, 'VRayNodeOutputMaterial')
		nodemat = node_create(ntree, 'VRayNodeMetaStandardMaterial')
		node_connect(ntree,nodemat.outputs[0], nodeout.inputs[0])
		
		print ("Material:", mat)
		tex_slot, non_imagetex_slot = object_texture_images(mat)
		
		nodes = []
		nodes.append(nodeout)
		nodes.append(nodemat)
		###
		
		mat_alpha = False
		slot_bump = False
		slot_normal = False
		
		for slot_index, slot in enumerate(tex_slot):
			
			if slot.use_map_normal and (slot_bump or slot_normal):
				print ("---------------------normal map or bump twice")
				continue
			else:
				nodeimg = node_create(ntree, "VRayNodeMetaImageTexture")
				nodeimg.texture.image = slot.texture.image
				nodes.append(nodeimg)
			
			###	
			if slot.use_map_color_diffuse:
				node_connect_2(ntree, nodeimg, "Output", nodemat, "Diffuse")
				print ("diffuse")

			if slot.use_map_color_spec:
				socket_out, socket_in = node_connect_2(ntree, nodeimg, "Output", nodemat, "Reflect")
				socket_in.multiplier = slot.specular_color_factor * 100

				print ("specular")	

			if slot.use_map_normal:
				
				if slot.texture.use_normal_map:
					#normal map
					slot_normal = True
					node_connect_2(ntree, nodeimg, "Output", nodemat, "Normal Texture")
					
					#"slot.normal_factor #'Bump Amount Texture'
					socket_bump_value = node_inputs_get(nodemat, 'Bump Amount Texture')
					socket_bump_value.value = slot.normal_factor
					#set normal tangent
					nodemat.BRDFBump.map_type = '1'
					print ("normal")
				else:
					#bump map
					slot_bump = True
					node_connect_2(ntree, nodeimg, "Intensity", nodemat, "Bump Texture")
					socket_bump_value = node_inputs_get(nodemat, 'Bump Amount Texture')
					socket_bump_value.value = slot.normal_factor
					print ("bump")
			if slot.use_map_emit:
				#Self Illumination
				#print ("Emit found")
				node_connect_2(ntree, nodeimg, "Output", nodemat, "Self Illumination")
				print ("emit")
			if slot.use_map_alpha:
				#print ("map alpha found in slot:", slot )
				socket_out, socket_in  = node_connect_2(ntree, nodeimg, "Alpha", nodemat, "Opacity")
				socket_in.multiplier = slot.alpha_factor*100
				mat_alpha = True
				print ("alpha")
		if mat.use_transparency :
			socket_in = node_inputs_get(nodemat, "Opacity")
			socket_in.value = mat.alpha

		#diffuse + diffuse intensity
		socket = node_inputs_get(nodemat, 'Diffuse')
		socket.value = mat.diffuse_color
		#reflection = specular color * specular intensity
		#socket = node_inputs_get(nodemat, 'Reflect')
		#socket.value = mat.specular_color * mat.specular_intensity
		#Emit
		if mat.emit > 0:
			socket = node_inputs_get(nodemat, "Self Illumination")
			socket.value = mat.diffuse_color
			socket.value.v *= mat.emit
		
		
		node_position(nodes)


#textures_image()
		