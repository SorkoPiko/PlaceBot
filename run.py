# very primitive run script

import argparse, os, json, asyncio
from convert import *

# process .json file
argparser = argparse.ArgumentParser(description="Uploads generated objects")
argparser.add_argument("file", help="The file to upload")
args = argparser.parse_args()

if not os.path.exists(args.file):
	raise FileNotFoundError("File does not exist")

if not args.file.endswith(".json"):
	raise ValueError("File must be a .json file")

async def main():
    with open(args.file, "r") as file:
        data = json.load(file)

    for obj in data:
        print(obj)
        gameObj = GameObject(
            id=obj["id"],
            x=obj["x"],
            y=obj["y"],
            x_scale_exp=obj["x_scale_exp"],
            x_angle=obj["x_angle"],
            y_scale_exp=obj["y_scale_exp"],
            y_angle=obj["y_angle"],
            z_layer=obj["z_layer"],
            z_order=obj["z_order"],
            main_color=Color(**obj["main_color"]),
            detail_color=Color(**obj["detail_color"])
        )
        await ObjectManager.place_object(gameObj)

# Run the main function
asyncio.run(main())