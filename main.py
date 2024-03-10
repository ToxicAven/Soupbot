from cleaninty.ctr.simpledevice import SimpleCtrDevice
from cleaninty.ctr.soap.manager import CtrSoapManager
from pyctr.type.exefs import ExeFSReader
from cleaninty.ctr.soap import helpers
from io import BytesIO, StringIO
from dotenv import load_dotenv
import discord
import json
import os

bot = discord.Bot()
load_dotenv()

@bot.slash_command(description="Generate a consoles soap key")
async def genjson(ctx: discord.ApplicationContext,
                    secinfo: discord.Option(discord.Attachment, "secinfo.bin, SecureInfo_A"),
                    otp: discord.Option(discord.Attachment, "otp.bin"), 
                    country: discord.Option(str, "Required for U and E regions", required=False)):
    await ctx.defer(ephemeral=True)

    try:
        soapJson = SimpleCtrDevice.generate_new_json(
            otp_data=await otp.read(),
            secureinfo_data=await secinfo.read(),
            country=country,
        )
    except Exception as e:
        await ctx.respond(ephemeral=True, content=f"Cleaninty error:\n```\n{e}\n```")
        print(f"Cleaninty: {e}")
        return
    
    try:
        await ctx.respond(ephemeral=True, file=discord.File(fp=StringIO(soapJson), filename="soap.json"))
    except:
        await ctx.respond(ephemeral=True, content="Failed to respond with soap.json")


@bot.slash_command(description="Generate a consoles soap key using essential.exefs")
async def genjsonessential(ctx: discord.ApplicationContext,
                           essential: discord.Option(discord.Attachment, "essential.exefs"),
                           country: discord.Option(str, "Required for U and E regions", required=False)):
    await ctx.defer(ephemeral=True)
    
    try:
        reader = ExeFSReader(BytesIO(await essential.read()))
    except:
        await ctx.respond(ephemeral=True, content="Failed to read essential")
        return
    
    if not "secinfo" and "otp" in reader.entries:
        await ctx.respond(ephemeral=True, content="Invalid essential")
        return

    try:
        soapJson = SimpleCtrDevice.generate_new_json(
            otp_data=reader.open("otp").read(),
            secureinfo_data=reader.open("secinfo").read(),
            country=country
        )
    except Exception as e:
        await ctx.respond(ephemeral=True, content=f"Cleaninty error:\n```\n{e}\n```")
        print(f"Cleaninty: {e}")
        return
    
    try:
        await ctx.respond(ephemeral=True, file=discord.File(fp=StringIO(soapJson), filename="soap.json"))
    except:
        await ctx.respond(ephemeral=True, content="Failed to respond with soap.json")

@bot.slash_command(description="check console registry")
async def checkreg(ctx : discord.ApplicationContext, jsonfile: discord.Option(discord.Attachment, "soap.json")):
    await ctx.defer(ephemeral=True)

    try:
        jsonStr = await jsonfile.read()
        jsonStr = jsonStr.decode("utf-8")
        json.loads(jsonStr) # Validate the json, output useless
    except:
        await ctx.respond(ephemeral = True, content="Failed to load json")
        return

    try:
        dev = SimpleCtrDevice(json_string=jsonStr)
        soapMan = CtrSoapManager(dev, False)
        helpers.CtrSoapCheckRegister(soapMan)

        retStr = ""
        retStr += f"Account status: {soapMan.account_status}\n"
        if soapMan.account_status != 'U':
            retStr += f"Account register: {'Expired' if soapMan.register_expired else 'Valid'}\n"
        retStr += f"Current effective region: {soapMan.region}\n"
        retStr += f"Current effective country: {soapMan.country}\n"
        retStr += f"Current effective language: {soapMan.language}\n"
    except Exception as e:
        await ctx.respond(ephemeral=True, content=f"Cleaninty error:\n```\n{e}\n```")
        return
    
    await ctx.respond(ephemeral=True, content=f"```\n{retStr}```")

@bot.slash_command(description="check serial of console uniques")
async def checkserial(ctx : discord.ApplicationContext, 
                      infile: discord.Option(discord.Attachment, "essential.exefs or secinfo")):
    await ctx.defer(ephemeral=True)

    try:
        data = await infile.read()
    except:
        await ctx.respond(ephemeral=True, content="Failed to read file")
        return
    
    # try to read as essential
    try:
        reader = ExeFSReader(BytesIO(data))
        if "secinfo" in reader.entries:
            data = reader.open("secinfo").read()
            # ensure it's 273 bytes
            if len(data) != 273:
                await ctx.respond(ephemeral=True, content="Invalid secinfo in essential")
                return
    except:
        pass
    
    # The problem here is secinfo has no magic, so we can't really validate it
    # 273 bytes is the only thing we can do lol
    try:
        if len(data) != 273:
            await ctx.respond(ephemeral=True, content="Invalid secinfo provided")
            return
        
        data = data[0x102:0x112]
        data = data.replace(b"\x00", b"").upper().decode("utf-8")
    except:
        await ctx.respond(ephemeral=True, content="Failed to read serial")
        return

    await ctx.respond(ephemeral=True, content=f"Serial: {data}")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print(discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(permissions=2147518464)))
    await bot.change_presence(activity=discord.Game(name="I HAS SOUP"))


bot.run(os.getenv("DISCORD_TOKEN"))