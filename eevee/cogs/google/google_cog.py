import json
import bs4

from discord.ext.commands import BadArgument

from eevee import Cog, group, checks
from eevee.utils import make_embed

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) "
              "Gecko/20100101 Firefox/50.0")


class ImageResult:
    def __init__(self, data, session):
        if isinstance(data, str):
            data = json.loads(data)
        self._session = session
        self.url = data['ou']
        self.title = data['s']
        self.origin_url = data['ru']
        self.thumb_url = data['tu']

    @property
    def embed(self):
        return make_embed(
            title=self.title,
            title_url=self.origin_url,
            image=self.url,
            icon="https://image.flaticon.com/teams/slug/google.jpg")


class ImageQuery:

    URL_FORMAT = "https://www.google.com/search?tbm=isch&q={}"

    def __init__(self, query, session):
        self.query = query
        self.results = None
        self.current_idx = 0
        self._session = session

    def parse(self, result):
        strainer = bs4.SoupStrainer('div', {'class': 'rg_meta notranslate'})
        soup = bs4.BeautifulSoup(result, 'lxml', parse_only=strainer)
        results = soup.find_all('div', {'class': 'rg_meta notranslate'})
        results = [ImageResult(r.string, self._session) for r in results]
        return results

    async def fetch_results(self):
        url = self.URL_FORMAT.format(self.query)
        headers = {'User-Agent': USER_AGENT}
        async with self._session.get(url, headers=headers) as r:
            html = await r.text()
        self.results = self.parse(html)
        return self.results

    @property
    def current_result(self):
        if not self.results:
            return None
        return self.results[self.current_idx]

    @property
    def embed(self):
        if not self.results:
            return None
        return self.current_result.embed

    @classmethod
    async def convert(cls, ctx, argument):
        instance = cls(argument, ctx.bot.session)
        results = await instance.fetch_results()
        if not results:
            raise BadArgument("No Results Found")
        return instance


class WebResult:
    def __init__(self, data):
        title = data.find('h3', {'class': 'r'})
        self.title = title.text
        self.title_url = title.find('a')['href']
        self.info = data.find('span', {'class': 'st'}).text

    @property
    def embed(self):
        return make_embed(title=self.title, title_url=self.title_url,
                          content=self.info)

    @property
    def title_only(self):
        return f"[{self.title}]({self.title_url})"

    @property
    def details(self):
        return f"**[{self.title}]({self.title_url})**\n{self.info}"


class WebQuery:

    URL_FORMAT = "https://www.google.com/search?q={}"

    def __init__(self, query, session):
        self.query = query
        self.results = None
        self.current_idx = 0
        self._session = session

    def parse(self, result):
        strainer = bs4.SoupStrainer('div', {'class': 'rc'})
        soup = bs4.BeautifulSoup(result, 'lxml', parse_only=strainer)
        results = soup.find_all('div', {'class': 'rc'})
        results = [WebResult(r) for r in results]
        return results

    async def fetch_results(self):
        url = self.URL_FORMAT.format(self.query)
        headers = {'User-Agent': USER_AGENT}
        async with self._session.get(url, headers=headers) as r:
            html = await r.text()
        self.results = self.parse(html)
        return self.results

    @property
    def current_result(self):
        if not self.results:
            return None
        return self.results[self.current_idx]

    def embed(self, entries=6):
        if not self.results:
            return None

        top = [r.details for r in self.results[:3]]
        rest = ["\n\n**Other Results:**",]
        rest.extend([r.title_only for r in self.results[3:entries]])

        return make_embed(
            title=f'Google Search for "{self.query}"',
            title_url=self.URL_FORMAT.format(self.query),
            content='\n\n'.join(top) + '\n'.join(rest),
            icon="https://image.flaticon.com/teams/slug/google.jpg")

    @classmethod
    async def convert(cls, ctx, argument):
        instance = cls(argument, ctx.bot.session)
        results = await instance.fetch_results()
        if not results:
            raise BadArgument("No Results Found")
        return instance

class Google(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = self.bot.session

    async def __local_check(self, ctx):
        return await checks.check_is_co_owner(ctx)

    @group(aliases=['g'], invoke_without_command=True)
    async def google(self, ctx, *, query: WebQuery):
        await ctx.embed(embed=query.embed())

    @google.command(aliases=['image', 'images'])
    async def img(self, ctx, *, query: ImageQuery):
        await ctx.embed(embed=query.embed)
