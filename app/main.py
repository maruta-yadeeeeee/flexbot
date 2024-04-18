import os
# 環境変数からトークンを読み取る
TOKEN = os.environ.get("DISCORD_TOKEN")
import discord
import typing
import discord
import asyncio
from collections import defaultdict
from discord import app_commands
from typing import Optional, Union
from discord.ui import View, TextInput, Button, Select
from discord import SelectOption
from datetime import datetime
from discord import Intents, Client, Interaction
from discord.app_commands import CommandTree
from discord.ext.commands import BucketType


from discord.ext import commands, tasks
import feedparser
import pytz
import random
import string
import requests
import io
import unicodedata
from captcha.image import ImageCaptcha
from PIL import Image
from discord.ext.commands import Bot, Context
from keep_alive import keep_alive

keep_alive()
intents = discord.Intents.all()
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)
ImageCaptcha = ImageCaptcha()
intents.members = True

@client.event
async def on_ready():
    print('ログインしました')
    update_status.start()

    await tree.sync()

@tasks.loop(seconds=5)
async def update_status():
    servers = len(client.guilds)
    total_members = sum(guild.member_count for guild in client.guilds)
    new_activity = f"テスト中"
    await client.change_presence(activity=discord.Game(new_activity), status=discord.Status.dnd)


@client.event
async def on_interaction(inter:discord.Interaction):
    try:
        if inter.data['component_type'] == 2:
            await on_button_click(inter)
        elif inter.data['component_type'] == 3:
            await on_dropdown(inter)
    except KeyError:
        pass



async def on_button_click(interaction: discord.Interaction):
  custom_id = interaction.data["custom_id"]
  def has_required_role():
    file_path = f'data/{interaction.guild.id}/verify-{interaction.channel.id}'
    if os.path.exists(file_path):
      with open(file_path, 'r', encoding='UTF-8') as file:
          role_id = file.read().strip()
          role = interaction.guild.get_role(int(role_id))
          return role and role in interaction.user.roles
    return False
  if custom_id == "image_au":
      if has_required_role():
          # ユーザーはすでに認証済み
          await interaction.response.send_message("すでに認証済みです。", ephemeral=True)
      else:
          file_path = os.path.join('data', str(interaction.guild.id), f'verify-{interaction.channel.id}')
          if os.path.exists(file_path):
              with open(file_path, 'r', encoding='UTF-8') as file:
                  text = string.ascii_letters + string.digits
                  global captcha_text
                  captcha_text = random.choices(text, k=5)
                  captcha_text = "".join(captcha_text)
                  original = ImageCaptcha.generate(captcha_text)
                  intensity = 20
                  global img
                  img = Image.open(original)
                  small = img.resize(
                      (round(img.width / intensity), round(img.height / intensity))
                  )
                  blur = small.resize(
                      (img.width, img.height),
                      resample=Image.BILINEAR
                  )
                  embed = discord.Embed()
                  a_button = discord.ui.Button(label="認証", style=discord.ButtonStyle.success, custom_id="phot_au")
                  b_button = discord.ui.Button(style=discord.ButtonStyle.primary, custom_id="reimage_au", label="再表示")
                  view = discord.ui.View()
                  view.add_item(a_button)
                  view.add_item(b_button)
                  with io.BytesIO() as image_binary:
                      img.save(image_binary, 'PNG')
                      image_binary.seek(0)
                      file = discord.File(image_binary, filename="captcha_img.png")
                      embed.set_image(url="attachment://captcha_img.png")
                      await interaction.response.send_message(file=file, embed=embed, view=view, ephemeral=True)
          else:
              await interaction.response.send_message("対応するファイルが見つかりませんでした。", ephemeral=True)

  elif custom_id == "reimage_au":
          text = string.ascii_letters + string.digits
          captcha_text = random.choices(text, k=5)
          captcha_text = "".join(captcha_text)
          original = ImageCaptcha.generate(captcha_text)
          intensity = 20
          img = Image.open(original)
          small = img.resize(
              (round(img.width / intensity), round(img.height / intensity))
          )
          blur = small.resize(
              (img.width, img.height),
              resample=Image.BILINEAR
          )
          embed = discord.Embed()
          a_button = discord.ui.Button(label="認証", style=discord.ButtonStyle.success, custom_id="phot_au")
          b_button = discord.ui.Button(style=discord.ButtonStyle.primary, custom_id="reimage_au", label="再表示")
          view = discord.ui.View()
          view.add_item(a_button)
          view.add_item(b_button)
          with io.BytesIO() as image_binary:
              img.save(image_binary, 'PNG')
              image_binary.seek(0)
              file = discord.File(image_binary, filename="captcha_img.png")
              embed.set_image(url="attachment://captcha_img.png")
              await interaction.response.edit_message(attachments=[file], view=view, embed=embed)

  elif custom_id == "phot_au":
          class Questionnaire(discord.ui.Modal):
            auth_answer = discord.ui.TextInput(label=f'認証コードを入力してください', style=discord.TextStyle.short, min_length=4, max_length=7)
            def __init__(self):
                super().__init__(title='認証', timeout=None)
            async def on_submit(self, interaction: discord.Interaction):
                answer = self.auth_answer.value
                lowercase_halfwidth_answer = unicodedata.normalize('NFKC', answer.lower())
                lowercase_captcha_text = captcha_text.lower()
                if lowercase_halfwidth_answer == lowercase_captcha_text:
                    role_id_file_path = f"data/{interaction.guild.id}/verify-{interaction.channel.id}"
                    if os.path.exists(role_id_file_path):
                        with open(role_id_file_path, 'r') as role_id_file:
                            role_id = int(role_id_file.read())
                            role = interaction.guild.get_role(role_id)
                            if role:
                                await interaction.user.add_roles(role)
                                embed = discord.Embed(title='認証完了', color=discord.Colour.green())
                                embed.add_field(name='', value=f'認証ユーザー: {interaction.user.mention}\n付与ロール: {role.mention}')
                                await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                      await interaction.response.send_message("対応するファイルが見つかりませんでした。", ephemeral=True)
                else:
                    embed = discord.Embed(description="**認証に失敗しました**\nもう一度確認するか再表示ボタンを押して画像を更新してください", title=None)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
          await interaction.response.send_modal(Questionnaire())
    
  elif custom_id == "verify_nomal":
    if has_required_role():
        # ユーザーはすでに認証済み
        await interaction.response.send_message("すでに認証済みです。", ephemeral=True)
    else:
        # ファイル名を verify-{interaction.channel.id} に変更
        file_path = os.path.join('data', str(interaction.guild.id), f'verify-{interaction.channel.id}')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='UTF-8') as file:
                role_id = file.read().strip()
                role = interaction.guild.get_role(int(role_id))

                if role:
                    await interaction.user.add_roles(role)
                    embed = discord.Embed(title='認証完了', color=discord.Colour.green())
                    embed.add_field(name='', value=f'認証ユーザー: {interaction.user.mention}\n付与ロール: {role.mention}')
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("指定されたロールが見つかりませんでした。", ephemeral=True)
        else:
            await interaction.response.send_message("対応するファイルが見つかりませんでした。", ephemeral=True)



  elif custom_id == "verify_math":
    if has_required_role():
        # ユーザーはすでに認証済み
        await interaction.response.send_message("すでに認証済みです。", ephemeral=True)
    else:
        file_path = os.path.join('data', str(interaction.guild.id), f'verify-{interaction.channel.id}')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='UTF-8') as file:
                rol = []
                for i in file:
                    i = i.replace('\n', '')
                    rol.append(i)
                role = interaction.guild.get_role(int(rol[0]))

                class VerifyMath(discord.ui.Modal):
                    one = random.randint(1, 30)
                    two = random.randint(1, 30)
                    ans = one + two
                    global ansa
                    ansa = ans
                    auth_answer = TextInput(label=f'{one}+{two}=??', style=discord.TextStyle.short)

                    def __init__(self):
                        super().__init__(title='認証', timeout=None)

                    async def on_submit(self, interaction: Interaction) -> None:
                        if int(self.auth_answer.value) == ansa:
                            await interaction.user.add_roles(role)
                            embed = discord.Embed(title='認証完了', color=discord.Colour.green())
                            embed.add_field(name='', value=f'認証ユーザー: {interaction.user.mention}\n付与ロール: {role.mention}')
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        else:
                            await interaction.response.send_message('計算が間違えています。', ephemeral=True)

                await interaction.response.send_modal(VerifyMath())
        else:
            await interaction.response.send_message("対応するファイルが見つかりませんでした。", ephemeral=True)
    
  elif custom_id.startswith("rolepanel"):
    role_number = int(custom_id.replace("rolepanel", ""))
    try:
        role_panel_message = await interaction.channel.fetch_message(interaction.message.id)
    except discord.HTTPException as e:
        print(f"Error fetching message: {e}")
        await interaction.response.send_message("エラー: メッセージを取得できませんでした。", ephemeral=True)
        return
    file_path = f'data/{interaction.guild.id}/{interaction.channel.id}/rolepanel/{interaction.message.id}.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            role_data = json.load(json_file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        await interaction.response.send_message("対応するファイルが見つかりませんでした。", ephemeral=True)
        return
    selected_role = next((role for role in role_data if role.get("rolenumber") == role_number), None)
    if selected_role:
        member = interaction.guild.get_member(interaction.user.id)
        if discord.utils.get(member.roles, id=int(selected_role["roleid"])):
            try:
                await member.remove_roles(discord.Object(int(selected_role["roleid"])))
                await interaction.response.send_message(f"ロールを削除しました: {selected_role['rolename']}", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("エラー: ロールを削除できません。権限が不足している可能性があります。", ephemeral=True)
        else:
            role = interaction.guild.get_role(int(selected_role["roleid"]))
            if role:
                try:
                    await member.add_roles(role)
                    await interaction.response.send_message(f"ロールを付与しました: {selected_role['rolename']}", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("エラー: ロールを付与できません。権限が不足している可能性があります。", ephemeral=True)
            else:
                await interaction.response.send_message("エラー: ロールを見つけられませんでした。", ephemeral=True)
    else:
        await interaction.response.send_message(f"エラー: ロール番号 {role_number} が見つかりませんでした。", ephemeral=True)



async def on_dropdown(interaction: discord.Interaction):
  custom_id = interaction.data["custom_id"]
  select = None
  if custom_id == "verify":
      selected_value = interaction.data["values"][0] if interaction.data["values"] else None
      if selected_value == "1":
          embed = discord.Embed(title="画像認証", description="下のボタンを押して認証を開始できます", color=discord.Colour.green())
          select = discord.ui.View()
          select.disabled = True
          await interaction.response.edit_message(view=select)
          image_auth_button = discord.ui.Button(style=discord.ButtonStyle.green, custom_id="image_au", label="認証")
          select.add_item(image_auth_button)
          await interaction.channel.send(embed=embed, view=select)
        
      elif selected_value == "2":
          embed = discord.Embed(title="通常認証", description="下のボタンを押して認証を開始できます", color=discord.Colour.green())
          select = discord.ui.View()
          select.disabled = True
          await interaction.response.edit_message(view=select)
          auth_button = discord.ui.Button(style=discord.ButtonStyle.green, custom_id="verify_nomal", label="認証")
          select.add_item(auth_button)
          await interaction.channel.send(embed=embed, view=select)

      elif selected_value == "3":
          embed = discord.Embed(title="計算認証", description="下のボタンを押して認証を開始できます", color=discord.Colour.green())
          select = discord.ui.View()
          select.disabled = True
          await interaction.response.edit_message(view=select)
          math_auth_modal = discord.ui.Button(style=discord.ButtonStyle.green, custom_id="verify_math", label="認証")
          select.add_item(math_auth_modal)
          await interaction.channel.send(embed=embed, view=select)
      else:
          await interaction.response.send_message("Invalid selection.", ephemeral=True)





@tree.command(name="help", description="helpコマンドを表示します")
async def help(interaction: discord.Interaction):
    help_fields = [
        ("/help", "ヘルプを表示します"),
        ("/ping", "ping値を表示します"),
        ("/rename", "ニックネームを変更します"),
        ("/rolepanel", "ロールパネルを作成します"),
        ("/serverinfo", "サーバー情報を表示します"),
        ("/servers", "リストを表示します"),
        ("/top", "最初に送信されたメッセージを取得します"),
        ("/useinfo", "ユーザー情報を表示します"),
        ("/verify", "認証パネルを作成します"),
    ]

    embed = discord.Embed(title="ヘルプコマンド", color=discord.Color.from_rgb(0, 255, 0))
    for name, value in help_fields:
        embed.add_field(name=name, value=value, inline=False)

    # メッセージを送信
    await interaction.response.send_message(embed=embed)

role_panel_message = None
@tree.command(name='rolepanel', description='ロールパネル')
@discord.app_commands.default_permissions(administrator=True)
@app_commands.describe(description='ロールパネルの説明',)
async def rolepanel(interaction: Interaction,ロール1: discord.Role,ロール2: Optional[discord.Role] = None,ロール3: Optional[discord.Role] = None,ロール4: Optional[discord.Role] = None,ロール5: Optional[discord.Role] = None,ロール6: Optional[discord.Role] = None,ロール7: Optional[discord.Role] = None,ロール8: Optional[discord.Role] = None,ロール9: Optional[discord.Role] = None,ロール10: Optional[discord.Role] = None,ロール11: Optional[discord.Role] = None,ロール12: Optional[discord.Role] = None,ロール13: Optional[discord.Role] = None,ロール14: Optional[discord.Role] = None,ロール15: Optional[discord.Role] = None,ロール16: Optional[discord.Role] = None,ロール17: Optional[discord.Role] = None,ロール18: Optional[discord.Role] = None,ロール19: Optional[discord.Role] = None,ロール20: Optional[discord.Role] = None,ロール21: Optional[discord.Role] = None,ロール22: Optional[discord.Role] = None,ロール23: Optional[discord.Role] = None,ロール24: Optional[discord.Role] = None,description:str=''):
    global role_panel_message
    warning_embed = discord.Embed(
        description="パネルを作成しました！",
        color=discord.Color.green(),
    )

    # 警告メッセージの送信
    await interaction.response.send_message(embed=warning_embed, ephemeral=True)

    # ロールパネルの埋め込みメッセージの作成
    panel_embed = discord.Embed(title='ロールパネル', color=discord.Color.green())

    # ボタンの作成
    buttons = []
    role_data = []  # ロールデータを格納するリスト
    roles = [
        ロール1, ロール2, ロール3, ロール4, ロール5,
        ロール6, ロール7, ロール8, ロール9, ロール10,
        ロール11, ロール12, ロール13, ロール14, ロール15,
        ロール16, ロール17, ロール18, ロール19, ロール20,
        ロール21, ロール22, ロール23, ロール24,
    ]

    view = discord.ui.View()

    left_description_text = ""
    left_value_text = ""
    right_description_text = ""
    right_value_text = ""

    for i, role in enumerate(roles):  # 最大25個まで表示
        if role:
            custom_id = f"rolepanel{i + 1}"  # カスタムIDをrolepanel1, rolepanel2のように設定

            # ボタンの設定
            button = discord.ui.Button(style=discord.ButtonStyle.primary, custom_id=custom_id, label=str(i+1))
            buttons.append(button)
            view.add_item(button)

            # ロール情報をリストに追加
            role_data.append({"rolenumber": i + 1, "rolename": role.name, "roleid": str(role.id)})

            # 左側に表示するロール情報を追加
            if i < 12:
                left_description_text += f"{i + 1}: {role.mention}\n"
                left_value_text += f"{i + 1}: {role.mention}\n"
            # 右側に表示するロール情報を追加
            else:
                right_description_text += f"{i + 1}: {role.mention}\n"
                right_value_text += f"{i + 1}: {role.mention}\n"

    

    # 埋め込みメッセージの設定
    panel_embed.add_field(name='', value=description, inline=False)
    panel_embed.add_field(name='', value=left_value_text, inline=True)
    panel_embed.add_field(name='', value=right_value_text, inline=True)

    # ロールパネルの送信
    role_panel_message = await interaction.channel.send(embed=panel_embed, view=view)
    


    # JSONファイルにデータを保存
    directory_path = f'data/{interaction.guild.id}/{interaction.channel.id}/rolepanel/'
    os.makedirs(directory_path, exist_ok=True)
    role_panel_message_id = role_panel_message.id

    # role_dataリストにメッセージIDを追加
    role_data.append({"message_id": role_panel_message_id})

    # JSONファイルにデータを保存
    file_path = f'{directory_path}{role_panel_message_id}.json'
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(role_data, json_file, ensure_ascii=False, indent=4)
    

    # メッセージIDを利用する場合、保存や他の処理に使用できます
    print(f"ロールパネルのメッセージID: {role_panel_message_id}")

@tree.command(name='verify', description='認証パネルを作成します')
@discord.app_commands.default_permissions(administrator=True)
async def verify(interaction: Interaction, 付与したいロール: discord.Role):
    role = 付与したいロール
    folder_path = f'data/{interaction.guild.id}'

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, f'verify-{interaction.channel.id}')

    with open(file_path, 'w', encoding='UTF-8') as file:
        file.write(f'{role.id}')

    select = [
        discord.SelectOption(label="画像認証", value="1", description="captchaを使用した認証方法です"),
        discord.SelectOption(label="通常認証", value="2", description="ボタンを押すだけの認証方法です"),
        discord.SelectOption(label="計算認証", value="3", description="計算問題を解く認証方法です")
    ]

    view = discord.ui.View()
    view.add_item(discord.ui.Select(custom_id="verify", options=select))

    embed = discord.Embed(title="認証パネル", description=f'**付与されるロール:** {role.mention}', color=discord.Colour.green())
    embed.add_field(name='注意事項', value="一つのチャンネルに複数のパネルを作成することはできません\n一つのチャンネルに複数のパネルが作成された場合は後に指定されたロールを付与するようになります")

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@tree.command(name="ping", description="ping値を表示します")
async def ping(interaction: discord.Interaction):
    raw_ping = interaction.client.latency
    ping = round(raw_ping * 1000)
    embed = discord.Embed(title="Pong!",description=f"BotのPing値は{ping}msです。",
    color=discord.Color.from_rgb(0, 255, 0))
    await interaction.response.send_message(embed=embed)

@tree.command(name="top", description="最初に送信されたメッセージを取得します")
async def firstmessage(interaction: discord.Interaction):
    first_message = None
    async for message in interaction.channel.history(oldest_first=True, limit=1):
        first_message = message
        break
    if first_message:
        message_url = first_message.jump_url
        button_message_link = discord.ui.Button(
            label="メッセージリンク",
            style=discord.ButtonStyle.link,
            url=message_url
        )
        embed = discord.Embed(title="最初のメッセージ", color=discord.Color.from_rgb(0, 255, 0))
        embed.add_field(name="", value="下のボタンから飛べます", inline=False)
        view = discord.ui.View()
        view.add_item(button_message_link)
        await interaction.response.send_message(embed=embed, view=view)
    else:
        await interaction.response.send_message("このチャンネルにはメッセージがありません。")

import json
from discord import File



@tree.command(name="serverinfo", description="サーバー情報を表示")
async def serverinfo(interaction: discord.Interaction, serverid: Optional[str] = 'default_message'):
    # サーバーIDが指定されていない場合はコマンドを実行したサーバーの情報を表示
    if serverid == 'default_message':
        guild = interaction.guild
    else:
        # サーバーIDが指定された場合はそのサーバーの情報を表示
        guild_id = int(serverid)
        bot = interaction.client  # or interaction.bot, depending on your Discord.py version
        guild = bot.get_guild(guild_id)

    if guild:
        # サーバーの情報を埋め込みメッセージで表示
        account_avatar_url = guild.icon.url if guild.icon else None
        embed = discord.Embed(title=f"{guild.name} の情報", color=0x00ff00)
        embed.set_thumbnail(url=account_avatar_url)
        embed.add_field(name="オーナー", value=f"{guild.owner.name}#{guild.owner.discriminator} (ID: {guild.owner.id})", inline=False)
        embed.add_field(name="作成日", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)

        # ボットと人のメンバー数を計算
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = guild.member_count - bot_count

        embed.add_field(name="メンバー数", value=f"トータル: {guild.member_count} 人\n人間: {human_count} 人\nボット: {bot_count} 人", inline=False)
        embed.add_field(name="チャンネル数", value=f"トータル: {len(guild.channels)}\nテキストチャンネル: {len(guild.text_channels)}\nボイスチャンネル: {len(guild.voice_channels)}\nカテゴリ  {len(guild.categories)}", inline=False)
        embed.add_field(name="ロール数", value=f"トータル: {len(guild.roles)}", inline=False)
        embed.add_field(name="ブースト", value=f"レベル: {guild.premium_tier}\n {guild.premium_subscription_count} 回",inline=False)

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("指定されたサーバーが見つかりませんでした。")

@tree.command(name="userinfo", description="ユーザー情報を確認")
async def userinfo(interaction: discord.Interaction, userid: typing.Optional[str] = None):
    if userid is None:
        userid = interaction.user
    else:
        userid = interaction.guild.get_member(int(userid))

    if userid:
        account_name = f"{userid.name}#{userid.discriminator}"
        account_id = userid.id
        account_created_at = userid.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # ユーザーのアバターのURLを取得
        account_avatar_url = userid.avatar.url if userid.avatar else userid.default_avatar.url
        flags_info = "\n".join(f"{flag}: {getattr(userid.public_flags, flag)}" for flag in dir(userid.public_flags) if flag.isupper())

        # 埋め込みメッセージを作成
        embed = discord.Embed(
            title="ユーザー情報",
            color=discord.Color.from_rgb(0, 255, 0)
        )
        embed.set_thumbnail(url=account_avatar_url)
        embed.add_field(name="ユーザー名", value=account_name, inline=False)
        embed.add_field(name="ユーザーID", value=account_id, inline=False)
        embed.add_field(name="アカウント作成日", value=account_created_at, inline=False)
        embed.add_field(name="ボット？", value="はい" if userid.bot else "いいえ", inline=False)
        embed.add_field(name="その他", value=f"{flags_info}", inline=False)

        # メッセージを送信
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("指定されたユーザーが見つかりませんでした。", ephemeral=True)

@tree.command(name='rename', description='ニックネームを変更')
@discord.app_commands.default_permissions(administrator=True)
async def rename(interaction: discord.Interaction, 変更後のニックネーム: str):
    if len(変更後のニックネーム) > 32:
        await interaction.response.send_message("エラー: 32文字以下で指定してください。",ephemeral=True)
        return
    if interaction is not None:
        new_nickname = 変更後のニックネーム
        await interaction.guild.me.edit(nick=new_nickname)
        await interaction.response.send_message(f'ニックネームを `{new_nickname}` に変更しました！',ephemeral=True)
    else:
        print("Interactionが存在しません")

@tree.command(name="servers", description="リストを表示します")
async def servers(interaction: discord.Interaction):
    allowed_user_id = 952490802574164039
    if interaction.user.id != allowed_user_id:
        await interaction.response.send_message("このコマンドは指定されたユーザーのみが実行できます。")
        return
    servers_dict = {}
    for guild in interaction.client.guilds:
        if guild.name in servers_dict:
            servers_dict[guild.name].append(str(guild.id))
        else:
            servers_dict[guild.name] = [str(guild.id)]

    # JSON ファイルに保存
    with open('servers.json', 'w', encoding='utf-8') as json_file:
        json.dump(servers_dict, json_file, ensure_ascii=False, indent=4)

    # JSON ファイルをdiscord.Fileに変換して送信
    file = File('servers.json', filename='servers.json')
    await interaction.response.send_message(file=file)



import os
import json



import re

global_channel_name = "flexchat"
test_channel_name = "test"

@client.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and message.author != client.user:
        target_user_ids = [952490802574164039]

        for target_user_id in target_user_ids:
            target_user = client.get_user(target_user_id)
            if target_user:
                embed = discord.Embed(title='DMが送信されました', description=f'{message.author}\n{message.content}', color=discord.Colour.green())
                await target_user.send(embed=embed)
    elif isinstance(message.channel, discord.TextChannel):
        if message.channel.name == global_channel_name:
          if message.author.bot or message.author.id == client.user.id:
              return

          for channel in client.get_all_channels():
              if channel.name == global_channel_name:
                  if channel == message.channel:
                      continue
                  jst = pytz.timezone('Asia/Tokyo')
                  created_at_jst = message.created_at.astimezone(jst)
                  embed = discord.Embed(description=message.content, color=discord.Colour.green())
                  embed.set_author(
                      name="{}#{} ({})".format(
                          message.author.name,
                          message.author.discriminator,
                          message.author.id
                      ),
                      icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                  )
                  embed.set_footer(
                      text="{}({})・{}・{}".format(
                          message.guild.name, message.guild.id, message.id, created_at_jst.strftime("%Y-%m-%d %H:%M:%S")),
                      icon_url=message.guild.icon.url if message.guild.icon else None
                  )
                  if message.attachments != []:  # 添付ファイルが存在するとき
                      embed.set_image(url=message.attachments[0].url)
                  warning_displayed = False
                  buttons = []  # ボタンを格納するリスト

                  # メッセージに添付されたファイルの処理
                  for index, attachment in enumerate(message.attachments):
                      if not warning_displayed:
                          embed.add_field(name="警告", value="添付されているファイルは安全ではない可能性があります", inline=False)
                          warning_displayed = True
                      file_name = attachment.filename
                      file_url = attachment.url
                      embed.description += f"\nFile{index + 1}:[{file_name}]({file_url})"
                      # ファイル用のボタンを作成
                      file_link_button = discord.ui.Button(
                          label=f"File{index + 1}",
                          style=discord.ButtonStyle.link,
                          url=file_url
                      )
                      buttons.append(file_link_button)

                  # メッセージにリンクが含まれていたらリンクボタンを作成
                  if any(url in message.content for url in ["http", "https"]):
                      for index, url in enumerate(re.findall(r'https?://[^\s]+', message.content)):
                          link_button = discord.ui.Button(
                              label=f"Link{index + 1}",
                              style=discord.ButtonStyle.link,
                              url=url
                          )
                          buttons.append(link_button)

                  # ボタンを埋め込みメッセージに追加
                  if buttons:
                      button_view = discord.ui.View()
                      for button in buttons:
                          button_view.add_item(button)
                      await channel.send(embed=embed, view=button_view)
                  else:
                      await channel.send(embed=embed)

                  if message.reference:
                      reference_msg = await message.channel.fetch_message(message.reference.message_id)
                      if reference_msg.embeds and reference_msg.author == client.user:
                          reference_message_content = reference_msg.embeds[0].description
                          reference_message_author = reference_msg.embeds[0].author.name
                      elif reference_msg.author != client.user:
                          reference_message_content = reference_msg.content
                          reference_message_author = reference_msg.author.name + '#' + reference_msg.author.discriminator
                      reference_content = ""
                      for string in reference_message_content.splitlines():
                          reference_content += "> " + string + "\n"
                      reference_value = "**@{}**\n{}".format(reference_message_author, reference_content)
                      embed.add_field(name='返信しました', value=reference_value, inline=True)
                      try:
                          await channel.send(embed=embed)
                      except Exception as e:
                          print(f"Error sending embed message: {e}")

          await message.add_reaction('✅')


      
        elif message.channel.name == test_channel_name:
          if message.author.bot or message.author.id == client.user.id:
              return

          for channel in client.get_all_channels():
              if channel.name == test_channel_name:
                  if channel == message.channel:
                      continue
                  jst = pytz.timezone('Asia/Tokyo')
                  created_at_jst = message.created_at.astimezone(jst)
                  embed = discord.Embed(description=message.content, color=discord.Colour.green())
                  embed.set_author(
                      name="{}#{} ({})".format(
                          message.author.name,
                          message.author.discriminator,
                          message.author.id
                      ),
                      icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                  )
                  embed.set_footer(
                      text="{}({})・{}・{}".format(
                          message.guild.name, message.guild.id, message.id, created_at_jst.strftime("%Y-%m-%d %H:%M:%S")),
                      icon_url=message.guild.icon.url if message.guild.icon else None
                  )
                  if message.attachments != []:  # 添付ファイルが存在するとき
                      embed.set_image(url=message.attachments[0].url)
                  warning_displayed = False
                  buttons = []  # ボタンを格納するリスト

                  # メッセージに添付されたファイルの処理
                  # メッセージに添付されたファイルの処理
                  for index, attachment in enumerate(message.attachments):
                      if not warning_displayed:
                          embed.add_field(name="警告", value="添付されているファイルは安全ではない可能性があります", inline=False)
                          warning_displayed = True
                      file_name = attachment.filename
                      file_url = attachment.url
                      embed.description += f"\nFile{index + 1}:[{file_name}]({file_url})"
                      # ファイル用のボタンを作成
                      file_link_button = discord.ui.Button(
                          label=f"File{index + 1}",
                          style=discord.ButtonStyle.link,
                          url=file_url
                      )
                      buttons.append(file_link_button)

                  # メッセージにリンクが含まれていたらリンクボタンを作成
                  if any(url in message.content for url in ["http", "https"]):
                      for index, url in enumerate(re.findall(r'https?://[^\s]+', message.content)):
                          link_button = discord.ui.Button(
                              label=f"Link{index + 1}",
                              style=discord.ButtonStyle.link,
                              url=url
                          )
                          buttons.append(link_button)

                  # ボタンを埋め込みメッセージに追加
                  if buttons:
                    button_view = discord.ui.View()
                    for button in buttons:
                        button_view.add_item(button)
                    response_message = await channel.send(embed=embed, view=button_view)
                  else:
                    response_message = await channel.send(embed=embed)

                  if message.reference:
                    reference_msg = await message.channel.fetch_message(message.reference.message_id)
                    if reference_msg.embeds and reference_msg.author == client.user:
                        reference_message_content = reference_msg.embeds[0].description
                        reference_message_author = reference_msg.embeds[0].author.name
                    elif reference_msg.author != client.user:
                        reference_message_content = reference_msg.content
                        reference_message_author = reference_msg.author.name + '#' + reference_msg.author.discriminator
                    reference_content = ""
                    for string in reference_message_content.splitlines():
                        reference_content += "> " + string + "\n"
                    reference_value = "**@{}**\n{}".format(reference_message_author, reference_content)
                    embed.add_field(name='返信しました', value=reference_value, inline=True)
                    try:
                        await response_message.edit(embed=embed)
                    except Exception as e:
                        print(f"Error editing embed message: {e}")

          await message.add_reaction('✅')

import shutil
import discord
import os


@client.event
async def on_guild_channel_delete(channel):
    # チャンネルがロールパネル関連のものであるか判定（適切な条件を追加してください）
    channel_directory_path = f'data/{channel.guild.id}/{channel.id}/'

    # ディレクトリが存在するか確認してから削除
    if os.path.exists(channel_directory_path):
        shutil.rmtree(channel_directory_path)
        print(f"チャンネル関連ディレクトリを削除しました: {channel_directory_path}")
    else:
        print(f"チャンネル関連ディレクトリが見つかりませんでした: {channel_directory_path}")

import discord
  
import os
import shutil

@client.event
async def on_guild_remove(guild):
    # ギルドに関連するディレクトリを削除
    guild_directory_path = f'data/{guild.id}/'

    # ディレクトリが存在するか確認してから削除
    if os.path.exists(guild_directory_path):
        shutil.rmtree(guild_directory_path)
        print(f"ギルド関連ディレクトリを削除しました: {guild_directory_path}")
    else:
        print(f"ギルド関連ディレクトリが見つかりませんでした: {guild_directory_path}")

@client.event
async def on_guild_join(guild):
    # サーバーオーナーにDMを送信
    owner = guild.owner
    owner_dm = await owner.create_dm()
    embed = discord.Embed(title="お知らせ",description=f"{guild.name}へ導入ありがとうございます！\n</help:1188517551421001840>で使い方を確認できます！",color=discord.Color.green())
    invite_link = discord.ui.Button(
      label="サーバーに参加",
      style=discord.ButtonStyle.link,
      url="https://discord.com/invite/GE4mraS7YQ"
    )
    bot_link = discord.ui.Button(
      label="🤖 ボットを追加",
      style=discord.ButtonStyle.link,
      url="https://discord.com/oauth2/authorize?client_id=1173979901859205160&permissions=8&scope=bot%20applications.commands"
    )
    view = discord.ui.View()
    view.add_item(invite_link)
    view.add_item(bot_link)
    await owner_dm.send(embed=embed,view=view)
  
@client.event
async def on_guild_remove(guild):
    # サーバーが削除されたときに実行されるコード
    owner = guild.owner
    owner_dm = await owner.create_dm()

    embed = discord.Embed(
        title="お知らせ",
        description=f"{guild.name}からボットが削除またはbanされました",
        color=discord.Color.red()
    )

    invite_link = discord.ui.Button(
      label="サーバーに参加",
      style=discord.ButtonStyle.link,
      url="https://discord.com/invite/GE4mraS7YQ"
    )
    bot_link = discord.ui.Button(
      label="🤖 ボットを追加",
      style=discord.ButtonStyle.link,
      url="https://discord.com/oauth2/authorize?client_id=1173979901859205160&permissions=8&scope=bot%20applications.commands"
    )
    view = discord.ui.View()
    view.add_item(invite_link)
    view.add_item(bot_link)
    await owner_dm.send(embed=embed,view=view)
  
@client.event
async def on_member_join(member):
    server_name = member.guild.name

    embed = discord.Embed(title=f'ようこそ、{member.name}さん！', description=f"{server_name}への参加ありがとうございます。", color=discord.Color.from_rgb(0, 255, 0))
    invite_link = discord.ui.Button(
        label="サーバーに参加",
        style=discord.ButtonStyle.link,
        url="https://discord.com/invite/GE4mraS7YQ"
    )
    bot_link = discord.ui.Button(
        label="🤖 ボットを追加",
        style=discord.ButtonStyle.link,
        url="https://discord.com/oauth2/authorize?client_id=1173979901859205160&permissions=8&scope=bot%20applications.commands"
    )
    view = discord.ui.View()
    view.add_item(invite_link)
    view.add_item(bot_link)
    try:
        dm_channel = await member.create_dm()
        await dm_channel.send(embed=embed, view=view)
    except discord.Forbidden:
        print(f'Unable to send welcome message to {member.name}. DMs are disabled or bot lacks permissions.')
    except Exception as e:
        print(f'An error occurred: {e}')





if TOKEN is None:
    print("環境変数 DISCORD_BOT_TOKEN が設定されていません。")
else:
    client.run(TOKEN)
