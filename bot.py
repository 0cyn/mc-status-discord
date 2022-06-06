#!/usr/bin/env python3

# complaints? go here: https://forms.gle/EJBHF9YjTyNvfFqt7

import json
import sys
from typing import List
import discord
from discord.ext import tasks
from mcstatus import JavaServer


client = discord.Client()


def split_lr_lists(source: List[str], pad_size: int, out_prefix, out_suffix):
    output_str = out_prefix if out_prefix else ''

    if len(source) < 1:
        output_str += out_suffix
        return output_str

    left, right = source[::2], source[1::2]

    max_left_len = len(max(left, key=len)) + pad_size

    for index, item in enumerate(left):
        output_str += item.ljust(max_left_len, " ")
        output_str += "" if (len(right) - 1 < index) else right[index]
        output_str += "\n"

    return output_str + out_suffix


class MCServerStatusBot:
    INSTANCE = None

    def __init__(self, token, target_channel, server_query_ip, dry=False):
        self.token = token

        MCServerStatusBot.INSTANCE = self

        self.target_channel = target_channel

        self.server_query_ip = server_query_ip

        self.active_status_message = None
        self.startup_has_been_run = False

        self.most_recent_player_list = []

        self.dry = dry

        self.client = client
        client.run(self.token)

    @staticmethod
    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))
        MCServerStatusBot.update_server_status.start()

    @staticmethod
    @tasks.loop(seconds=10)
    async def update_server_status():
        self = MCServerStatusBot.INSTANCE

        channel = client.get_channel(self.target_channel)

        if not channel:
            return

        loading_msg = None
        if not self.startup_has_been_run:
            if self.dry:
                print("Loading...")
            else:
                await channel.purge(limit=100, check=lambda m: m.author == client.user)
                embed = discord.Embed(title="Loading...", description="", color=0x000000)
                loading_msg = await channel.send(embed=embed)
                self.startup_has_been_run = True

        player_name_list = []

        try:
            server = JavaServer.lookup(self.server_query_ip)
            query = server.query()
            player_name_list = query.players.names

            if set(player_name_list) == set(self.most_recent_player_list):
                return

            self.most_recent_player_list = player_name_list
            if len(player_name_list) > 0:
                player_text = split_lr_lists(player_name_list, pad_size=5, out_prefix='```\n', out_suffix='\n```\n')
            else:
                player_text = 'No Players Online'
        except:
            player_text = 'Server Offline'

        if self.dry:
            print(player_text)
        else:
            embed = discord.Embed(title="sh.community.tf", description="", color=0x000000)
            embed.add_field(name="Online", value=str(len(player_name_list)), inline=True)
            embed.add_field(name="Players", value=player_text, inline=False)

            if loading_msg:
                await loading_msg.delete()

            if self.active_status_message:
                await self.active_status_message.edit(embed=embed)
            else:
                self.active_status_message = await channel.send(embed=embed)


if __name__ == "__main__":
    with open('key.json') as j:
        keyfile = json.load(j)
        bot_token = keyfile['token']
        target_channel_id = int(keyfile['target_channel_id'])
        server_query_ip = keyfile['server_query_ip']

    dry_run = False

    if 'dry' in sys.argv:
        print("Doing Dry Run")
        dry_run = True

    MCServerStatusBot(bot_token,
                      target_channel=target_channel_id,
                      server_query_ip=server_query_ip,
                      dry=dry_run)
