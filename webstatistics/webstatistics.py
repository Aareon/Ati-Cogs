import asyncio
import datetime
import os
from aiohttp import web
from cogs.utils.dataIO import dataIO

try:
    import ipgetter
    has_ipgetter = True
except:
    has_ipgetter = False

class WebStatistics:
    def __init__(self, bot):
        self.bot = bot
        self.server = None
        self.app = web.Application()
        self.handler = None
        self.dispatcher = {}
        self.settings = dataIO.load_json('data/webstatistics/settings.json')
        self.ip = ipgetter.myip()
        self.port = self.settings['server_port']
        self.bot.loop.create_task(self.make_webserver())

    async def get_owner(self):
        return await self.bot.get_user_info(self.bot.settings.owner)

    async def get_bot(self):
        return self.bot.user

    async def _get_servers_html(self, data):
        template = """
        <div class="server">
          <div class="avatar">
            <img src="{icon_url}" alt='' />
          </div>
          <div class="title">
            {name} ({members})
          </div>
        </div>"""
        tmp = ''
        for server in data['servers']:
            if server['icon_url']:
                icon_url = server['icon_url']
            else:
                icon_url = 'data:image/gif;base64,R0lGODlhAQABAPcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAP8ALAAAAAABAAEAAAgEAP8FBAA7'
            tmp += template.format(icon_url=icon_url, name=server['name'], members=server['members'])
        return tmp

    async def _get_cogs_html(self, data):
        template = """
        <div class="other-thing">
            {cog}
        </div>"""
        tmp = ''
        for cog in data['loaded_cogs']:
            tmp += template.format(cog=cog)
        return tmp

    async def _get_commands_html(self, data):
        template = """
        <div class="other-thing">
            {command}
        </div>"""
        tmp = ''
        for command in data:
            tmp += template.format(command=command)
        return tmp

    async def generate_body(self):
        data = self.bot.get_cog('Statistics').redapi_hook()
        name = "{0.name}#{0.discriminator}".format(await self.get_bot())
        owner = "{0.name}#{0.discriminator}".format(await self.get_owner())
        all_commands = await self._get_commands_html([command for command in self.bot.commands])
        servers = await self._get_servers_html(data)
        loaded_cogs = await self._get_cogs_html(data)
        with open("webtemplate.html", "r") as web_template:
            body = web_template.format(
                    servers=servers,
                    bot_avatar_icon_url=data['avatar'],
                    name=name,
                    owner=owner,
                    uptime=data['uptime'],
                    total_servers=data['total_servers'],
                    user_count=data['users'],
                    active_cogs=data['cogs'],
                    total_commands=data['total_commands'],
                    total_channels=data['text_channels'],
                    text_channels=data['text_channels'],
                    voice_channels=data['voice_channels'],
                    messages_received=data['read_messages'],
                    commands_run=data['commands_run'],
                    cpu_usage=data['cpu_usage'],
                    memory_usage=data['mem_v'],
                    memory_usage_mb=int(data['mem_v_mb']) / 1024 / 1024,
                    created=data['created_at'],
                    date_now="Page generated on {}".format(datetime.datetime.utcnow()),
                    loaded_cogs=loaded_cogs,
                    all_commands=all_commands,
                    threads=threads,
                    io_reads=data['io_reads'],
                    io_writesdata['io_writes'])
        return body

    async def make_webserver(self):
        async def page(request):
            body = await self.generate_body()
            return web.Response(text=body, content_type='text/html')

        await asyncio.sleep(10)

        self.app.router.add_get('/', page)
        self.handler = self.app.make_handler()

        self.server = await self.bot.loop.create_server(self.handler, '0.0.0.0', self.port)

        print('webstatistics.py: Serving on http://{}:{}'.format(self.ip, self.port))
        message = 'Serving Web Statistics on http://{}:{}'.format(self.ip, self.port)

        await self.bot.send_message(await self.get_owner(), message)

    def __unload(self):
        self.server.close()
        self.server.wait_closed()
        print('webstatistics.py: Stopping server')


def check_folder():
    if not os.path.exists('data/webstatistics'):
        print('Creating data/webstatistics folder...')
        os.makedirs('data/webstatistics')


def check_file():
    data = {}
    data['server_port'] = 4545
    if not dataIO.is_valid_json('data/webstatistics/settings.json'):
        print('Creating settings.json...')
        dataIO.save_json('data/webstatistics/settings.json', data)


def setup(bot):
    if not has_ipgetter:
        raise RuntimeError('ipgetter is not installed. Run `pip3 install ipgetter --upgrade` to use this cog.')
    elif not bot.get_cog('Statistics'):
        raise RuntimeError('To run this cog, you need the Statistics cog')
    else:
        check_folder()
        check_file()
        cog = WebStatistics(bot)
        bot.add_cog(cog)
