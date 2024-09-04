import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
import pytz
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

running = False
period = 5
fire_position = "no_fire"
fire_x = 0
fire_y = 0

class ROSListener(Node):
    def __init__(self):
        super().__init__('discord_listener')
        self.subscription = self.create_subscription(
            String,
            'yolov5/fire_position',
            self.listener_callback,
            10
        )
    
    def listener_callback(self, msg):
        global fire_position
        fire_position = msg.data
        self.get_logger().info(f"Fire position: {fire_position}")

# ROS2 초기화 및 노드 실행
def start_ros_node():
    rclpy.init()
    node = ROSListener()
    return node

def data_load():
    global fire_position
    # fire_position 값이 "no_fire"가 아닐 때 화재 발생을 True로 처리
    TF = fire_position != "no_fire"
    return TF, fire_x, fire_y  # fire_x, fire_y는 추가 정보

@bot.event
async def on_ready():
    print(f'{bot.user.name} - connected')
    # ROS2 노드 비동기 실행
    asyncio.create_task(run_ros_node())

@bot.command(name='set')
async def set_period(ctx):
    global period
    new_period = ctx.message.content[5:]
    if new_period.isdigit() and int(new_period) >= 1:
        new_period = int(new_period)
        embed = discord.Embed(title="시스템 정보 출력 주기", description=f"출력 주기가 {period}초에서 {new_period}초로 수정되었습니다.", color=0x42c1cc)
        period = new_period
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="시스템 정보 출력 주기", description=f"현재 출력 주기는 {period}초입니다.\n1 이상의 정수를 입력해주세요.", color=0x42c1cc)
        await ctx.send(embed=embed)

@bot.command(name='start')
async def start(ctx):
    global running
    if running:
        await ctx.send("작동중입니다.")
        return

    running = True
    tz = pytz.timezone('Asia/Seoul')

    while running:
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        TF, x, y = data_load()

        embed = discord.Embed(title="시스템 정보", color=0xFF9999 if TF else 0x62c1cc)
        embed.add_field(name="시간", value=current_time, inline=False)
        embed.add_field(name="화재 유무", value=TF, inline=False)
        embed.add_field(name="불 위치", value=f"x: {x}\ny: {y}", inline=False)

        await ctx.send(embed=embed)
        await asyncio.sleep(period)

@bot.command(name='end')
async def end(ctx):
    global running
    if not running:
        await ctx.send("작동중이지 않습니다.")
        return

    running = False
    await ctx.send("작동이 중지되었습니다.")

async def run_ros_node():
    node = start_ros_node()
    while rclpy.ok():
        rclpy.spin_once(node)
        await asyncio.sleep(0.1)  # 작은 지연을 통해 비동기 루프가 정상 작동하도록 함

bot.run(TOKEN)