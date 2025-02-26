import sqlite3
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rapidfuzz import fuzz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

TOKEN = "7800758636:AAGL-xc1PbiPVcSzQ_YmePv9lOF21gJpmpY"
ADMIN_ID = -8148331454  # Replace with your Telegram ID
GOOGLE_SHEETS_JSON = "C:\\Users\\Admin\\Desktop\\vs code extensions\\Telegram\\google_sheets.json"
SHEET_ID = "1uiVtUy1h_Ojmk0_fhfThfE_LEikFhE0fLvl58VnJS6s"

# Database setup
conn = sqlite3.connect("trailblazer_trek.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    player_id INTEGER PRIMARY KEY,
    username TEXT,
    theme TEXT,
    step INTEGER DEFAULT 0,
    start_time REAL,
    step_start_time REAL
    waiting_for_answer INTEGER DEFAULT 0
)
""")
conn.commit()
try:
    cursor.execute("ALTER TABLE progress ADD COLUMN waiting_for_answer INTEGER DEFAULT 0;")
    conn.commit()
except sqlite3.OperationalError:
    pass
# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_JSON, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1  # Open first sheet

# Clues categorized by theme
hunt_data = {
    "Sitcoms": [
        {
            "clue": "'Could I BE any more electric?' If Chandler studied circuits, he'd be here!",
            "location": "department of electrical and electronics engineering",
            "question": "In Friends, what is the name of the TV guide that Joey and Chandler have delivered to their apartment?",
            "answer": "tv guide"
        },
        {
            "clue": "This place is like Sheldon’s spot on the couch—sacred for students who love AI & coding!",
            "location": "department of artificial intelligence and machine learning",
            "question": "In The Big Bang Theory, what is Sheldon Cooper's catchphrase?",
            "answer": "bazinga"
        },
        {
            "clue": "Leonard and Sheldon’s whiteboards would be full here. Find me where equations rule!",
            "location": "department of mathematics",
            "question": "In Brooklyn Nine-Nine, what is the name of Jake Peralta’s favorite movie franchise?",
            "answer": "die hard"
        },
        {
            "clue": "'How you doin’?' If Joey loved food, he’d hang out here!",
            "location": "bakery",
            "question": "In Friends, what food does Joey never share?",
            "answer": "pizza"
        },
        {
            "clue": "What’s the deal with this place? It’s where students crack jokes and presentations!",
            "location": "auditorium",
            "question": "In Seinfeld, what is George Costanza’s biggest fear?",
            "answer": "becoming bald"
        },
        {
            "clue": "This place is like Dunder Mifflin’s Scranton branch—full of paperwork and deadlines!",
            "location": "administrative office",
            "question": "In The Office, what does Jim put in Jell-O as a prank on Dwight?",
            "answer": "a stapler"
        },
        {
            "clue": "Where do geeky physicists and engineers love to gather for scientific experiments?",
            "location": "physics lab",
            "question": "In The Big Bang Theory, what song does Sheldon ask Penny to sing when he's sick?",
            "answer": "soft kitty"
        }
    ],
    "Money Heist": [
        {
            "clue": "If Professor were a CBIT student, this is where he’d plan the heist—where all knowledge is stored!",
            "location": "library",
            "question": "In Money Heist, what is the real name of The Professor?",
            "answer": "sergio marquina"
        },
        {
            "clue": "Like the Royal Mint, this place is full of people working on making millions—just in a different way!",
            "location": "school of management studies",
            "question": "What is the name of the bank targeted in Money Heist Season 3 and 4?",
            "answer": "bank of spain"
        },
        {
            "clue": "Tokyo and Nairobi were always on the move—just like the students who hustle here between classes!",
            "location": "parking lot",
            "question": "In Money Heist, which city name is given to the team’s mastermind?",
            "answer": "the professor"
        },
        {
            "clue": "Just like the escape tunnel in Money Heist, this place leads you to survival—one snack at a time!",
            "location": "food truck",
            "question": "What is the name of the song that becomes an anthem for the heist members?",
            "answer": "bella ciao"
        },
        {
            "clue": "Gold bars are stored in vaults, but here, students store something even more valuable—their creativity!",
            "location": "innovation lab",
            "question": "In Money Heist, which member of the gang is an expert in forging banknotes?",
            "answer": "nairobi"
        }
    ],
    "Crypto": [
        {
            "clue": "I’m a unique piece of digital art stored on the blockchain. People flip me for millions, but I exist only online. Find me where tech meets creativity!",
            "location": "aiml/cse labs opposite sms block",
            "question": "What does NFT stand for?",
            "answer": "non-fungible token"
        },
        {
            "clue": "I am a marketplace where NFTs are bought and sold. My name sounds like the vast ocean. Head to the place where students ‘surf’ for knowledge.",
            "location": "library",
            "question": "Which blockchain is most commonly used for NFTs?",
            "answer": "ethereum"
        },
        {
            "clue": "Just like NFTs, I have rarity levels. You’ll find me where the rarest students work all night!",
            "location": "r and e hub",
            "question": "Are NFTs always expensive? (Yes/No)",
            "answer": "no"
        },
        {
            "clue": "Bitcoin mining takes energy, but so do students pulling all-nighters. Find me where caffeine fuels the grind!",
            "location": "campus café",
            "question": "What is Bitcoin mining?",
            "answer": "the process of validating transactions and adding them to the blockchain using computational power"
        }
    ],
    "Memes": [
        {
            "clue": "Giga-brains learn here, but none are as giga as him!",
            "location": "department of artificial intelligence",
            "question": "What is the popular term for an ultra-intelligent, meme-worthy character, often depicted as a bald muscular figure with glowing eyes?",
            "answer": "giga chad"
        },
        {
            "clue": "If you understand this department’s lessons, you deserve a ‘rizz award.’",
            "location": "department of english literature",
            "question": "What does the slang term 'rizz' mean in Gen Z culture?",
            "answer": "charisma"
        },
        {
            "clue": "You dare oppose me, mortal? If Thanos snapped his fingers in a physics class, he'd be here!",
            "location": "department of physics",
            "question": "In Avengers: Infinity War, what was Thanos’ famous line before snapping his fingers?",
            "answer": "i am inevitable"
        }
    ]
}

# Alternative answers (abbreviations, synonyms)
alternative_answers = {
    "bazinga": ["bazinga!", "sheldon's phrase"],
    "the professor": ["sergio marquina", "money heist mastermind"],
    "non-fungible token": ["nft", "digital asset"],
    "i am inevitable": ["thanos snap", "inevitable"]
}

# Function to check answer with fuzzy matching
def is_correct_answer(user_answer, correct_answer):
    user_answer = user_answer.lower().strip()

    # Check exact match
    if user_answer == correct_answer:
        return True

    # Check alternative answers
    if correct_answer in alternative_answers:
        for alt in alternative_answers[correct_answer]:
            if user_answer == alt:
                return True

    # Use fuzzy matching (above 80% similarity is accepted)
    if fuzz.ratio(user_answer, correct_answer) > 80:
        return True

    return False

# Function to update Google Sheets
def update_google_sheets(username, theme, step, time_taken):
    data = [username, theme, step, time_taken]
    sheet.append_row(data)

# Start command - Theme selection
async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    keyboard = [["Sitcoms", "Money Heist", "Crypto", "Memes"]]
    
    cursor.execute("INSERT OR IGNORE INTO progress (player_id, username, start_time) VALUES (?, ?, ?)",
                   (user.id, user.username, time.time()))
    conn.commit()
    
    await update.message.reply_text("Welcome to the TRAILBLAZER TREK! Choose a theme:",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

# Theme selection handler
async def choose_theme(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    theme = update.message.text

    if theme not in hunt_data:
        await update.message.reply_text("Invalid theme! Please choose from the given options.")
        return

    # ✅ Reset step to 0 so the first clue is always sent
    cursor.execute("UPDATE progress SET theme=?, step=0, step_start_time=? WHERE player_id=?", (theme, time.time(), user.id))
    conn.commit()

    await update.message.reply_text(f"Great choice! Here’s your first clue for {theme}:")
    await send_clue(update, user.id)


# Send the next clue
async def send_clue(update, user_id):
    cursor.execute("SELECT theme, step FROM progress WHERE player_id=?", (user_id,))
    result = cursor.fetchone()

    if result:
        theme, step = result
        if step < len(hunt_data[theme]):  
            clue = hunt_data[theme][step]["clue"]  # ✅ Get the correct clue
            await update.message.reply_text(f"🔎 Clue: {clue}")

            # ✅ Reset waiting_for_answer flag to ensure next input is a location guess
            cursor.execute("UPDATE progress SET step_start_time=?, waiting_for_answer=0 WHERE player_id=?", (time.time(), user_id))
            conn.commit()
        else:
            await update.message.reply_text("🎉 Congratulations! You've completed the trek.")

# Check if the location is correct
async def check_location(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    location = update.message.text.strip().lower()

    cursor.execute("SELECT theme, step FROM progress WHERE player_id=?", (user.id,))
    result = cursor.fetchone()

    if result:
        theme, step = result
        if step < len(hunt_data[theme]) and location == hunt_data[theme][step]["location"]:
            await update.message.reply_text("✅ Correct location! Now scan the QR code, read the question, and send your answer.")

            # ✅ Set waiting_for_answer = 1 so the next input is treated as an answer
            cursor.execute("UPDATE progress SET step_start_time=?, waiting_for_answer=1 WHERE player_id=?", (time.time(), user.id))
            conn.commit()
        else:
            await update.message.reply_text("❌ Wrong location! Try again.")


# Check if the answer is correct and track time taken
async def check_answer(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    answer = update.message.text.strip().lower()

    cursor.execute("SELECT theme, step, step_start_time, waiting_for_answer FROM progress WHERE player_id=?", (user.id,))
    result = cursor.fetchone()

    if result:
        theme, step, step_start_time, waiting_for_answer = result
        correct_answer = hunt_data[theme][step]["answer"].lower()

        # ✅ Ensure the bot is expecting an answer
        if waiting_for_answer == 1:
            if is_correct_answer(answer, correct_answer):
                time_taken = round(time.time() - step_start_time, 2)
                await update.message.reply_text(f"✅ Correct answer! You took {time_taken} seconds. Here's your next clue:")

                update_google_sheets(user.username, theme, step + 1, time_taken)

                # ✅ Move to next clue & reset waiting_for_answer flag
                cursor.execute("UPDATE progress SET step=step+1, step_start_time=?, waiting_for_answer=0 WHERE player_id=?", (time.time(), user.id))
                conn.commit()
                await send_clue(update, user.id)
            else:
                await update.message.reply_text("❌ Wrong answer! Try again.")
        else:
            await update.message.reply_text("❌ First, guess the correct location before answering!")


# Admin command to check player progress
async def check_progress(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT username, theme, step, start_time FROM progress")
    results = cursor.fetchall()

    if not results:
        await update.message.reply_text("No players have started yet.")
        return

    report = "📊 **Player Progress Report:**\n"
    for username, theme, step, start_time in results:
        elapsed_time = round(time.time() - start_time, 2)
        report += f"👤 {username} - Theme: {theme} - Step {step} - Total Time: {elapsed_time} sec\n"

    await update.message.reply_text(report)

# Main function
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(Sitcoms|Money Heist|Crypto|Memes)$"), choose_theme))

    # ✅ First, check locations
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_location))

    # ✅ Then, check answers (only if bot is expecting one)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    print("🤖 Bot is running...")
    app.run_polling()




if __name__ == "__main__":
    main()