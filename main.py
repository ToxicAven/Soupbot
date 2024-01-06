import discord
from dotenv import load_dotenv
import os
from cleaninty.ctr.simpledevice import SimpleCtrDevice
from pyctr.type.exefs import ExeFSReader
import shutil

bot = discord.Bot()
load_dotenv()

@bot.slash_command(description="Generate a consoles soap key")
async def genjson(ctx: discord.ApplicationContext,
                    secinfo: discord.Option(discord.Attachment, "secinfo.bin, SecureInfo_A"),
                    otp: discord.Option(discord.Attachment, "otp.bin"), 
                    country: discord.Option(str, "Required for U and E regions", required=False)):
    
    try:
        tmpdir = str(ctx.interaction.id)
        os.mkdir(tmpdir)
    except:
        ctx.respond(ephemeral=True, content="Failed to create interaction workspace")
        return

    try:
        await otp.save(f"{tmpdir}/otp.bin")
        await secinfo.save(f"{tmpdir}/secinfo.bin")
    except:
        ctx.respond(ephemeral=True, content="Failed to save uploaded content")
        shutil.rmtree(tmpdir)
        return
    
    try:
        SimpleCtrDevice.generate_new_json(
            otp_file=f"{tmpdir}/otp.bin",
            secureinfo_file=f"{tmpdir}/secinfo.bin",
            country=country,
            json_file=f"{tmpdir}/soap.json"
        )
    except Exception as e:
        await ctx.respond(ephemeral=True, content=f"Cleaninty error: {e}")
        shutil.rmtree(tmpdir)
        print(f"Cleaninty: {e}")
        return
    
    try:
        await ctx.respond(ephemeral=True, file=discord.File(f"{tmpdir}/soap.json"))
    except Exception as e:
        print("Failed to respond, what")
        print(e.with_traceback())

    shutil.rmtree(tmpdir)

@bot.slash_command(description="Generate a consoles soap key using essential.exefs")
async def genjsonessential(ctx: discord.ApplicationContext,
                           essential: discord.Option(discord.Attachment, "essential.exefs"),
                           country: discord.Option(str, "Required for U and E regions", required=False)):
    try:
        tmpdir = str(ctx.interaction.id)
        os.mkdir(tmpdir)
    except:
        ctx.respond(ephemeral=True, content="Failed to create interaction workspace")
        return
    
    try:
        await essential.save(f"{tmpdir}/essential.exefs")
    except:
        await ctx.respond(ephemeral=True, content="Failed to save uploaded content")
        shutil.rmtree(tmpdir)
        return
    
    try:
        reader = ExeFSReader(f"{tmpdir}/essential.exefs")
    except:
        await ctx.respond(ephemeral=True, content="Failed to read essential")
        shutil.rmtree(tmpdir)
        return
    
    if not "secinfo" and "otp" in reader.entries:
        await ctx.respond(ephemeral=True, content="Invalid essential")
        shutil.rmtree(tmpdir)
        return
    try:
        with open(f"{tmpdir}/otp.bin", "wb") as f:
            f.write(reader.open("otp").read())
            f.close()
        
        with open(f"{tmpdir}/secinfo.bin", "wb") as f:
            f.write(reader.open("secinfo").read())
            f.close()
            reader.close()
    except:
        await ctx.respond(ephemeral=True, content="Failed to copy out of essential.exefs")
        shutil.rmtree(tmpdir)
        return
    
    try:
        SimpleCtrDevice.generate_new_json(
            otp_file=f"{tmpdir}/otp.bin",
            secureinfo_file=f"{tmpdir}/secinfo.bin",
            country=country,
            json_file=f"{tmpdir}/soap.json"
        )
    except Exception as e:
        await ctx.respond(ephemeral=True, content=f"Cleaninty error:\n```\n{e}\n```")
        shutil.rmtree(tmpdir)
        print(f"Cleaninty: {e}")
        return
    
    try:
        await ctx.respond(ephemeral=True, file=discord.File(f"{tmpdir}/soap.json"))
    except Exception as e:
        print("Failed to respond, what")
        print(e.with_traceback())
    shutil.rmtree(tmpdir)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print(discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(permissions=2147518464)))
    await bot.change_presence(activity=discord.Game(name="I HAS SOUP"))


bot.run(os.getenv("DISCORD_TOKEN"))