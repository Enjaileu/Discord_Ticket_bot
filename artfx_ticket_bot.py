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

class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self) -> None:
        # Register the persistent view for listening here.
        self.add_view(CreateTicketView())

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
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
                bot.guilds[0].default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False), # Every role can read messages but not send_messages
                bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), # Bot can read and send messages
            }
            await category.create_text_channel("create-ticket", overwrites=overwrites)
            ticket_channel = discord.utils.get(category.channels, name="create-ticket")

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
            await self.setup_hook()  # Appel à la méthode pour enregistrer la vue persistante


# class used to display buttons in create ticket message with the function executed
class CreateTicketView(View):

    def __init__(self):
        super().__init__(timeout=None)  # Définir le timeout à None pour la vue persistante

    @discord.ui.button(label="Ticket Silex", style=discord.ButtonStyle.green, emoji = "🪨", custom_id="ticket_silex") 
    async def first_button_callback(self, button, interaction):
        '''
        Button "Ticket Silex". Execute function self.create_ticket with type="pipeline" when pushed.
        '''
        user_mention = button.user.mention
        td = discord.utils.get(button.guild.roles, name="Technical Director")
        td_mention = td.mention
        await self.create_ticket("pipeline", user_mention, td_mention)
        await button.response.defer()

    @discord.ui.button(label="Ticket Farm", style=discord.ButtonStyle.secondary, emoji="🖥️", custom_id="ticket_farm")
    async def second_button_callback(self, button, interaction):
        '''
        button "Ticket Farm". Execute function self.create_ticket with type="farm" when pushed.
        '''
        user_mention = button.user.mention
        td = discord.utils.get(button.guild.roles, name="Technical Director")
        td_mention = td.mention
        await self.create_ticket("farm", user_mention, td_mention)
        await button.response.defer()

    async def create_ticket(self, type, user_mention, td_mention):

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
            bot.guilds[0].default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
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
        view = TicketView(ticket_channel)
        await ticket_channel.send(message_content, view=view)

# class used to display buttons in new ticket message
class TicketView(View):

    def __init__(self, channel):
        self.channel = channel
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji = "🗑️", custom_id="close_ticket") 
    async def button_callback(self, button, interaction):
        '''
        Button "Close Ticket". Execute function self.close_ticket when pushed.
        '''
        await close_ticket(button)

    # TODO : button to archive somewhere the ticket's info
        
async def close_ticket(ctx_or_interaction):
    '''
    Function executed by button "Close Ticket" and !close command. Remove current channel.
    '''
    if isinstance(ctx_or_interaction, commands.Context):  # If it's a command context
        td_role = discord.utils.get(ctx_or_interaction.guild.roles, name="Technical Director")
        if td_role in ctx_or_interaction.author.roles or ctx_or_interaction.author.guild_permissions.administrator:
            # Vérifier si la commande est utilisée dans un channel ticket
            if ctx_or_interaction.channel.name.startswith("pipeline-ticket-") or ctx_or_interaction.channel.name.startswith("farm-ticket-"):
                # Supprimer le channel actuel
                await ctx_or_interaction.channel.delete()
            else:
                await ctx_or_interaction.send("This command can only be used in ticket channels.")
        else:
            await ctx_or_interaction.send("Vous n'avez pas la permission d'utiliser cette commande.")
    else:  # If it's an interaction
        td_role = discord.utils.get(ctx_or_interaction.guild.roles, name="Technical Director")
        if td_role in ctx_or_interaction.user.roles or ctx_or_interaction.user.guild_permissions.administrator:
            # Vérifier si la commande est utilisée dans un channel ticket
            if ctx_or_interaction.channel.name.startswith("pipeline-ticket-") or ctx_or_interaction.channel.name.startswith("farm-ticket-"):
                # Supprimer le channel actuel
                await ctx_or_interaction.channel.delete()
            else:
                await ctx_or_interaction.send("This command can only be used in ticket channels.")
        else:
            await ctx_or_interaction.send("Vous n'avez pas la permission d'utiliser cette commande.")


if __name__ == '__main__':

    bot = PersistentViewBot()
    bot.remove_command("help")  # Remove the default help command

    @bot.command()
    async def hello(ctx):
        await ctx.send('Hello!')

    @bot.command()
    async def close(ctx):
        """
        # Vérifiez si l'auteur a le rôle "Technical Director" ou est administrateur
        td_role = discord.utils.get(ctx.guild.roles, name="Technical Director")
        if td_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
            # Supprimez le channel actuel
            await ctx.channel.delete()
        else:
            await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        """
        await close_ticket(ctx)


    # run bot
    bot.run('MTE0Mzk4NDI2NjEyOTE5MDk4Mw.GOryrP.PmOJnyAwJYciu5dTcFYOvWlAmt9uy2Q02OLebU')