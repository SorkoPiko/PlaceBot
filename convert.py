from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import struct
from array import array

@dataclass
class Color:
	r: int
	g: int
	b: int
	opacity: int
	blending: bool

@dataclass
class ServerResponse:
	data: Dict[str, Any]

class GameObject:
	def __init__(
		self,
		id: int,
		x: float,
		y: float,
		x_scale_exp: int = 0,
		x_angle: int = 0,
		y_scale_exp: int = 0,
		y_angle: int = 0,
		z_layer: int = 0,
		z_order: int = 0,
		main_color: Optional[Color] = None,
		detail_color: Optional[Color] = None
	):
		self.id = id
		self.x = x
		self.y = y
		self.x_scale_exp = x_scale_exp
		self.x_angle = x_angle
		self.y_scale_exp = y_scale_exp
		self.y_angle = y_angle
		self.z_layer = z_layer
		self.z_order = z_order
		self.main_color = main_color or Color(255, 255, 255, 255, False)
		self.detail_color = detail_color or Color(255, 255, 255, 255, False)

	def bytes(self) -> bytes:
		"""Convert object data to bytes"""
		# Create format string for struct packing
		fmt = '<HffBBBBBB' + 'BBBBB' * 2  # 2 colors with 5 components each
		
		return struct.pack(
			fmt,
			self.id,
			self.x,
			self.y,
			self.x_scale_exp,
			self.x_angle,
			self.y_scale_exp,
			self.y_angle,
			self.z_layer,
			self.z_order,
			self.main_color.r,
			self.main_color.g,
			self.main_color.b,
			self.main_color.opacity,
			1 if self.main_color.blending else 0,
			self.detail_color.r,
			self.detail_color.g,
			self.detail_color.b,
			self.detail_color.opacity,
			1 if self.detail_color.blending else 0
		)

	@classmethod
	def from_bytes(cls, data: bytes) -> 'GameObject':
		"""Create GameObject instance from bytes"""
		fmt = '<HffBBBBBB' + 'BBBBB' * 2
		unpacked = struct.unpack(fmt, data)
		
		main_color = Color(
			r=unpacked[9],
			g=unpacked[10],
			b=unpacked[11],
			opacity=unpacked[12],
			blending=bool(unpacked[13])
		)
		
		detail_color = Color(
			r=unpacked[14],
			g=unpacked[15],
			b=unpacked[16],
			opacity=unpacked[17],
			blending=bool(unpacked[18])
		)
		
		return cls(
			id=unpacked[0],
			x=unpacked[1],
			y=unpacked[2],
			x_scale_exp=unpacked[3],
			x_angle=unpacked[4],
			y_scale_exp=unpacked[5],
			y_angle=unpacked[6],
			z_layer=unpacked[7],
			z_order=unpacked[8],
			main_color=main_color,
			detail_color=detail_color
		)

class ObjectManager:
	# Base-N conversion constants
	INPUT_BASE = 256
	OUTPUT_BASE = 126
	
	@staticmethod
	async def place_object(game_object: GameObject) -> Dict[str, Any]:
		"""
		Places a game object on the server
		
		Args:
			game_object (GameObject): The object to place
			
		Returns:
			Dict[str, Any]: Dictionary containing key and cooldown
			
		Raises:
			Exception: If placement fails or chunk is full
		"""
		# try:
		encoded_data = ObjectManager.encode_game_object(game_object)
		
		response = await ObjectManager.send_to_server({
			"object": encoded_data
		})
		
		# return {
		# 	"key": response.data["key"],
		# 	"cooldown": response.data["cooldown"]
		# }
		
		# except Exception as error:
		#     if getattr(error, 'details', {}).get('code') == 600:
		#         raise Exception("Chunk is full. Try deleting some objects first.")
		#     raise Exception(f"Failed to place object: {getattr(error, 'details', {}).get('message', 'Unknown error')}")

	@staticmethod
	async def delete_object(object_id: str, chunk_coords: Tuple[int, int]) -> int:
		"""
		Deletes a game object from the server
		
		Args:
			object_id (str): The ID of the object to delete
			chunk_coords (Tuple[int, int]): The coordinates of the chunk [x, y]
			
		Returns:
			int: The cooldown period after deletion
			
		Raises:
			Exception: If deletion fails
		"""
		try:
			response = await ObjectManager.send_delete_request({
				"chunkId": f"{chunk_coords[0]},{chunk_coords[1]}",
				"objId": object_id
			})
			
			return response.data["cooldown"]
			
		except Exception as error:
			raise Exception(f"Failed to delete object: {getattr(error, 'details', {}).get('message', 'Unknown error')}")

	@staticmethod
	def encode_game_object(game_object: GameObject) -> List[int]:
		"""
		Converts the game object data to encoded format
		
		Args:
			game_object (GameObject): The game object to encode
			
		Returns:
			List[int]: Encoded data as array of numbers
		"""
		bytes_data = array('B', game_object.bytes())
		return ObjectManager.convert_base(list(bytes_data), ObjectManager.INPUT_BASE, ObjectManager.OUTPUT_BASE)

	@staticmethod
	def convert_base(input_data: List[int], from_base: int, to_base: int) -> List[int]:
		"""
		Converts an array of numbers from one base to another
		
		Args:
			input_data (List[int]): Array of numbers in source base
			from_base (int): Source base
			to_base (int): Target base
			
		Returns:
			List[int]: Array of numbers in target base
		"""
		from_base_big = from_base
		to_base_big = to_base
		
		# Count leading zeros
		leading_zeros = 0
		for num in input_data:
			if num == 0:
				leading_zeros += 1
			else:
				break

		# Convert to base 10 first
		base_10_value = 0
		for i, value in enumerate(input_data):
			position = len(input_data) - 1 - i
			base_10_value += value * (from_base_big ** position)

		# Convert to target base
		result = []
		while base_10_value > 0:
			result.append(int(base_10_value % to_base_big))
			base_10_value //= to_base_big

		# Restore leading zeros
		result.extend([0] * leading_zeros)
		
		return list(reversed(result))

	@staticmethod
	async def send_to_server(data: Dict[str, Any]) -> ServerResponse:
		"""Sends the encoded object data to the server"""
		print(data)
		#return await api_client.place_object(data)

	@staticmethod
	async def send_delete_request(data: Dict[str, Any]) -> ServerResponse:
		"""Sends a delete request to the server"""
		print(data)
		#return await api_client.delete_object(data)


# Usage example:
"""
# Create and place an object:
game_object = GameObject(
	id=1,
	x=5205.0,
	y=1245.0,
	y_angle=18,
	z_layer=3
)

try:
	result = await ObjectManager.place_object(game_object)
	print(f"Object placed with key {result['key']}, cooldown: {result['cooldown']}ms")
except Exception as error:
	print(f"Error: {str(error)}")

# Delete an object:
try:
	cooldown = await ObjectManager.delete_object("object123", (0, 0))
	print(f"Object deleted, cooldown: {cooldown}ms")
except Exception as error:
	print(f"Error: {str(error)}")

# Binary serialization example:
bytes_data = game_object.bytes()
reconstructed = GameObject.from_bytes(bytes_data)
"""