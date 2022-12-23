import discord
import requests
import asyncio
import os
import random
from discord.ext import commands
from dotenv import load_dotenv
import json
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Get discord Bot token and guild from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
GENERAL_CHANNEL = int(os.getenv('DISCORD_GENERAL_CHANNEL'))
DISCORD_BOT_COMMANDS_CHANNEL= int(os.getenv('DISCORD_BOT_COMMANDS_CHANNEL'))
SUBSCAN_API = os.getenv('SUBSCAN_API')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


# This event runs when the bot logs in
@bot.event
async def on_ready():
    # Get the current guild
    guild = discord.utils.get(bot.guilds, name=GUILD)

    # print the guild's name and ID the bot is connected to
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    # print bot log in details
    print(f'Logged in as {bot.user}')

    # send a message to General Channel
    channel = bot.get_channel(GENERAL_CHANNEL)
    await channel.send('I am alive')
    
    # Get a list of all members in the guild
    members = guild.members

    # Print the name and ID of each member
    for member in members:
        print(f"{member.name} ({member.id})")
    
    # Create a new role with the name 'verified' if not available
    for role in guild.roles:
        if role.name == 'verified':
            return
        else:
            role = await guild.create_role(name='verified')
            print(f"Created role {role.name} (ID: {role.id})")

    # Print the list of roles in the guild
    print("Roles in the guild:")
    for role in guild.roles:
        print(f"- {role.name} (ID: {role.id})")

# Generate a random CAPTCHA challenge
def generate_captcha():
    letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    challenge = ''.join(random.choice(letters) for i in range(5))
    return challenge

# Check if the user's response is correct
def check_captcha(challenge, response):
    return challenge.lower() == response.lower()

# define function to check channel ID
async def is_channel(ctx):
    return ctx.channel.id == DISCORD_BOT_COMMANDS_CHANNEL

# Bot command to verify a user with a CAPTCHA challenge
@bot.command()
@commands.check(is_channel)
async def verify(ctx):
    # Get the interacting guild author
    author = ctx.author

    # check if the author has the 'verified' role
    for role in author.roles:
        if role.name == "verified":
            await ctx.send("You are already verified.")
            return

    # Generate a CAPTCHA challenge
    challenge = generate_captcha()
    print(challenge)
        
    # Send the challenge to the user
    await ctx.send('Please enter the following characters to verify that you are a human: ' + challenge)
        
    # Wait for the user's response
    def check(m):
        return m.author == ctx.message.author and m.channel == ctx.message.channel
    try:
        response = await bot.wait_for('message', check=check, timeout=60.0)
        print(response)
    except asyncio.TimeoutError:
        await ctx.send('Timed out waiting for response.')
        return

    #print(challenge, response.content)

    # Check if the response is correct
    if check_captcha(challenge, response.content):
        # Assign the "verified" role to the user
        role = discord.utils.get(ctx.guild.roles, name='verified')
        #print(role)
        await ctx.message.author.add_roles(role)
        await ctx.send('You are likely to be a human and have been assigned the "verified" role!')
    else:
        await ctx.send('Incorrect response.')

# Get the current date
today = datetime.date.today()

# Convert the date to a string using the strftime() method
date_string = today.strftime('%Y-%m-%d')

# Calculate the date one year before today
one_month_ago = today - datetime.timedelta(days=30)

# Convert the date to a string using the strftime() method
one_month_ago_string = one_month_ago.strftime('%Y-%m-%d')

# Set the API endpoint URL and the API key as variables
url = 'https://khala.api.subscan.io/api/scan/price/history'
api_key = SUBSCAN_API

# Set the request headers
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': api_key
}

# Set the request payload
payload = {
    'start': one_month_ago_string,
    'end': date_string
}

# Make a POST request to the API
response = requests.post(url, headers=headers, json=payload)

# Print the response status code
#print(response.status_code)

# Print the response body
#print(response.text)


# Parse the dictionary from a JSON string
dictionary = json.loads(response.text)

# Access the values in the dictionary
code = dictionary['code']
message = dictionary['message']
generated_at = dictionary['generated_at']
data = dictionary['data']
average = data['average']
ema7_average= data['ema7_average']

# Print the values
# print(f'Code: {code}')
# print(f'Message: {message}')
# print(f'Generated at: {generated_at}')
# print(f'Average: {average}')
# print(f'ema7_average: {ema7_average}')

# Convert the list of dictionaries to a Pandas dataframe
df = pd.DataFrame(data['list'])
print(df.head())

# print summary statistics
print(df.describe())

# check column data types
print(df.dtypes)

# convert price column data type to float
price = df['price'].astype(float)

# calculate summary statistics
# round the values to the first five decimal places
mean = price.mean().round(5)
median = price.median().round(5)
min = price.min().round(5)
max = price.max().round(5)

# print summary statistics
print(f'mean: {mean} \nmedian: {median} \nminimum: {min} \nmaximum: {max}')

# Plot the price
plt.plot(price)

# Add a title and axis labels
plt.title('Plot of PHA price')

# Set the y-axis range to [0, 30]
plt.ylim(0.0, 1.4)
plt.xlabel('Index')
plt.ylabel('Price')

# Show the plot
#plt.show()

# Save the plot as a png file
filename = "price_chart.png"
plt.savefig(filename)

# bot command for verified users to check Phala price changes in the last month
@bot.command()
@commands.has_role("verified")
@commands.check(is_channel)
async def check_price(ctx):
    # Send the summary statistics to the channel
    await ctx.send(f'mean: {mean} \nmedian: {median} \nminimum: {min} \nmaximum: {max}')

    # Read the file and convert it to a bytes object
    with open('./price_chart.png', 'rb') as f:
        file_bytes = f.read()

    # Create a new file object using the bytes
    file = discord.File(fp=file_bytes, filename='image.png')

    # Create a new embed with the file attached
    embed = discord.Embed().set_image(url='attachment://image.png')

    # Send the embed in the channel
    await ctx.send(file=file, embed=embed)
   

# Catch errors if bot.command() gives an error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You are not using the Bot_commands channel or You do not have the correct role for this command.')

bot.run(TOKEN)