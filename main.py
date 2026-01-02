import os
import discord
from discord.ext import commands
from openai import OpenAI

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = (
    "You are chicken.ai, a factual, careful, and intelligent AI assistant. "
    "You answer like ChatGPT in a clear and neutral tone. "
    "You never guess or make up information. "
    "If you do not know something, you say 'I don't know' clearly. "
    "You only use information explicitly provided by the user or well-known facts. "
    "You remember user-provided personal facts like names when told. "
    "Do not roleplay. Do not add unnecessary humor."
)

# 🔒 Only allow this channel
ALLOWED_CHANNEL_ID = 1456617189762138273

# 🧠 Memory per user
user_memory = {}
MAX_MEMORY_MESSAGES = 8  # keeps bot fast

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🐔 chicken.ai is online as {bot.user}")

@bot.tree.command(name="ask", description="Ask chicken.ai a question")
async def ask(interaction: discord.Interaction, question: str):

    # ❌ Wrong channel
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            "I only respond in the designated channel.",
            ephemeral=True
        )
        return

    # Respond immediately (Discord speed)
    await interaction.response.defer(thinking=True)

    user_id = str(interaction.user.id)

    # Initialize memory
    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    "Only remember facts the user explicitly states. "
                    "Do not infer or assume personal information."
                )
            }
        ]

    # Add user message
    user_memory[user_id].append(
        {"role": "user", "content": question}
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_memory[user_id],
            max_tokens=200,        # ⚡ faster
            temperature=0.2        # factual, less rambling
        )

        reply = response.choices[0].message.content.strip()

        # 🚫 Guard against guessing
        if "i think" in reply.lower() or "maybe" in reply.lower():
            reply = (
                "I don't have enough information to answer that accurately. "
                "Please provide more details."
            )

        # Add bot reply to memory
        user_memory[user_id].append(
            {"role": "assistant", "content": reply}
        )

        # 🧹 Trim memory for speed
        if len(user_memory[user_id]) > MAX_MEMORY_MESSAGES + 2:
            user_memory[user_id] = (
                user_memory[user_id][:2] +
                user_memory[user_id][-MAX_MEMORY_MESSAGES:]
            )

        await interaction.followup.send(reply)

    except Exception as e:
        print(e)
        await interaction.followup.send(
            "An error occurred while processing your request."
        )
@bot.tree.command(name="ping", description="Test command")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

bot.run(os.getenv("DISCORD_TOKEN"))
