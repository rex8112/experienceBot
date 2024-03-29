﻿import discord
import sqlite3
import datetime
import sys
import asyncio

from discord.ext import commands
from configobj import ConfigObj
from random import randint

db = sqlite3.connect('experience.db')
cursor = db.cursor()
config = ConfigObj(infile = 'config.ini')
masterColor = discord.Colour(0x30673a)

try: ##Check if config.ini exist, if not, create a new file and kill the program
  f = open('config.ini')
  f.close()
except IOError as e:
  f = open('config.ini', 'w+')
  f.close()
  print('config.ini not found, generating one now. Please fill it in.')
  config['token'] = ''
  config['ownerID'] = ''
  config.write()
  sys.exit()

game = discord.Activity(name='!help', type=discord.ActivityType.listening)
bot = commands.Bot(description='True Experience', command_prefix='!', activity=game, owner_id=int(config['ownerID']))

def ttCheck(ctx, indx):
  guild = ctx.guild
  cursor.execute( """SELECT id FROM TIMETABLE WHERE indx = ?""", (indx,) )
  uid = cursor.fetchone()[0]
  if guild.get_member(uid):
    return True
  else:
    return False
    
async def outCheck():
  cnt = 0
  while True:
    cnt += 1
    print('Waiting to Check: {}'.format(cnt))
    await asyncio.sleep(600)

    cursor.execute( """SELECT * FROM TIMETABLE WHERE active = 1""" )
    entries = cursor.fetchall()
    
    for entry in entries:
      indx = entry[0]
      id = entry[2]
      cin = entry[3]

      begin = datetime.datetime.strptime(cin, "%Y-%m-%d %H:%M:%S")
      now = datetime.datetime.now()
      dur = now - begin

      if dur.seconds > 3600 * 2:
        usr = bot.get_user(id)

        min = dur.days * 1440
        sec = dur.seconds
        hrs, min, sec = timeConvert(min, sec)

        embed = discord.Embed(title='Did you forget to clock out?', colour=masterColor,
                description='It seems you haven\'t clocked out in awhile\n**{}** Hours, **{}** Minutes, and **{}** Seconds\nTo be exact.'.format(hrs, min, sec))
        embed.add_field(name='Is this intentional?', value='Per my settings, I inform everyone every **10** minutes (or immediately once I come back online) if their workblock has surpassed **2** hours.\n\
              If you want to continue another two hours without being notified, please run the `!reclock` or `!rc` command in your discord')
        embed.add_field(name='Not intentional?', value='Chances are, you just forgot to clock out, that\'s alright, just go clock out now\n\
              Keep in mind this still clocks you out at the time of the command, if you need to have your clock out time fixed, simply let someone in your group with the `ban_members` \
              permission know and they can fix your clock out with a quick `!tt edit update {} out {}`. Of course you will have to change the date/time accordingly.'.format(indx, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        embed.set_footer(text='This message will be deleted in 9 Minutes and 50 Seconds')
        embed.set_author(name=usr.name, icon_url=usr.avatar_url)
        
        await usr.send(embed=embed, delete_after=590)
    

def timeConvert(min, sec):

  min += sec // 60
  sec = sec % 60
  hrs = min // 60
  min = min % 60
  
  return hrs, min, sec

bg_task = bot.loop.create_task(outCheck())
@bot.event
async def on_ready():
  print("Logged in as")
  print('Name: {}'.format(bot.user.name))
  print('ID:   {}'.format(bot.user.id))
  print("----------")
  for guild in bot.guilds:
    print(guild.name)
    print(guild.id)
    print('----------')
  cursor.execute( """CREATE TABLE IF NOT EXISTS SERVERS( indx INTEGER PRIMARY KEY, id INTEGER, exp INTEGER DEFAULT 0, announce INTEGER, core TEXT )""" )
  cursor.execute( """CREATE TABLE IF NOT EXISTS MENTION(indx INTEGER PRIMARY KEY, name TEXT, id INTEGER, count INTEGER DEFAULT 0)""" )
  cursor.execute( """CREATE TABLE IF NOT EXISTS TIMETABLE(indx INTEGER PRIMARY KEY, name TEXT, id INTEGER, cin TEXT, cout TEXT, active INTEGER)""" )
  
  for guild in bot.guilds:
    cursor.execute( """SELECT * FROM SERVERS WHERE id = ?""", (guild.id,) )
    if not cursor.fetchone():
      cursor.execute( """INSERT INTO SERVERS(id) VALUES(?)""", (guild.id,) )
  
  db.commit()

@bot.event
async def on_message(ctx):
  await bot.process_commands(ctx)
  if not ctx.author.bot:
    mentions = ctx.mentions
    if 'experience' in ctx.content.lower():
      await ctx.channel.send('🎉🎊 **CORE ESSENTIAL EXPERIENCE** 🎊🎉')
      cursor.execute("""UPDATE SERVERS SET exp = exp + 1 WHERE id = ?""", (ctx.guild.id,))
      db.commit()

    for mem in mentions:
      name = str(mem)
      id = mem.id
      cursor.execute("""SELECT * FROM MENTION WHERE id = ?""", (id,))
      user = cursor.fetchone()
      if user:
        cursor.execute("""UPDATE MENTION SET count = count + 1 WHERE id = ?""", (id,))
      else:
        cursor.execute("""INSERT INTO MENTION(name, id, count) VALUES(?, ?, 1)""", (name, id))
      db.commit()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
      print(error)
      await ctx.send('[NoPrivateMessage] Sorry. This command is not allow in private messages.')
    elif isinstance(error, commands.CommandNotFound):
      return
    else:
      print('{}: {}'.format(type(error).__name__, error))
      embed = discord.Embed(title="Error", colour=discord.Colour(0xd0021b), description='{}: {}'.format(type(error).__name__, str(error)))
      embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
      embed.set_footer(text='Please message rex8112#1200 if the error is not from user error')
      await ctx.send(embed=embed)
      
@bot.event
async def on_guild_join(guild):
  print(guild.name)
  print(guild.id)
  print('----------')
  
  embed = discord.Embed(title='Hello!', colour=masterColor, description='I have a few setup requests to run at maximum efficiency. Anyone with Manage Server permission can use these commands.')
  embed.set_author(name=guild.name, icon_url=guild.icon_url)
  embed.add_field(name='Announcements', value='By using !setannounce or !sa in a channel, you will set that channel to be where I will post any bot related announcements, including but not limited to new features, scheduled downtimes, or known errors/workarounds. If you don\'t set this, then the server owner will get the announcements in their DMs.', inline=False)
  embed.add_field(name='Core Essential Experience', value='By using !setcore you can set your game\'s Core Essential Experience, which will be posted when using !core')
  
  cursor.execute( """SELECT * FROM SERVERS WHERE id = ?""", (guild.id,) )
  if not cursor.fetchone():
    cursor.execute( """INSERT INTO SERVERS(id) VALUES(?)""", (guild.id,) )
    db.commit()
  
  if guild.system_channel:
    await guild.system_channel.send(embed=embed)
  else:
    await guild.owner.send(embed=embed)
    
@bot.command()
@commands.is_owner()
async def announcement(ctx, title, *, message):
  """Send a bot wide announcement"""
  embed = discord.Embed(title='Announcement: {}'.format(title), colour=masterColor, description=message)
  cursor.execute( """SELECT id, announce FROM SERVERS""" )
  servers = cursor.fetchall()
  
  for server in servers:
    guild = bot.get_guild(server[0])
    if server[1]:
      annCh = guild.get_channel(server[1])
      try:
        await annCh.send(embed=embed)
      except discord.Forbidden:
        await guild.owner.send(content='I did not have access to your announcement channel: {}'.format(annCh.name), embed=embed)
    else:
      gowner = guild.owner
      await gowner.send(embed=embed)
      
@bot.command()
@commands.guild_only()
async def ahelp(ctx, *, issue):
  """Ask for help from the bot owner"""
  owner = bot.get_user(int(config['ownerID']))
  embed = discord.Embed(title='{}:{} - {}'.format(str(ctx.author), ctx.author.id, ctx.guild.name), colour=masterColor, description=issue)
  await owner.send(embed=embed)
  await ctx.message.add_reaction('✅')
  
@bot.command()
@commands.is_owner()
async def answer(ctx, mem: discord.Member, *, content):
  """Answer an ahelp"""
  embed = discord.Embed(title='Bot Owner\'s Reply', colour=masterColor, description=content)
  embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
  await mem.send(embed=embed)
  await ctx.message.add_reaction('✅')

@bot.command()
@commands.guild_only()
async def core(ctx):
  """State the Core Essential Experience"""
  cursor.execute( """SELECT core FROM SERVERS WHERE id = ?""", (ctx.guild.id,) )
  core = cursor.fetchone()
  
  await ctx.send('🎉🎊 **CORE ESSENTIAL EXPERIENCE** 🎊🎉\n{}'.format(core[0]))

@bot.command()
@commands.guild_only()
async def count(ctx):
  """Get Mention and Experience Count"""
  cursor.execute("""SELECT exp FROM SERVERS WHERE id = ?""", (ctx.guild.id,) )
  count = cursor.fetchone()
  cursor.execute("""SELECT id, count FROM MENTION ORDER BY count DESC""")
  mcount = cursor.fetchall()

  embed = discord.Embed(title="🎉🎊 **CORE ESSENTIAL EXPERIENCE** 🎊🎉", colour=masterColor, description='Main Count: {}'.format(count[0]))

  for mem in mcount:
    user = ctx.guild.get_member(mem[0])
    if user:
      embed.add_field(name='{}'.format(user.display_name), value='**Count:** {}'.format(mem[1]), inline=False)

  await ctx.send(embed=embed)
  
@bot.command(aliases=['sa'])
@commands.has_permissions(manage_channels=True)
async def setannounce(ctx):
  announce = ctx.channel.id
  cursor.execute( """UPDATE SERVERS SET announce = ? WHERE id = ?""", (announce, ctx.guild.id) )
  db.commit()
  await ctx.message.add_reaction('✅')
  
@bot.command()
@commands.has_permissions(manage_channels=True)
async def setcore(ctx, *, core):
  cursor.execute( """UPDATE SERVERS SET core = ? WHERE id = ?""", (core, ctx.guild.id) )
  db.commit()
  await ctx.message.add_reaction('✅')

@bot.command(aliases=['in'])
@commands.guild_only()
async def cin(ctx):
  """Clock In"""
  id = ctx.author.id
  cursor.execute("""SELECT * FROM TIMETABLE WHERE id = ? AND active = 1""", (id,))
  clockedIn = cursor.fetchone()
  if clockedIn: # If the user is already clocked in
    embed = discord.Embed(title='You have already clocked in', colour=masterColor, description='Clocked in at: `{}`'.format(clockedIn[3]))
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.set_footer(text='Please message Riley (rex8112#1200) if you forgot to clock out')
    await ctx.message.add_reaction('⛔')
    await ctx.send(embed=embed)
  else:
    cursor.execute("""INSERT INTO TIMETABLE(name, id, cin, active) VALUES(?, ?, datetime('now', 'localtime'), 1)""", (str(ctx.author), id))
    db.commit()
    await ctx.message.add_reaction('✅')

@bot.command(aliases=['out'])
@commands.guild_only()
async def cout(ctx):
  """Clock Out"""
  id = ctx.author.id
  cursor.execute("""SELECT * FROM TIMETABLE WHERE id = ? AND active = 1""", (id,))
  clockedOut = cursor.fetchone()
  if clockedOut:
    cursor.execute("""UPDATE TIMETABLE SET cout = datetime('now', 'localtime'), active = 0 WHERE id = ? AND active = 1""", (id,))
    db.commit()
    await ctx.message.add_reaction('✅')
  else:
    embed = discord.Embed(title='You have already clocked out', colour=masterColor)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.set_footer(text='Please message Riley (rex8112#1200) if you forgot to clock in')
    await ctx.message.add_reaction('⛔')
    await ctx.send(embed=embed)

@bot.command(aliases=['rc'])
@commands.guild_only()
async def reclock(ctx):
  """Reset the two hour reminder counter be quickly clocking you in and out."""
  id = ctx.author.id
  cursor.execute("""SELECT * FROM TIMETABLE WHERE id = ? AND active = 1""", (id,))
  clockedIn = cursor.fetchone()
  if clockedIn:
    cursor.execute("""UPDATE TIMETABLE SET cout = datetime('now', 'localtime'), active = 0 WHERE id = ? AND active = 1""", (id,))
    cursor.execute("""INSERT INTO TIMETABLE(name, id, cin, active) VALUES(?, ?, datetime('now', 'localtime'), 1)""", (str(ctx.author), id))
    db.commit()
    await ctx.message.add_reaction('✅')
  else:
    embed = discord.Embed(title='This can only be ran if you are already clocked in', colour=masterColor)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.set_footer(text='Please message Riley (rex8112#1200) if you forgot to clock in')
    await ctx.message.add_reaction('⛔')
    await ctx.send(embed=embed)

@bot.group(aliases=['tt'])
@commands.guild_only()
async def timetable(ctx):
  """A group of commands related to the TT

  Using without any subcommands will get the latest 20 TT listings of yourself."""
  if ctx.invoked_subcommand is None:
    id = ctx.author.id

    cursor.execute("""SELECT * FROM TIMETABLE WHERE id = ? ORDER BY cin DESC LIMIT 20""", (id,))
    stamps = cursor.fetchall()

    embed = discord.Embed(title='Timetable for {}'.format(ctx.author.display_name), color=masterColor)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    if ctx.author.avatar_url:
      embed.set_thumbnail(url=ctx.author.avatar_url)
    else:
      embed.set_thumbnail(url='https://cdn.discordapp.com/embed/avatars/{}.png'.format(randint(0,4)))

    for stamp in stamps:
      indx = stamp[0]
      #name = stamp[1]
      #nid = stamp[2]
      cin = stamp[3]
      cout = stamp[4]
      act = stamp[5]

      if act:
        embed.add_field(name='__{}__: **{} - Now**'.format(indx, cin), value='__***Currently Active***___', inline=False)
      else:
        begin = datetime.datetime.strptime(cin, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(cout, "%Y-%m-%d %H:%M:%S")
        dur = end - begin

        min = dur.days * 1440
        sec = dur.seconds

        hrs, min, sec = timeConvert(min, sec)

        embed.add_field(name='__{}__: **{} - {}**'.format(indx, cin, cout), value='Duration: **{}** Hours, **{}** Minutes, **{}** Seconds'.format(hrs, min, sec), inline=False)

    await ctx.author.send(embed=embed)
    await ctx.message.add_reaction('✅')

@timetable.command()
async def active(ctx):
  """Get your currently active timestamp"""
  id = ctx.author.id
  cursor.execute("""SELECT * FROM TIMETABLE WHERE id = ? AND active = 1""", (id,))

  embed = discord.Embed(title='Your Active Timestamp', colour=masterColor)
  embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
  embed.set_footer(text='If more than one listing, please tell rex8112#1200')

  act = cursor.fetchall()
  if act:
    for stamp in act:
      indx = stamp[0]
      name = stamp[1]
      nid = stamp[2]
      cin = stamp[3]
      embed.add_field(name='{}: {} `{}`'.format(indx, name, nid), value='**{}**'.format(cin))

  await ctx.send(embed=embed)

@timetable.command()
@commands.has_permissions(ban_members=True)
async def summary(ctx, begin, end):
  """Collect total time between dates for everyone
    Use date format: YYYY-MM-DD
    This works by checking for all clock in times so it will not grab someone if they clocked in the day before the first date but clocked out on the first date or later"""
  embed = discord.Embed(title='Times Between', colour=masterColor, description='{} - {}'.format(begin, end))
  embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

  for mem in ctx.guild.members:
    if not mem.bot:
      id = mem.id
      cursor.execute("""SELECT cin, cout FROM TIMETABLE WHERE id = ? AND active = 0 AND cin BETWEEN ? AND ? """, (id, begin, end))
      times = cursor.fetchall()

      hrs = 0
      min = 0
      sec = 0

      for time in times:
        cin = datetime.datetime.strptime(time[0], "%Y-%m-%d %H:%M:%S")
        cout = datetime.datetime.strptime(time[1], "%Y-%m-%d %H:%M:%S")
        dur = cout - cin

        min += dur.days * 1440
        sec += dur.seconds

      hrs, min, sec = timeConvert(min, sec)

      embed.add_field(name='{.display_name}'.format(mem), value='**{}** Hours, **{}** Minutes, **{}** Seconds'.format(hrs, min, sec), inline=False)

  await ctx.author.send(embed=embed)

@timetable.command()
@commands.has_permissions(ban_members=True)
async def get(ctx, mem: discord.Member):
  """Get a list of 20 TT entries of someone else"""
  id = mem.id

  cursor.execute("""SELECT * FROM TIMETABLE WHERE id = ? ORDER BY cin DESC LIMIT 20""", (id,))
  stamps = cursor.fetchall()

  embed = discord.Embed(title='Timetable for {}'.format(mem.display_name), color=masterColor)
  embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
  if mem.avatar_url:
    embed.set_thumbnail(url=mem.avatar_url)
  else:
    embed.set_thumbnail(url='https://cdn.discordapp.com/embed/avatars/{}.png'.format(randint(0,4)))

  for stamp in stamps:
    indx = stamp[0]
    #name = stamp[1]
    #nid = stamp[2]
    cin = stamp[3]
    cout = stamp[4]
    act = stamp[5]

    if act:
      embed.add_field(name='{}: **{} - Now**'.format(indx, cin), value='__***Currently Active***___', inline=False)
    else:
      begin = datetime.datetime.strptime(cin, '%Y-%m-%d %H:%M:%S')
      end = datetime.datetime.strptime(cout, '%Y-%m-%d %H:%M:%S')
      dur = end - begin
      
      min = dur.days * 1440
      sec = dur.seconds

      hrs, min, sec = timeConvert(min, sec)

      embed.add_field(name='{}: **{} - {}**'.format(indx, cin, cout), value='Duration: **{}** Hours, **{}** Minutes, **{}** Seconds'.format(hrs, min, sec), inline=False)

  await ctx.author.send(embed=embed)
  await ctx.message.add_reaction('✅')

@timetable.group()
@commands.has_permissions(ban_members=True)
async def edit(ctx):
  """Administrative Edit Commands"""
  owner = bot.get_user(bot.owner_id)
  if ctx.author.id is not owner.id:
    embed = discord.Embed(title='Edit Command Invoked', colour=masterColor, description=str(ctx.message.content))
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    await owner.send(embed=embed)

@edit.command()
async def new(ctx, mem: discord.Member, cin: str, cout: str):
  """Manually add a new TT entry for someone
  
  mem is a member in your Discord
  cin is the in times
  cout is the out time
  You must use the whole format: YYYY-MM-DD HH:MM:SS"""
  id = mem.id
  try:
    tin = datetime.datetime.strptime(cin, '%Y-%m-%d %H:%M:%S')
    tout = datetime.datetime.strptime(cout, '%Y-%m-%d %H:%M:%S')

    cursor.execute("""INSERT INTO TIMETABLE(name, id, cin, cout, active) VALUES(?, ?, ?, ?, 0)""", (str(mem), id, tin.strftime('%Y-%m-%d %H:%M:%S'), tout.strftime('%Y-%m-%d %H:%M:%S')))
    db.commit()
    await ctx.message.add_reaction('✅')

  except ValueError:
    await ctx.message.add_reaction('⛔')
    raise commands.UserInputError('Format error: Please Format in "YYYY-MM-DD HH:MM:SS"')
    
@edit.command()
async def remove(ctx, indx: int):
  """Removes an existing entry THERE IS NO UNDO
  
  Simply supply the correct indx"""
  cursor.execute("""DELETE FROM TIMETABLE WHERE indx = ?""", (indx,))
  db.commit()
  await ctx.message.add_reaction('✅')
  
@edit.command()
async def update(ctx, indx, pos: str, *, timestamp):
  """Update an existing entry to change the in or out time
  
  indx is the number of the entry
  pos is either in or out, depending on what you want to change
  timestamp is the new value
  You must use the whole format: YYYY-MM-DD HH:MM:SS"""
  if ttCheck(ctx, indx):
    try:
      _ = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
      
      if pos == 'in':
        cursor.execute( """UPDATE TIMETABLE SET cin = ? WHERE indx = ?""", (timestamp, indx))
      elif pos == 'out':
        cursor.execute( """UPDATE TIMETABLE SET cout = ? WHERE indx = ?""", (timestamp, indx))
      db.commit()
      await ctx.message.add_reaction('✅')
    
    except ValueError:
      await ctx.message.add_reaction('⛔')
      raise commands.UserInputError('Format error: Please Format in "YYYY-MM-DD HH:MM:SS"')
  else:
    await ctx.message.add_reaction('⛔')
    raise commands.UserInputError('Permission error: That entry belongs to another project')

@bot.command(hidden=True)
@commands.is_owner()
async def channelsServer(ctx, gid: int):
  guild = bot.get_guild(gid)
  embed = discord.Embed(title='Incoming Channel List', colour=masterColor)
  if guild.icon_url:
    embed.set_author(name=guild.name, icon_url=guild.icon_url)
  else:
    embed.set_author(name=guild.name)

  for channel in guild.text_channels:
    embed.add_field(name=channel.name, value='`{.id}`'.format(channel), inline=False)

  await ctx.send(embed=embed)

@bot.command(hidden=True)
@commands.is_owner()
async def leaveServer(ctx, gid: int, cid: int):
  guild = bot.get_guild(gid)
  channel = guild.get_channel(cid)

  embed = discord.Embed(title='__***Goodbye***__', colour=discord.Colour(0x0052bd), description='I\'m heading out. I am glad you all enjoyed my presence but I am getting heavily upgraded and my owner wishes to have more control over where I am.')
  if guild.icon_url:
    embed.set_author(name=guild.name, icon_url=guild.icon_url)
    embed.set_thumbnail(url=guild.icon_url)
  else:
    embed.set_author(name=guild.name)

  embed.add_field(name='Sad to see me go?', value='If you wish to see me in your future GAME Projects Discord, contact my owner, `rex8112#1200`. If you\'re not in a server with him he can be found here: https://discord.gg/ynqC5Ex', inline=False)
  embed.set_footer(text='Bye Bye, I\'ll miss you', icon_url='https://cdn.shopify.com/s/files/1/1061/1924/files/Waving_Hand_Sign_Emoji_Icon_ios10.png?9057686143853941278')
  embed.set_image(url='https://www.askideas.com/media/07/Thank-You-Goodbye.jpg')

  await channel.send(embed=embed)
  await guild.leave()
  await ctx.message.add_reaction('✅')


bot.run(config['token'])
