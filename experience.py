import discord
import sqlite3
import datetime

from discord.ext import commands
from configobj import ConfigObj

db = sqlite3.connect('experience.db')
cursor = db.cursor()
config = ConfigObj(infile = 'config.ini')
masterColor = discord.Colour(0x30673a)

game = discord.Activity(name='!help', type=discord.ActivityType.listening)
bot = commands.Bot(description='True Experience', command_prefix='!', activity=game)

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
  cursor.execute( """CREATE TABLE IF NOT EXISTS EXP( count INTEGER DEFAULT 0 )""")
  cursor.execute( """CREATE TABLE IF NOT EXISTS MENTION(indx INTEGER PRIMARY KEY, name TEXT, id INTEGER, count INTEGER DEFAULT 0)""" )
  cursor.execute( """CREATE TABLE IF NOT EXISTS TIMETABLE(indx INTEGER PRIMARY KEY, name TEXT, id INTEGER, cin TEXT, cout TEXT, active INTEGER)""" )
  cursor.execute( """SELECT count FROM EXP""" )
  if not cursor.fetchone():
    cursor.execute( """INSERT INTO EXP DEFAULT VALUES""" )
  
  db.commit()

@bot.event
async def on_message(ctx):
  await bot.process_commands(ctx)
  if not ctx.author.bot:
    mentions = ctx.mentions
    if 'experience' in ctx.content.lower():
      await ctx.channel.send('🎉🎊 **CORE ESSENTIAL EXPERIENCE** 🎊🎉')
      cursor.execute("""UPDATE EXP SET count= count + 1""")
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
      await ctx.send(embed=embed, delete_after=5.00)

@bot.command()
@commands.guild_only()
async def core(ctx):
  """State the Core Essential Experience for Necro Nursery"""
  await ctx.send('🎉🎊 **CORE ESSENTIAL EXPERIENCE** 🎊🎉\nI don\'t know')

@bot.command()
@commands.guild_only()
async def get(ctx):
  """Get Mention and Experience Count"""
  cursor.execute("""SELECT count FROM EXP""")
  count = cursor.fetchone()
  cursor.execute("""SELECT id, count FROM MENTION ORDER BY count DESC""")
  mcount = cursor.fetchall()

  embed = discord.Embed(title="🎉🎊 **CORE ESSENTIAL EXPERIENCE** 🎊🎉", colour=masterColor, description='Main Count: {}'.format(count[0]))

  for mem in mcount:
    user = ctx.guild.get_member(mem[0])
    if user:
      embed.add_field(name='{}'.format(user.display_name), value='**Count:** {}'.format(mem[1]), inline=False)

  await ctx.send(embed=embed)
  #await ctx.send('🎉🎊 **CORE ESSENTIAL EXPERIENCE** 🎊🎉\nCount: *{}*'.format(count[0]))

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
      embed.set_thumbnail(url='https://cdn.discordapp.com/embed/avatars/{}.png'.format(random.randint(0,4)))

    for stamp in stamps:
      indx = stamp[0]
      name = stamp[1]
      nid = stamp[2]
      cin = stamp[3]
      cout = stamp[4]
      act = stamp[5]

      if act:
        embed.add_field(name='__{}__: **{} - Now**'.format(indx, cin), value='__***Currently Active***___', inline=False)
      else:
        begin = datetime.datetime.strptime(cin, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(cout, "%Y-%m-%d %H:%M:%S")
        dur = end - begin

        min = dur.days * 86400
        sec = dur.seconds

        min += sec // 60
        sec = sec % 60
        hrs = min // 60
        min = min % 60

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
    Use date format: YYYY-MM-DD"""
  embed = discord.Embed(title='Times Between', colour=masterColor, description='{} - {}'.format(begin, end))
  embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

  for mem in ctx.guild.members:
    if not mem.bot:
      id = mem.id
      cursor.execute("""SELECT cin, cout FROM TIMETABLE WHERE id = ? AND active = 0 AND cin BETWEEN ? AND ? """, (id, begin, end))
      times = cursor.fetchall()

      hrs = 0;
      min = 0;
      sec = 0;

      for time in times:
        cin = datetime.datetime.strptime(time[0], "%Y-%m-%d %H:%M:%S")
        cout = datetime.datetime.strptime(time[1], "%Y-%m-%d %H:%M:%S")
        dur = cout - cin

        min += dur.days * 86400
        sec += dur.seconds

      min += sec // 60
      sec = sec % 60
      hrs += min // 60
      min = min % 60

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
    embed.set_thumbnail(url='https://cdn.discordapp.com/embed/avatars/{}.png'.format(random.randint(0,4)))

  for stamp in stamps:
    indx = stamp[0]
    name = stamp[1]
    nid = stamp[2]
    cin = stamp[3]
    cout = stamp[4]
    act = stamp[5]

    if act:
      embed.add_field(name='{}: **{} - Now**'.format(indx, cin), value='__***Currently Active***___', inline=False)
    else:
      begin = datetime.datetime.strptime(cin, '%Y-%m-%d %H:%M:%S')
      end = datetime.datetime.strptime(cout, '%Y-%m-%d %H:%M:%S')
      dur = end - begin

      min = dur.days * 86400
      sec = dur.seconds

      min += sec // 60
      sec = sec % 60
      hrs = min // 60
      min = min % 60

      embed.add_field(name='{}: **{} - {}**'.format(indx, cin, cout), value='Duration: **{}** Hours, **{}** Minutes, **{}** Seconds'.format(hrs, min, sec), inline=False)

  await ctx.author.send(embed=embed)
  await ctx.message.add_reaction('✅')

@timetable.group()
@commands.has_permissions(ban_members=True)
async def edit(ctx):
  """Administrative Edit Commands"""

@edit.command()
async def new(ctx, mem: discord.Member, cin: str, cout: str):
  """Manually add a new TT entry for someone"""
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
  cursor.execute("""DELETE FROM TIMETABLE WHERE indx = ?""", (indx))
  db.commit()
  await ctx.message.add_reaction('✅')

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
