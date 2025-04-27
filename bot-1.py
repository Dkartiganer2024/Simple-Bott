from dotenv import dotenv_values
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import re
import unicodedata
import asyncio
import pytz

# initialize empty lists
flashcards = []
events = {}
reminders = []

est = pytz.timezone("US/Eastern")

class MyBot(commands.Bot): # define subclass, async setup hook for checking reminder datetime
    async def setup_hook(self):
        self.loop.create_task(reminder_check_loop(self))

async def reminder_check_loop(bot): # checks if datetime of reminder is reached every second
    while True:
        if reminders:
            now = datetime.now(est)
            next_reminder = reminders[0]
            if now >= next_reminder["time"]:
                try:
                    await next_reminder["user"].send(f"🔔 Reminder: **{next_reminder['name']}** is due now!") # send first reminder in dm
                except Exception:
                    pass
                reminders.pop(0)  # Remove first reminder after it's handled
        await asyncio.sleep(0.5)

def normalize_param(text):
    text = unicodedata.normalize('NFKD', text)  # Normalize accents, emojis
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', '', text)  # Remove anything not a-z or 0-9
    return text

if __name__ == '__main__':

    # load token from .env
    config = dotenv_values(".env")
    TOKEN = config['TOKEN']

    intents = discord.Intents.default()
    intents.message_content = True  # Ensure the bot can read messages
    bot = MyBot(command_prefix="!", intents=intents, case_insensitive=True) #Initialize bot

    @bot.command(name="commandHelp")
    async def command_help(ctx):
        help_text = (
            "**📜 Bot Commands:**\n\n"
            "**•!createFlashcard [topic] [question] [answer]** — Creates a new flashcard under the given topic.\n"
            "**•!viewFlashcards [optional topic]** — Views all flashcards, or only flashcards from a specific topic.\n"
            "**•!deleteFlashcard [topic] [question]** — Deletes a flashcard matching the given topic and question.\n\n"
            "**•!quiz [topic]** — Starts a quiz with questions under the given topic.\n\n"
            "**•!createReminder [name] [date MM/DD/YYYY] [time HH:MM]** — Sets a reminder and sends you a DM when it's due.\n"
            "**•!listReminders** — Lists all your active reminders.\n"
            "**•!deleteReminder [name]** — Deletes a reminder by name.\n\n"
            "**•!createEvent [name] [date MM/DD/YYYY] [time HH:MM]** — Schedules a Discord server event.\n"
            "**•!listEvents** — Shows all upcoming scheduled events.\n"
            "**•!deleteEvent [name or ID]** — Deletes a server event by name or ID.\n"
        )

        await ctx.send(help_text)

    ### FLASHCARD COMMANDS ###
    # Flashcards are formatted (topic, question, answer). The topic is normalized, and flashcards are grouped by topic

    @bot.command(name="createFlashcard")
    async def create_flashcard(ctx, topic: str, question: str, answer: str):
        norm = normalize_param(topic) # normalize topic so that similar topic names are combined into one topic (math! vs Math)
        new_flashcard = (topic, question, answer)
        # insert flashcard alongside other flashcards of the same topic
        index = next(
            (i for i, f in enumerate(flashcards) if normalize_param(f[0]) >= norm),
            len(flashcards)
        )
        flashcards.insert(index, new_flashcard)
        await ctx.send(f"✅ Flashcard created for **{topic}**!")

    @bot.command(name="listFlashcards")
    async def list_flashcards(ctx, topic: str = None):
        if not flashcards:
            await ctx.send("No flashcards yet.")
            return

        if topic is None:
            # No filtering, send all
            filtered = flashcards
        else:
            norm_topic = normalize_param(topic)
            # Find starting index manually
            start = next(
                (i for i, f in enumerate(flashcards) if normalize_param(f[0]) >= norm_topic),
                len(flashcards)
            )
            
            # Filter flashcards by topic
            filtered = []
            for i in range(start, len(flashcards)):
                if normalize_param(flashcards[i][0]) != norm_topic:
                    break
                filtered.append(flashcards[i])

        if not filtered:
            await ctx.send(f"No flashcards found for topic '{topic}'." if topic else "No flashcards found.")
            return

        current_msg = ""
        for t, q, a in filtered:
            entry = f"•**{t}:** {q} ||{a}||\n"
            if len(current_msg) + len(entry) > 2000:
                await ctx.send(current_msg)
                current_msg = entry
            else:
                current_msg += entry

        if current_msg:
            await ctx.send(current_msg)

    @bot.command(name="deleteFlashcard")
    async def delete_flashcard(ctx, topic: str, question: str):
        norm_topic = normalize_param(topic)
        question = question.lower()

        for i, (t, q, a) in enumerate(flashcards):
            if normalize_param(t) == norm_topic and q.lower() == question:
                del flashcards[i]
                await ctx.send(f"🗑️ Flashcard on **{t}** with question '**{q}**' deleted.")
                return

        await ctx.send(f"❌ No flashcard found with topic '**{topic}**' and question '**{question}**'.")

    @bot.command(name="quizme")
    async def start_quiz(ctx, *, topic: str): # creates a personalized quiz for a given topic, pulling questions from flashcards
        norm_topic = normalize_param(topic)
        quiz_cards = [f for f in flashcards if normalize_param(f[0]) == norm_topic]

        if not quiz_cards:
            await ctx.send(f"❌ No flashcards found for topic '{topic}'.")
            return

        await ctx.send(f"📨 Check your DMs — starting quiz on **{topic}**!")

        score = 0
        total = len(quiz_cards)
        user = ctx.author

        for i, (t, question, answer) in enumerate(quiz_cards, 1):
            try:
                await user.send(f"❓ Q{i}: {question}")
                msg = await bot.wait_for(
                    "message",
                    check=lambda m: m.author == user and m.guild is None,
                    timeout=60.0
                )

                user_ans = normalize_param(msg.content.strip())
                correct_ans = normalize_param(answer.strip())

                if user_ans == correct_ans:
                    await user.send("✅ Correct!")
                    score += 1
                else:
                    await user.send(f"❌ Wrong. Correct answer: {answer}")
            except Exception:
                await user.send("⏰ Time's up! Moving to next question.")

        await user.send(f"🏁 Quiz finished! Your score: {score}/{total}")

    ### EVENT COMMANDS ###
    # Events are formated (name, datetime). Events use the Discord API to integrate into Discord's scheduled event system

    @bot.command(name='createEvent')
    async def create_event(ctx, name: str, date: str, time: str):
        try:
            # Parse MM/DD/YYYY HH:MM in EST
            dt_naive = datetime.strptime(f"{date} {time}", "%m/%d/%Y %H:%M")
            dt_est = est.localize(dt_naive)
        except ValueError:
            await ctx.send("❌ Use format: `!createEvent \"Event Name\" MM/DD/YYYY HH:MM`")
            return

        # Reject past datetimes
        if dt_est <= datetime.now(est):
            await ctx.send("❌ You can't schedule an event in the past.")
            return

        dt_utc = dt_est.astimezone(pytz.utc)  # Discord needs UTC

        try:
            event = await ctx.guild.create_scheduled_event(
                name=name,
                description="Scheduled by bot.",
                start_time=dt_utc,
                end_time=dt_utc + timedelta(hours=1),
                privacy_level=discord.PrivacyLevel.guild_only,
                entity_type=discord.EntityType.voice,
                location="General Voice Channel"
            )
            await ctx.send(f"✅ Event **{name}** created for {dt_est.strftime('%m/%d/%Y %H:%M')} ET.")
        except Exception as e:
            await ctx.send(f"❌ Failed to create event: {e}")

    @bot.command(name='listEvents')
    async def list_events(ctx):
        events = await ctx.guild.fetch_scheduled_events()
        if not events:
            await ctx.send("📭 No scheduled events found.")
            return

        msg = "\n".join(
            [f"🗓️ **{e.name}** — {e.start_time.strftime('%m/%d/%Y %H:%M')} UTC (ID: `{e.id}`)" for e in events]
        )
        await ctx.send(f"📅 Upcoming Events:\n{msg}")

    @bot.command(name='deleteEvent')
    async def delete_event(ctx, *, identifier: str):
        events = await ctx.guild.fetch_scheduled_events()

        # Try to match by ID
        event = next((e for e in events if str(e.id) == identifier), None)

        # If no ID match, try case-insensitive name match
        if not event:
            event = next((e for e in events if e.name.lower() == identifier.lower()), None)

        if not event:
            await ctx.send(f"❌ No event found matching '{identifier}'.")
            return

        try:
            await event.delete()
            await ctx.send(f"🗑️ Event **{event.name}** deleted.")
        except Exception as e:
            await ctx.send(f"❌ Failed to delete event: {e}")

    ### REMINDER COMMANDS ###
    # Reminders are formatted (name, datetime, user). When the datetime is reached, the bot sends a DM including the reminder name to the corresponding user

    @bot.command(name="createReminder")
    async def create_reminder(ctx, name: str, date: str, time: str):
        try:
            dt_naive = datetime.strptime(f"{date} {time}", "%m/%d/%Y %H:%M")
            dt = est.localize(dt_naive)  # convert to timezone-aware EST
        except ValueError:
            await ctx.send("❌ Invalid date/time format. Use `MM/DD/YYYY HH:MM`")
            return

        if dt <= datetime.now(est):
            await ctx.send("❌ You can't set a reminder in the past.")
            return

        # Check for duplicate name
        for r in reminders:
            if r["user"] == ctx.author and r["name"].lower() == name.lower():
                await ctx.send(f"❌ You already have a reminder named **{name}**.")
                return

        # Insert in sorted order
        index = next((i for i, r in enumerate(reminders) if r["time"] >= dt), len(reminders))
        reminders.insert(index, {"name": name, "time": dt, "user": ctx.author})

        await ctx.send(f"✅ Reminder **{name}** set for {dt.strftime('%m/%d/%Y %H:%M')} EST.")

    @bot.command(name="listReminders")
    async def list_reminders(ctx):
        user_reminders = [r for r in reminders if r["user"] == ctx.author]
        if not user_reminders:
            await ctx.send("📭 You have no reminders.")
            return

        msg = "\n".join([f"**{r['name']}** — {r['time'].strftime('%m/%d/%Y %H:%M')} EST" for r in user_reminders])
        await ctx.send(f"📅 Your Reminders:\n{msg}")

    @bot.command(name="deleteReminder")
    async def delete_reminder(ctx, name: str):
        for r in reminders:
            if r["user"] == ctx.author and r["name"].lower() == name.lower():
                reminders.remove(r)
                await ctx.send(f"🗑️ Reminder **{name}** deleted.")
                return
        await ctx.send(f"❌ No reminder named **{name}** found.")
    
    print("Bot is starting...")
    bot.run(TOKEN)