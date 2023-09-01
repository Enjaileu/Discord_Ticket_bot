'''
The bot is designed to simplify the process of sending tickets to the Artfx TD team. 
On the discord server where the bot is installed, a "HELP Pipeline/Renderfarm" channel category is created. 
In this category, a "create-ticket" channel is also created with a message. 
To send a ticket, the user must press one of the buttons proposed in the "create-ticket" channel. 
This will create another channel specific to the newly created ticket, where the TD team and the user can discuss the problem.
'''

import discord
from discord.ext import commands
from discord.ui import View
import json
import os

# Set intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")  # Remove the default help command


# Obtenez le chemin absolu du répertoire du script
script_directory = os.path.dirname(os.path.abspath(__file__))
file_res_path = os.path.join(script_directory, "interactions.json")

# Chargement des données d'interaction depuis un fichier JSON au démarrage du bot
print(f"initial load of interactions")
try:
    with open("interactions.json", "r") as file:
        interactions_data = json.load(file)
except FileNotFoundError:
    interactions_data = []

# class used to display buttons in new ticket message
class TicketView(View):
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji = "🗑️") 
    async def button_callback(self, button, interaction):
        '''
        Button "Close Ticket". Execute function self.close_ticket when pushed.
        '''
        await self.close_ticket(button)

    # TODO : button to archive in a .json the ticket info.
        
    async def close_ticket(self, interaction):
        '''
        Function executed by button "Close Ticket". Remove current channel.
        '''
        # Verify if interaction from a ticket channel
        if isinstance(interaction.channel, discord.TextChannel) and "ticket" in interaction.channel.name:
            # Delete channel
            await interaction.channel.delete()
        else:
            # Not right channel
            await interaction.response.send_message("This button can only be used in ticket channels.", ephemeral=True)

        save_interactions_data()

# class used to display buttons in create ticket message with the function executed
class CreateTicketView(View):

    buttons_data = {
        "Ticket Silex": {"type": "pipeline", "function_name": "first_button_callback"},
        "Ticket Farm": {"type": "farm", "function_name": "second_button_callback"}
    }

    @discord.ui.button(label="Ticket Silex", style=discord.ButtonStyle.green, emoji = "🪨") 
    async def first_button_callback(self, button, interaction):
        '''
        Button "Ticket Silex". Execute function self.create_ticket with type="pipeline" when pushed.
        '''
        user_mention = button.user.mention
        user_id = button.user.id
        td = discord.utils.get(button.guild.roles, name="Technical Director")
        td_mention = td.mention
        await self.create_ticket("pipeline", user_mention, user_id, td_mention)

    @discord.ui.button(label="Ticket Farm", style=discord.ButtonStyle.secondary, emoji="🖥️")
    async def second_button_callback(self, button, interaction):
        '''
        button "Ticket Farm". Execute function self.create_ticket with type="farm" when pushed.
        '''
        user_mention = button.user.mention
        user_id = button.user.id
        td = discord.utils.get(button.guild.roles, name="Technical Director")
        td_mention = td.mention
        await self.create_ticket("farm", user_mention, user_id, td_mention)


    async def create_ticket(self, type, user_mention, user_id, td_mention):

        # Get category "HELP Pipeline/Renderfarm". Create it if not found.
        category = discord.utils.get(bot.guilds[0].categories, name="HELP Pipeline/Renderfarm")
        if not category:
            category = await bot.guilds[0].create_category("HELP Pipeline/Renderfarm")

        # Find or create the next ticket number.
        ticket_number = 1
        while discord.utils.get(category.channels, name=f"{type}-ticket-{ticket_number:03}"):
            ticket_number += 1

        # Create the new channel
        channel_name = f"{type}-ticket-{ticket_number:03}"
        overwrites = {
            bot.guilds[0].default_role: discord.PermissionOverwrite(read_messages=False),
            bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)

        # Send first message with buttons
        message_content = f"""
    [FR]🥖
    Salut {user_mention} ! Explique nous ton problème en rapport avec la/le {type}.
    Donne nous le plus de détails possible pour nous aider à régler le problème (numéro du PC, ton numéro de salle, des screenshot/vidéos, quelles actions ont déclenchées ton problème etc.)

    La team {td_mention} revient vers toi au plus tôt!

    [EN]🌏
    Hi {user_mention} ! Tell us about your problem with the {type}. 
    Give us as many details as possible to help us fix the problem (PC number, your room number, screenshots/videos, what actions triggered your problem etc.).

    The {td_mention} team will get back to you as soon as possible!
    """
        view = TicketView()
        await ticket_channel.send(message_content, view=view)

        button_info = self.buttons_data[self.children[0].label]  # Utilisez self.children[0] au lieu de self.view.children[0]
        print(f"interaction in create ticket before append = {interactions_data}")
        interactions_data.append({
            "type": button_info["type"],
            "function_name": button_info["function_name"],
            "user_id": user_id,
            "user_mention": user_mention,
            "td_mention": td_mention,
            "channel_name": channel_name
        })
        print(f"after = {interactions_data}")
        save_interactions_data()

# Fonction pour sauvegarder les données d'interaction dans un fichier JSON
def save_interactions_data(interactions_data=None):
    print(f"interactions to save : {interactions_data}")

    try:
        with open(file_res_path, 'w') as output_file:
            content = json.dumps(interactions_data, indent=4)
            output_file.write(content)
    except Exception as e:
        print(f"An error occurred while saving data: {e}")

@bot.event
async def on_ready():
    '''
    Execute when bot is run. 
    Create category "HELP Pipeline/Renderfarm" if it not exists.
    Create channel "create-ticket" in category "HELP Pipeline/Renderfarm" if it not exists. User can't send message in this channel.
    Send a first message with button and explaination of the process.
    '''
    print(f'Logged in as {bot.user.name}')

    # Get category "HELP Pipeline/Renderfarm". Create it if not found.
    category = discord.utils.get(bot.guilds[0].categories, name="HELP Pipeline/Renderfarm")
    if not category:
        category = await bot.guilds[0].create_category("HELP Pipeline/Renderfarm")

     # Get td role mention
    td_role = discord.utils.get(bot.guilds[0].roles, name="Technical Director")
    if td_role:
        td_role_mention = td_role.mention
    else:
        td_role_mention = "@Technical Director"  # Utilisation du texte brut si le rôle n'est pas trouvé
    
    # Create channel create-ticket
    ticket_channel = discord.utils.get(category.channels, name="create-ticket")
    if not ticket_channel:
        overwrites = {
            bot.guilds[0].default_role: discord.PermissionOverwrite(read_messages=False),
            bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await category.create_text_channel("create-ticket", overwrites=overwrites)
        ticket_channel = discord.utils.get(category.channels, name="create-ticket")

    # Charger les interactions à partir du fichier JSON
    try:
        with open(file_res_path, "r") as file:
            interactions_data = json.load(file)
    except FileNotFoundError:
        interactions_data = []

    # Configurer les boutons avec les interactions chargées
    ticket_view = CreateTicketView()
    for interaction in interactions_data:
        button_type = interaction["type"]
        function_name = CreateTicketView.buttons_data[button_type]["function_name"]
        function = getattr(ticket_view, function_name)

        ticket_view.children[0].label = button_type
        ticket_view.children[0].callback = function

    # If channel create-ticket is empty, send first message.
    async for message in ticket_channel.history(limit=1):
        break
    else:
        message_content = f"""
[FR]🥖
Bonjour. Si tu as un problème avec Silex ou la Renderfarm, tu peux créer un ticket qui contactera automatiquement la team {td_role_mention}.
Clique sur le bouton "ticket Silex" si le problème est sur Silex.
Clique sur le bouton "ticket Farm" si le problème a lieu sur la Renderfarm.

Si le bot ne fonctionne pas, adresse ton problème à cette adresse mail : 5-td-mtp@artfx.fr

[EN]🌏
Hello. If you have a problem with Silex or the Renderfarm, you can create a ticket that will automatically contact the {td_role_mention} team.
Click on the "Silex ticket" button if the problem is with flint.
Click on the "Farm ticket" button if the problem is on the renderfarm.

If the bot is not working, please explain your problem by mail : 5-td-mtp@artfx.fr
"""
        view = CreateTicketView()
        await ticket_channel.send(content=message_content, view=view)

        # Initial interactions for "Ticket Silex" and "Ticket Farm"
        interactions_data.append({
            "type": "pipeline",  # type for "Ticket Silex"
            "user_id": None,
            "user_mention": None,
            "td_mention": None,
            "channel_name": None
        })
        interactions_data.append({
            "type": "farm",  # type for "Ticket Farm"
            "user_id": None,
            "user_mention": None,
            "td_mention": None,
            "channel_name": None
        })

        print(f"before save, data = {interactions_data}")
        save_interactions_data(interactions_data)

# Replace "YOUR_TOKEN_HERE" by the token you copy from discord development website
bot.run('MTE0Mzk4NDI2NjEyOTE5MDk4Mw.GOryrP.PmOJnyAwJYciu5dTcFYOvWlAmt9uy2Q02OLebU')