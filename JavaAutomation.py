#made by Java#9999 for mewt .gg/mewt
#join JavaAutomation: .gg/javaw
import discord
from discord.ext import commands
import json
import aiohttp
import os
import sys
import psutil
import subprocess
import signal
from discord import Embed, Colour
from discord import Game  
from robloxapi import Client
import httpx
import asyncio
import os
import time
import subprocess
from io import BytesIO
import requests
from typing import Union 
import platform 
import importlib
from datetime import datetime
import threading

def whichPythonCommand():
    LocalMachineOS = platform.system()
    if LocalMachineOS == "win32" or LocalMachineOS == "win64" or LocalMachineOS == "Windows":
        print("This version of JavaAutomation is not supported with Windows. Please use the Windows version. Python Script ended")
        quit()
    else:
        return "python3"
    
if whichPythonCommand() == "python3":
    os.system("clear")
    
print("Welcome to JavaAutomation")
print("Device Info: " + platform.system())

#Load Settings
with open('settings.json') as f:
    settings = json.load(f)

webhook_url = settings['MISC']['WEBHOOK']['URL']
autorestart_notify_enabled = True
#Variables
ROBLOX_API_URL = "https://users.roblox.com/v1/users/authenticated"   
intents = discord.Intents.default()
intents.message_content = True    
intents.messages = True
autorestart_task = None
autorestart_minutes = None
start_time = None
print_cache = {}
discord_ids = settings['MISC']['DISCORD']['AUTHORIZED_IDS'][0]
discord_id = discord_ids
whitelist = [discord_id]
type_to_id = dict([ ("Hat", 8),
("HairAccessory", 41), ("FaceAccessory", 42),
("NeckAccessory", 43),
("ShoulderAccessory", 44),
("FrontAccessory", 45),
("BackAccessory", 46),
("WaistAccessory", 47),
("TShirtAccessory", 64),
("ShirtAccessory", 65),
("PantsAccessory", 66),
("JacketAccessory", 67),
("SweaterAccessory", 68),
("ShortsAccessory", 69)
])
serials = dict([ ("last_bought_needs_update", False),
("update_trigger", False),
("last_updated", False),
("error", None),
("status", None),
("inventory_data", [])
])

types = ''
for key in type_to_id.keys(): types += key + ','
types = types[:-1]

#Class
class MyBot(commands.AutoShardedBot):
    async def on_socket_response(self, msg):
        self._last_socket_response = time.time()

    async def close(self):
        if self._task:
            self._task.cancel()
        await super().close()

    async def on_ready(self):
        if not hasattr(self, "_task"):
            self._task = self.loop.create_task(self.check_socket())

    async def disconnectTask(self):
        if self._task:
            self._task.cancel()

    async def check_socket(self):
        while not self.is_closed():
            if time.time() - self._last_socket_response > 60:
                await self.close()
                await self.start(bot_token)
            await asyncio.sleep(5)

bot = MyBot(command_prefix='!', intents=intents)
bot._last_socket_response = time.time()


#Functions
def user_can_use_bot(user):
    return str(user.id) in whitelist or str(user) in whitelist

def bot_login(token, ready_event):
    intents = discord.Intents.default()
    intents.message_content = True  
    bot = commands.Bot(command_prefix="!",
                       intents=intents)

def is_owner(): 
    async def predicate(ctx):
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        authorized_ids = [int(x) for x in settings['MISC']['DISCORD']['AUTHORIZED_IDS']]
        return ctx.author.id in authorized_ids
    return commands.check(predicate)

def load_settings():
    with open("settings.json") as f:
        global settings
        settings = json.load(f)
    return settings
    
def restart_main_py():
    os.system("pkill -9 -f main.py")
    subprocess.Popen(["python3", 'main.py'])

async def restart_bot(ctx):
    try:
        restart_main_py()
    except Exception as e:
        pass

def testIfVariableExists(tablee, variablee):
    if tablee is dict:
        list = tablee.keys()
        for i in list:
            if i == variablee:
                return True
        return False
    else:
        if variablee in tablee:
            return True
        else:
            return False

async def send_cookie_invalid_webhook(cookie_name, command_name):
    webhook_url = settings['MISC']['WEBHOOK']['URL']
    embed = discord.Embed(
        title="Cookie check notification!",
        description=f" ``` The {cookie_name} has become invalid. Please update it by using the command !{command_name}. ```",
        color=discord.Color.red()
    )
    embed_dict = embed.to_dict()

    async with aiohttp.ClientSession() as session:
        async with session.post(
            webhook_url,
            json={
                "embeds": [embed_dict],
                "username": bot.user.name,
                "avatar_url": str(bot.user.avatar.url) if bot.user.avatar else None,
            },
        ) as response:
            if response.status != 204:
                print(f"Failed to send the embed to the webhook. HTTP status: {response.status}")

async def check_cookie(cookie):
    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
        response = await client.get(ROBLOX_API_URL, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        username = user_data["name"]
        return True, username
    else:
        return False, None

def update_settings(new_settings):
    with open("settings.json", "w") as file:
        json.dump(new_settings, file, indent=4)

def get_request(url, timeout=4, cursor=None):
    try:
        response = requests.get(url if cursor == None else url + f"&cursor={cursor}", timeout=timeout,
                                cookies={ ".ROBLOSECURITY": settings["AUTHENTICATION"]["COOKIES"][0]})
    except Exception as e:
        serials["error"] = str(e)
        print("Couldn't update inventory:", serials["error"])
        return False
    
    serials["error"] = None
    return response.json()   

def update_serial_status(message, print_msg):
    if print_msg: print(message)
    serials["status"] = message

user_id = 0

def sync_inventory(wait=2, max_retry=3, print=False):
    overall_inv_url = f"https://inventory.roblox.com/v2/users/{user_id}/inventory?assetTypes={types}&filterDisapprovedAssets=false&limit=100&sortOrder=Desc"
    __builtins__.print("Succesfully started the inventory load for the provided roblox ID")  # Call built-in print()
    type_to_oldest = {}
    item_counts = {}
    cursor = None
    retry_count = 0
    __builtins__.print("Scanning ID: " + str(user_id))

    if len(serials["inventory_data"]) == 0:
        count = 0
        iters = 100
        update_serial_status("Loading last 1000 limiteds from inventory", print)


        while count < iters:
            response = get_request(overall_inv_url, cursor=cursor)
            time.sleep(wait)
            if not response:
                retry_count += 1
                if retry_count <= max_retry:
                    update_serial_status(serials["error"] + ". Retrying", print)
                    continue
                else:
                    update_serial_status("Too many retries", print)
                    return False
            cursor = response.get("nextPageCursor", None)

            if testIfVariableExists(response, "data"):
                data = response["data"]
    
                for item in data:
                    this_seconds = datetime.fromisoformat(item["created"]).timestamp()
                    type_name = item["assetType"]
                    asset_id = item["assetId"]
    
                    if asset_id in item_counts: item_counts[asset_id] += 1
                    else: item_counts[asset_id] = 1
                    if type_name not in type_to_oldest or this_seconds < type_to_oldest[type_name][0]:
                        type_to_oldest[type_name] = [this_seconds, asset_id]

                count += 1
                if cursor == None: break
            else:
                error = response["errors"]
                __builtins__.print("There's an issue while loading your inventory. This can happen if your inventory is private or not viewable with the API. Skipped section")
                count += 1
                if cursor == None: break
    else:
        resolved = False
        update_serial_status("Updating the inventory with the latest items...", print)

        while not resolved:
            response = get_request(overall_inv_url, cursor=cursor)
            time.sleep(wait)
            if not response:
                retry_count += 1
                if retry_count <= max_retry:
                    update_serial_status(serials["error"] + ". Retrying", print)
                    continue
                else:
                    update_serial_status("Too many retries", print)
                    return False
            current_recent = serials["inventory_data"][0]["created_timestamp"]
            cursor = response["nextPageCursor"]

            if testIfVariableExists(response, "data"):
                data = response["data"]
    
                for item in data:
                    this_seconds = datetime.fromisoformat(item["created"]).timestamp()
                    if this_seconds <= current_recent:
                        resolved = True
                        break
                    type_name = item["assetType"]
                    asset_id = item["assetId"]
    
                    if asset_id in item_counts: item_counts[asset_id] += 1
                    else: item_counts[asset_id] = 1
                    if type_name not in type_to_oldest or this_seconds < type_to_oldest[type_name][0]:
                        type_to_oldest[type_name] = [this_seconds, asset_id]
    
                if cursor == None: resolved = True
            else:
                error = response["errors"]
                __builtins__.print("There's an issue while loading your inventory. This can happen if your inventory is private or not viewable with the API. Skipped section")
                count += 1
                if cursor == None: break
    
    to_add = []
    for type_name, oldest in type_to_oldest.items():
        type_id = type_to_id[type_name]
        url = f"https://inventory.roblox.com/v2/users/{user_id}/inventory/{type_id}?limit=100&sortOrder=Desc"
        cursor = None
        resolved = False
        retry_count = 0
        update_serial_status(f"Loading: {type_name}", print)

        while not resolved:
            response = get_request(url, cursor=cursor)
            time.sleep(wait)
            if not response:
                retry_count += 1
                if retry_count <= max_retry:
                    update_serial_status(serials["error"] + ". Retrying", print)
                    continue
                else:
                    update_serial_status("Too many retries", print)
                    return False
            cursor = response["nextPageCursor"]
            data = response["data"]
            curr_count = 0
            end_count = item_counts[oldest[1]]

            for item in data:
                serial = item["serialNumber"] if "serialNumber" in item else "none"
                if item["assetId"] == oldest[1]:
                    curr_count += 1
                    if curr_count == end_count:
                        resolved = True
                        break
                if item["collectibleItemId"] != None:
                    this_seconds = datetime.fromisoformat(item["created"]).timestamp()
                    to_add.append({
                            "asset_id": item["assetId"],
                            "asset_name": item["assetName"],
                            "serial": serial,
                            "created_timestamp": this_seconds
                        })

            if cursor == None: resolved = True

    to_add.sort(key=lambda obj : obj["created_timestamp"], reverse=True)
    serials["inventory_data"] = to_add + serials["inventory_data"]

    update_serial_status("Finished updating", print)
    serials["last_updated"] = time.time()
    return True

def get_user_id_from_cookie(cookie):
    api_url = "https://users.roblox.com/v1/users/authenticated"
    headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
    response = get_request(url=api_url)
    user_data = response
    if testIfVariableExists(user_data, "id"):
        return user_data["id"]
    else:
        return 90457282


print("Loading inventory data from roblox...\n")
user_id = get_user_id_from_cookie(settings["AUTHENTICATION"]["COOKIES"][0])
print("Got ID from First Cookie: " + str(user_id))
sync_inventory(wait=1, max_retry=8, print=True)


#Events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        embed = Embed(title="Error", description=" ```Only the owner can use such commands. ```", color=Colour.red())
        await ctx.send(embed=embed)

@bot.event
async def on_ready():
    global start_time
    start_time = time.time()
    os.system('cls' if os.name == 'nt' else 'clear')

    print("JavaAutomation is now running in background!")
    await bot.change_presence(activity=Game(name="!info"))
    print(f'Logged in as bot: {bot.user.name}')

    checks = 0
    while True:
        checks += 1

        # Refresh if there was change to cookie.
        newSettings = load_settings()
        cookies = newSettings["AUTHENTICATION"]["COOKIES"]
        details_cookie = newSettings["AUTHENTICATION"]["DETAILS_COOKIE"]

        # Check all cookies
        for i, cookie in enumerate(cookies, start=1):
            cookie_valid, username = await check_cookie(cookie)
            if cookie_valid == False:
                print(f"WARNING! Cookie #{i} is detected invalid!")
                await send_cookie_invalid_webhook(f"COOKIE_{i}", f"cookie{i}")

        # Check DETAILS_COOKIE
        details_cookie_valid, details_username = await check_cookie(details_cookie)
        if details_cookie_valid == False:
            print(f"WARNING! Details Cookie is detected invalid!")
            await send_cookie_invalid_webhook("DETAILS_COOKIE", "altcookie")

        # Wait for 5 minutes before checking again
        await asyncio.sleep(300)




#Commands:

#Invite command
@bot.command()
async def invite(ctx):
    response_message = "https://discord.gg/javaw"
    await ctx.send(response_message)

#prefix command
@bot.command()
@is_owner()
async def prefix(ctx, new_prefix: str):
    bot.command_prefix = new_prefix
    await bot.change_presence(activity=Game(name=f"{new_prefix}info"))
    embed = discord.Embed(
        title="Prefix Update",
        description=f"```Successfully changed the command prefix to: {new_prefix}```\n \nNote that for a better user experience the prefix dosen't save, so if you close the sniper the prefix will go back to !",
        color=discord.Color.from_rgb(255, 182, 193)
    )
    await ctx.send(embed=embed)

#screenshot
@bot.command()
@is_owner()
async def screenshot(ctx):
    # Capture the screenshot
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
    except ImportError:
        await ctx.send("Failed to capture screenshot. Please make sure you have the Pillow library installed.")
        return

    # Convert the image to bytes
    image_bytes = BytesIO()
    screenshot.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    # Read the webhook URL from the settings
    webhook_url = settings['MISC']['WEBHOOK']['URL']

    # Create a Discord file object from the image bytes
    file = discord.File(image_bytes, filename='screenshot.png')

    # Send the screenshot as an embed to the webhook
    embed = discord.Embed()
    embed.set_image(url='attachment://screenshot.png')

    async with ctx.typing():
        try:
            await ctx.send(file=file, embed=embed)
        except discord.HTTPException:
            await ctx.send("Failed to send the screenshot to the webhook.")

#webhook command
@bot.command() 
@is_owner()
async def webhook(ctx, webhook_url: str):
    
    with open('settings.json', 'r') as f:
        settings = json.load(f)


    
    settings['MISC']['WEBHOOK']['URL'] = webhook_url

    
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    
    embed = discord.Embed(
        title="Success!",
        description=" ``` This webhook has been succesfully set and will be used for the next notifications! ```",
        color=discord.Color.from_rgb(255, 182, 193)
    )

    
    embed_dict = embed.to_dict()

    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            webhook_url,
            json={
                "embeds": [embed_dict],
                "username": bot.user.name,
                "avatar_url": str(bot.user.avatar.url) if bot.user.avatar else None,
            },
        ) as response:
            if response.status != 204:
                await ctx.send(f"Failed to send the embed to the webhook. HTTP status: {response.status}")
                return
            
            if await restart_main_py():
               print("Succesfully restarted mewt after updating the webhook")
            else:
               print("Error while trying to restart mewt after updating the webhook.")

#onlyfree command
@bot.command(name='onlyfree')  
@is_owner()
async def onlyfree(ctx, status: str):
    if status.lower() not in ['on', 'off']:
        embed = Embed(title='Error', description='```Please use !onlyfree on or !onlyfree off```', color=Colour.from_rgb(255, 0, 0))
        await ctx.send(embed=embed)
        return

  
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    
    if status.lower() == 'on':
        settings['MISC']['WATCHER']['ONLY_FREE'] = True
        description = '```Mewt sniper will now only snipe free items. Run !onlyfree off to deactivate this setting.```'
    else:
        settings['MISC']['WATCHER']['ONLY_FREE'] = False
        description = '```Mewt sniper will now snipe paid items too. Run !onlyfree on to activate this setting.```'

    
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    embed = Embed(title='Success!', description=f'```{description}```', color=Colour.from_rgb(255, 182, 193))
    await ctx.send(embed=embed)

    if await restart_main_py():
            print("Succesfully restarted mewt after updating the onlyfree option")
    else:
            print("Error while trying to restart mewt after updating the onlyfree option.")

#speed command
@bot.command(name='speed')  
@is_owner()
async def speed(ctx, new_speed: str):
    try:
        new_speed_float = float(new_speed)
    except ValueError:
        embed = Embed(title=' ```The scan speed must be a number. ```', color=Colour.from_rgb(255, 0, 0))
        await ctx.send(embed=embed)
        return

    
    with open('settings.json', 'r') as f:
        settings = json.load(f)
    
    if new_speed_float.is_integer():
        new_speed_str = str(int(new_speed_float))
        new_speed_value = int(new_speed_float)
    else:
        new_speed_str = str(new_speed_float)
        new_speed_value = new_speed_float

   
    settings['MISC']['WATCHER']['SCAN_SPEED'] = new_speed_value

    
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    embed = Embed(title='Success!', description=f'```New scan speed: {new_speed_str}```', color=Colour.from_rgb(255, 182, 193))
    await ctx.send(embed=embed)

    if await restart_main_py():
            print("Succesfully restarted mewt after updating the speed")
    else:
            print("Error while trying to restart mewt after updating the speed.")


#inventory command        
@bot.command()
@is_owner()  
async def inventory(ctx, *args):
    if len(serials["inventory_data"]) == 0:
        await ctx.reply("Still working...")
    if not user_can_use_bot(ctx.message.author): return  
    cache = serials["inventory_data"]
    if not user_id:
        await ctx.reply("Set the robloxID by using the robloxid command.")    
        return
    if len(cache) == 0:
        await ctx.reply("inventory has still not loaded")
        return
        
    color = discord.Color.from_rgb(255, 182, 193)
    page = 1
    max_page = (len(cache) / 10).__ceil__()
        
    avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"    
    async with httpx.AsyncClient() as client:
        avatar_response = await client.get(avatar_api_url)  
    avatar_data = avatar_response.json()    
    avatar_url = avatar_data["data"][0]["imageUrl"]
    username_api_url = f"https://users.roblox.com/v1/users/{user_id}"
    async with httpx.AsyncClient() as client:
     response = await client.get(username_api_url)
    username = response.json()["name"]

    embed = discord.Embed(title=f"{username}'s inventory:", color=color)
 
    embed.set_footer(text=f".gg/javaw {page}/{max_page}")
    if len(args) > 0:
            if not args[0].isnumeric():
                await ctx.reply("The page must be a numeric value.")
                return
            if int(args[0]) > max_page:
                await ctx.reply(f"You went too far, your current maximum page is:{max_page}")
                return
            page = int(args[0])
    embed = discord.Embed(title=f"Roblox UserID inventory:", color=color)  
    embed.set_footer(text=f".gg/javaw {page}/{max_page}")

    desc = f"Total cached: {len(cache)}\n"
    if serials["last_bought_needs_update"] != False or serials["update_trigger"]:
            if serials["last_bought_needs_update"] != False: desc += f"Items bought <t:{int(serials['last_bought_needs_update'])}:R>, awaiting update...\n"
            elif serials["update_trigger"]: desc += "Update triggered, awaiting update...\n"
            desc += f"Status: {serials['status']}\n"
            desc += f"Errors: {serials['error'] if serials['error'] != None else 'none'}\n"
    desc += f"Last updated: <t:{int(serials['last_updated'])}:R>\n\n"
        
    page_list = cache[(page - 1) * 10 : page * 10]
    for item in page_list:
            desc += f"[{item['asset_name']}](https://roblox.com/catalog/{item['asset_id']})\n"
            desc += f"`#{item['serial']}` | <t:{int(item['created_timestamp'])}:R>\n\n"

    embed.description = desc[:4000]
    embed.set_thumbnail(url=avatar_url)
    await ctx.send(embed=embed)





#updateinventory
@bot.command(name='updateinv')
@is_owner()
async def updateinv(ctx):
        if not user_can_use_bot(ctx.message.author): return
        if serials["update_trigger"] or serials["last_bought_needs_update"]:
            await ctx.reply("Already updating....")
            return    
        await ctx.reply("Starting update. Monitor progress with the inventory command")
        serials["update_trigger"] = True

#info command
@bot.command()
async def info(ctx):
    prefix = bot.command_prefix
    embed = discord.Embed(
        title="JavaExtension Commands:",
        color=discord.Color.from_rgb(255, 182, 193)
    )
    embed.add_field(name=f"{prefix}prefix", value="To change your prefix to anything you want (**When you close it will go back to !**)", inline=False)
    embed.add_field(name=f"{prefix}cookie", value="To change your main cookie", inline=False)
    embed.add_field(name=f"{prefix}cookie2", value="To change secondary main cookie", inline=False)
    embed.add_field(name=f"{prefix}altcookie", value="To change your alt cookie", inline=False)
    embed.add_field(name=f"{prefix}robloxid", value="To add the robloxID for the inventory loading", inline=False)
    embed.add_field(name=f"{prefix}inventory", value="To view the inventory and serial of the robloxID you have selected.", inline=False)
    embed.add_field(name=f"{prefix}updateinv", value="To update the inventory [May not be working]", inline=False)
    embed.add_field(name=f"{prefix}check main", value="To check if your main cookie is valid", inline=False)
    embed.add_field(name=f"{prefix}check alt", value="To check if your alt cookie is valid", inline=False)
    embed.add_field(name=f"{prefix}addowner", value="To add a new ownerID", inline=False)
    embed.add_field(name=f"{prefix}removeowner", value="To remove an ownerID", inline=False)
    embed.add_field(name=f"{prefix}owners", value="to view the owners", inline=False)
    embed.add_field(name=f"{prefix}webhook", value="To change your webhook", inline=False)
    embed.add_field(name=f"{prefix}token", value="To change your Discord bot token", inline=False)
    embed.add_field(name=f"{prefix}speed", value="To change your speed", inline=False)
    embed.add_field(name=f"{prefix}onlyfree off", value="To snipe paid items too", inline=False)
    embed.add_field(name=f"{prefix}onlyfree on", value="To snipe free items only", inline=False)
    embed.add_field(name=f"!add", value="To add an id to the watchlist **(only works with prefix !)**", inline=False)
    embed.add_field(name=f"!remove", value="To remove an id to the watchlist **(only works with prefix !)**", inline=False)
    embed.add_field(name=f"!watching", value="To see the list of the IDS being watched **(only works with prefix !)**", inline=False)
    embed.add_field(name=f"!stats", value="To see your current stats on the sniper **(Only works with ! prefix)**", inline=False)
    embed.add_field(name=f"{prefix}removeall", value="Remove all the current watching ids", inline=False)
    embed.add_field(name=f"{prefix}more", value="To see more infos about your current setup", inline=False)
    embed.add_field(name=f"{prefix}restart", value="To restart the mewt sniper", inline=False)
    embed.add_field(name=f"{prefix}autorestart (minutes)", value="Starts autorestarting the bot every tot minutes, example {prefix}restart 20", inline=False)
    embed.add_field(name=f"{prefix}autorestart off", value="Stops the autorestarter", inline=False)
    embed.add_field(name=f"{prefix}autorestart", value="Shows you the autorestart status", inline=False)
    embed.add_field(name=f"{prefix}screenshot", value="To take a screenshot of the current host machine", inline=False)
    embed.add_field(name=f"{prefix}update", value="Update JavaAutomation to latest version in GitHub.", inline=False)
    embed.add_field(name=f"{prefix}shutdown", value="Shutdown Bot and mewt", inline=False)
    embed.add_field(name=f"{prefix}invite", value="To join JavaAutomation server", inline=False)
    embed.set_footer(text="Developed by: Java#9999 \nHelped by: Lag#1234")
    await ctx.send(embed=embed)

#remove all command
@bot.command()
@is_owner()
async def removeall(ctx):
    settings = load_settings()
    settings["MISC"]["WATCHER"]["ITEMS"] = []
    update_settings(settings)

    embed = Embed(title="Items Removed", description="All items have been removed.", color=discord.Color.from_rgb(255, 182, 193))
    await ctx.send(embed=embed)

    if await restart_main_py():
            print("Bot restarted after updating the cookie.")
    else:
            print("Error while trying to restart the bot after updating the cookie.")

#add owner
@bot.command()
@is_owner()
async def addowner(ctx, user_id: int):
    with open('settings.json', 'r') as file:
        settings = json.load(file)
    
    authorized_ids = settings["MISC"]["DISCORD"]["AUTHORIZED_IDS"]
    
    if str(user_id) not in authorized_ids:
        authorized_ids.append(str(user_id))
        settings["MISC"]["DISCORD"]["AUTHORIZED_IDS"] = authorized_ids
        
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=4)
        
        embed = discord.Embed(
            title="Owner Added",
            description=f"```User ID {user_id} has been added as an owner.```",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Error",
            description=f"```User ID {user_id} is already an owner.```",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        await ctx.send(embed=embed)

@bot.command()
@is_owner()
async def removeowner(ctx, user_id: int):
    with open('settings.json', 'r') as file:
        settings = json.load(file)
    authorized_ids = settings["MISC"]["DISCORD"]["AUTHORIZED_IDS"]
    if str(user_id) in authorized_ids:
        authorized_ids.remove(str(user_id))
        settings["MISC"]["DISCORD"]["AUTHORIZED_IDS"] = authorized_ids
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=4)
        embed = discord.Embed(
            title="Owner Removed",
            description=f"```User ID {user_id} has been removed as an owner.```",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Error",
            description=f"```User ID {user_id} is not an owner.```",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        await ctx.send(embed=embed)


#owners
@bot.command()
@is_owner()
async def owners(ctx):
    with open('settings.json', 'r') as file:
        settings = json.load(file)
    authorized_ids = settings["MISC"]["DISCORD"]["AUTHORIZED_IDS"]

    # Create an embed with the specified color
    embed = discord.Embed(
        title="Current Owners",
        color=discord.Color.from_rgb(255, 182, 193)
    )

    # Add a field for the owners
    owners_str = "\n".join(authorized_ids)
    embed.add_field(name="Owners", value=owners_str, inline=False)

    # Send the embed message
    await ctx.send(embed=embed)

#updatejava
@bot.command()
@is_owner()
async def update(ctx):
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    # Create an embed with the specified color
    embed = discord.Embed(
        title="Updating JavaAutomation for latest updates...",
        color=discord.Color.from_rgb(255, 182, 193)
    )

    # Send the embed message
    await ctx.send(embed=embed)
    print("Launching macOS/Linux Version...")
    url = "https://raw.githubusercontent.com/EfazDev/JavaAutomationLinux/main/JavaAutomation.py"
    time.sleep(2)
    print("Locating Request from URL...")
    resp = requests.get(url)
    if resp.status_code == 200:
        print("Finished GET Request, saving script...")
        content = resp.text
        if os.path.exists("ExtenderRunner.py"):
            with open("ExtenderRunner.py", "w", encoding="utf-8") as f:
                f.write(content)
            print("Finished Writing Script")
            print("Running Script...")
            os.system("pkill -9 -f main.py")
            subprocess.Popen(["python3", 'ExtenderRunner.py'])
            __builtins__.print("Finished Running, ending launcher, mewt sniper and this script...")
            exit()
        else:
            with open("JavaAutomation.py", "w", encoding="utf-8") as f:
                f.write(content)
            print("Finished Writing Script")
            print("Running Script...")
            os.system("pkill -9 -f main.py")
            subprocess.Popen(["python3", 'JavaAutomation.py'])
            __builtins__.print("Finished Running, ending launcher, mewt sniper and this script...")
            exit()
    else:
        print("Server returned unknown status code. Extension not runned")

#restart command
@bot.command()
@is_owner()
async def shutdown(ctx):
    try:
        embed = Embed(title="Shutting down Mewt and JavaAutomation..", description="", color=Colour.from_rgb(255, 182, 193))
        await ctx.send(embed=embed)
        if os.path.exists("ExtenderRunner.py"):
            os.system("pkill -9 -f main.py")
            __builtins__.print("Shutting down JavaAutomation...")
            exit()
        else:
            os.system("pkill -9 -f main.py")
            __builtins__.print("Shutting down JavaAutomation...")
            exit()
    except Exception as e:
        embed = Embed(title="Error", description="An error occurred while trying to shutdown the bot: {}".format(str(e)), color=Colour.red())
        await ctx.send(embed=embed)

@bot.command()
@is_owner()
async def restart(ctx):
    try:
        restart_main_py()
        embed = Embed(title="Success!", description="Successfully restarted the bot.", color=Colour.from_rgb(255, 182, 193))
        await ctx.send(embed=embed)
    except Exception as e:
        embed = Embed(title="Error", description="An error occurred while trying to restart the bot: {}".format(str(e)), color=Colour.red())
        await ctx.send(embed=embed)

#More command
@bot.command()
@is_owner()
async def more(ctx):
    settings = load_settings()

    
    main_cookie = settings["AUTHENTICATION"]["COOKIES"][0]
    details_cookie = settings["AUTHENTICATION"]["DETAILS_COOKIE"]
    owner_id = settings['MISC']['DISCORD']['AUTHORIZED_IDS']
    onlyfree = settings['MISC']['WATCHER']['ONLY_FREE']
    autorestart_status = "Off" if autorestart_task is None or autorestart_task.cancelled() else f"{autorestart_minutes} minutes"
    scan_speed = settings['MISC']['WATCHER']['SCAN_SPEED']
    prefix = bot.command_prefix
    items = settings["MISC"]["WATCHER"]["ITEMS"]
    watching = ', '.join(str(item) for item in items)

    main_cookie_valid, main_username = await check_cookie(main_cookie)
    details_cookie_valid, details_username = await check_cookie(details_cookie)

    if start_time is not None:
        runtime = int(time.time() - start_time)
        minutes = runtime // 60
        seconds = runtime % 60
        days = minutes // 1440
        minutes = minutes % 1440
        runtime = f"{days} days, {minutes} minutes and {seconds} seconds"
    else:
        runtime = "Unknown"

    embed = discord.Embed(title="More about you:", color=discord.Color.from_rgb(255, 182, 193))
    embed.add_field(name="Prefix:", value=prefix, inline=False)
    embed.add_field(name="Roblox main:", value=main_username if main_cookie_valid else "Invalid cookie", inline=False)
    embed.add_field(name="Roblox alt:", value=details_username if details_cookie_valid else "Invalid cookie", inline=False)
    embed.add_field(name="Current owner id:", value=owner_id, inline=False)
    embed.add_field(name="Onlyfree:", value="On" if onlyfree else "Off", inline=False)
    embed.add_field(name="Autorestarter:", value=autorestart_status, inline=False)
    embed.add_field(name="Scan speed:", value=scan_speed, inline=False)
    embed.add_field(name="Watching:", value=watching if watching else "No items", inline=False)
    embed.add_field(name="Runtime:", value=runtime, inline=False)
    embed.set_footer(text="A bot by Java#9999")

    await ctx.send(embed=embed)

#cookie command
@bot.command()
@is_owner()
async def cookie(ctx, new_cookie: str):
    
    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={new_cookie}"}
        response = await client.get(ROBLOX_API_URL, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        username = user_data["name"]
        user_id = user_data["id"]

        
        avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        async with httpx.AsyncClient() as client:
            avatar_response = await client.get(avatar_api_url)
        avatar_data = avatar_response.json()
        avatar_url = avatar_data["data"][0]["imageUrl"]

        
        with open('settings.json', 'r') as f:
            settings = json.load(f)

        
        settings["AUTHENTICATION"]["COOKIES"][0] = new_cookie

        
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)

        
        embed = discord.Embed(
            title="MAIN Cookie Update",
            description=f" ```The MAIN cookie was valid for the username: {username}```\n  \n **If the bot dosen't react to !stats it means that either your main/alt cookie was invalid. In this case update them.** ",
            color=discord.Color.from_rgb(255, 182, 193)
        )

       
        embed.set_thumbnail(url=avatar_url)

        
        await ctx.send(embed=embed)

        
        if await restart_main_py():
            print("Bot restarted after updating the cookie.")
        else:
            print("Error while trying to restart the bot after updating the cookie.")

    else:
        
        embed = discord.Embed(
            title="Error",
            description=" ```The cookie you have input was invalid. ```",
            color=discord.Color.red()
        )

        
        await ctx.send(embed=embed)











@bot.command()
@is_owner()
async def cookie2(ctx, new_cookie: str):
    
    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={new_cookie}"}
        response = await client.get(ROBLOX_API_URL, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        username = user_data["name"]
        user_id = user_data["id"]

        
        avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        async with httpx.AsyncClient() as client:
            avatar_response = await client.get(avatar_api_url)
        avatar_data = avatar_response.json()
        avatar_url = avatar_data["data"][0]["imageUrl"]

        
        with open('settings.json', 'r') as f:
            settings = json.load(f)

        
        if len(settings["AUTHENTICATION"]["COOKIES"]) >= 2:
            settings["AUTHENTICATION"]["COOKIES"][1] = new_cookie
        else:
            settings["AUTHENTICATION"]["COOKIES"].append(new_cookie)

        
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)

        
        embed = discord.Embed(
            title="SECONDARY Cookie Update",
            description=f" ```The SECONDARY cookie was valid for the username: {username}```\n  \n **If the bot doesn't react to !stats it means that either your main/alt cookie was invalid. In this case update them.** ",
            color=discord.Color.from_rgb(255, 182, 193)
        )

       
        embed.set_thumbnail(url=avatar_url)

        
        await ctx.send(embed=embed)

        
        if await restart_main_py():
            print("Bot restarted after updating the cookie.")
        else:
            print("Error while trying to restart the bot after updating the cookie.")

    else:
        
        embed = discord.Embed(
            title="Error",
            description=" ```The cookie you have input was invalid. ```",
            color=discord.Color.red()
        )

        
        await ctx.send(embed=embed)


#altcookie command
@bot.command() 
@is_owner()
async def altcookie(ctx, new_cookie: str):
    
    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={new_cookie}"}
        response = await client.get(ROBLOX_API_URL, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        username = user_data["name"]
        user_id = user_data["id"]

        
        avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        async with httpx.AsyncClient() as client:
            avatar_response = await client.get(avatar_api_url)
        avatar_data = avatar_response.json()
        avatar_url = avatar_data["data"][0]["imageUrl"]

        
        with open('settings.json', 'r') as f:
            settings = json.load(f)

        
        settings["AUTHENTICATION"]["DETAILS_COOKIE"] = new_cookie

        
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)

       
        embed = discord.Embed(
            title="ALT Cookie Update",
            description=f" ```The ALT cookie was valid for the username: {username} ```\n  \n **If the bot dosen't react to !stats it means that either your main/alt cookie was invalid. In this case update them.** '",
            color=discord.Color.from_rgb(255, 182, 193)
        )

        
        embed.set_thumbnail(url=avatar_url)

        
        await ctx.send(embed=embed)

         
        if await restart_main_py():
            print("Bot restarted after updating the ALT cookie.")
        else:
            print("Error while trying to restart the bot after updating the cookie.")


    else:
        
        embed = discord.Embed(
            title="Error",
            description=" ```The cookie you have input was invalid. ```",
            color=discord.Color.red()
        )

       
        await ctx.send(embed=embed)


#token command
@bot.command()  
@is_owner()
async def token(ctx, new_token: str):
    
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    
    settings['MISC']['DISCORD']['TOKEN'] = new_token

    
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    
    embed = discord.Embed(
        title="Token Update",
        description=" ``` Successfully changed the discord bot TOKEN, make sure that you have invited the new bot to the server. ```",
        color=discord.Color.from_rgb(255, 182, 193)
    )


    
    await ctx.send(embed=embed)

    if await restart_main_py():
            print("Bot restarted after updating the token.")
    else:
            print("Error while trying to restart the bot after updating the token.")

#Autorestart command
@bot.command()
@is_owner()
async def autorestart(ctx, minutes: Union[int, str] = None):
    global autorestart_task, autorestart_minutes
    
    if minutes is None:
        # If no minutes provided, display current autorestart status
        if autorestart_task is not None and not autorestart_task.cancelled():
            embed = Embed(title="Autorestart Status", color=Colour.from_rgb(255, 182, 193))
            embed.add_field(name="Status", value="Autorestart is currently enabled.")
            embed.add_field(name="Minutes", value=f"Restarting every {autorestart_minutes} minutes.")
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Autorestart Status", color=Colour.from_rgb(255, 182, 193))
            embed.add_field(name="Status", value="Autorestart is currently disabled.")
            await ctx.send(embed=embed)
    elif isinstance(minutes, str) and minutes.lower() == "off":
        # Disable autorestart
        if autorestart_task is not None and not autorestart_task.cancelled():
            autorestart_task.cancel()
            autorestart_task = None
            autorestart_minutes = None
            embed = Embed(title="Autorestart Disabled", color=Colour.from_rgb(255, 182, 193))
            embed.add_field(name="Status", value="Autorestart has been disabled.")
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Autorestart Disabled", color=Colour.from_rgb(255, 182, 193))
            embed.add_field(name="Status", value="Autorestart is already disabled.")
            await ctx.send(embed=embed)
    elif isinstance(minutes, int) and minutes == 0:
        # If minutes is 0, disable autorestart
        if autorestart_task is not None and not autorestart_task.cancelled():
            autorestart_task.cancel()
            autorestart_task = None
            autorestart_minutes = None
            embed = Embed(title="Autorestart Disabled", color=Colour.from_rgb(255, 182, 193))
            embed.add_field(name="Status", value="Autorestart has been disabled.")
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Autorestart Disabled", color=Colour.from_rgb(255, 182, 193))
            embed.add_field(name="Status", value="Autorestart is already disabled.")
            await ctx.send(embed=embed)
    else:
        # Enable or update autorestart
        if autorestart_task is not None and not autorestart_task.cancelled():
            autorestart_task.cancel()
        
        autorestart_task = bot.loop.create_task(autorestart_task_fn(minutes, ctx))
        autorestart_minutes = minutes

        embed = Embed(title="Autorestart Enabled", color=Colour.from_rgb(255, 182, 193))
        embed.add_field(name="Status", value="Autorestart has been enabled.")
        embed.add_field(name="Minutes", value=f"Restarting every {minutes} minutes.")
        await ctx.send(embed=embed)

async def autorestart_task_fn(minutes: int, ctx):
    while True:
        await asyncio.sleep(minutes * 60)
        await restart_bot(ctx)





@bot.command()
@is_owner()  
async def robloxid(ctx, new_id: int):
    global user_id
    user_id = new_id
        
    # Clear cached inventory data
    serials["inventory_data"] = []
    
    # Send loading message    
    embed = discord.Embed(title="Loading...", description="Loading the user inventory....wait for my notification and run !inventory again.", color=Colour.orange())
    await ctx.send(embed=embed)
    
    # Reload inventory data    
    sync_inventory(wait=1, max_retry=8, print=True)
    
    embed = discord.Embed(title="Roblox ID Updated!", description=f"The Roblox ID has been updated to: `{new_id}` and the inventory cache has been repopulated.", color=Colour.from_rgb(255, 182, 193))

    await ctx.send(embed=embed)

#cookie check
@bot.command()
@is_owner()
async def check(ctx, cookie_type: str):
    if cookie_type not in ['main', 'alt']:
        await ctx.send('Invalid cookie type. Must be `main` or `alt`.')
        return
    
    with open('settings.json') as f:
        settings = json.load(f)
        
    if cookie_type == 'main':
        cookies = settings["AUTHENTICATION"]["COOKIES"]
    else: 
        cookies = [settings["AUTHENTICATION"]["DETAILS_COOKIE"]]
    
    for cookie in cookies:
        valid, username = await check_cookie(cookie)

        if valid == True:
            user_id = await get_user_id_from_cookie(cookie)  # Get the user ID from the cookie
            avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
            async with httpx.AsyncClient() as client:
                avatar_response = await client.get(avatar_api_url)
            avatar_data = avatar_response.json()
            avatar_url = avatar_data["data"][0]["imageUrl"]

            embed = Embed(title="Cookie check result:", color=Colour.from_rgb(255, 182, 193))
            embed.add_field(name="Username", value=username)
            embed.add_field(name="Cookie type", value=cookie_type.title())
            embed.set_thumbnail(url=avatar_url)
            await ctx.send(embed=embed)

        else:
            embed = Embed(title="Cookie check result:", description="The {} cookie in your settings was invalid".format(cookie_type), color=Colour.red()) 
            await ctx.send(embed=embed)

# Run main.py when JavaAutomation.py is executed
subprocess.Popen(["python3", 'main.py'])

# Get the bot token from the settings
bot_token = settings['MISC']['DISCORD']['TOKEN']

# Run the bot using the token from the settings
bot.run(bot_token)


def searchinventory(): 
    while True:
        if not serials["last_bought_needs_update"] and not serials["update_trigger"]: continue
        if time.time() - serials["last_bought_needs_update"] > 5 or serials["update_trigger"]:
            sync_inventory()
            serials["last_bought_needs_update"] = False
            serials["update_trigger"] = False
        time.sleep(0.5)
if user_id:
    sync_inventory()
    serials_thread = threading.Thread(target=searchinventory, daemon=True)
    serials_thread.start()
        

try:
    if not user_id: print("The robloxID was not found. use robloxid command to update it.")
    else:
        sync_inventory(wait=1, max_retry=8, print=True)
        print("Collecting every inventory data for ID: {user_id}")
        serials_thread = threading.Thread(target=searchinventory, daemon=True)
        serials_thread.start()

    time.sleep(2)
except (KeyboardInterrupt, SystemExit):
    print("Exit status...")
    sys.exit(1)

while True:
    webhook_color = discord.Color.from_rgb(255, 182, 193)
    stage = 0
