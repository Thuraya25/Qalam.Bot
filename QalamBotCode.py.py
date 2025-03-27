#!/usr/bin/env python
# coding: utf-8

# In[1]:


import logging

# Create a logger
logger = logging.getLogger(__name__)

# Set up logging to both a file and the console
logger.setLevel(logging.DEBUG)

# Create handlers for file and console logging
file_handler = logging.FileHandler('bot.log')
console_handler = logging.StreamHandler()

# Create formatter and add it to handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Example log message
logger.debug("Bot has started")



# In[2]:


#import all necessary libraries 
import os
import asyncio
import nest_asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from telegram.constants import ParseMode
import language_tool_python
import nltk
from nltk import pos_tag
from nltk.corpus import wordnet
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.corpus import words
from nltk.tokenize import word_tokenize
import pytz
from datetime import datetime
from telegram import Bot
import spacy
import signal
import sys


# In[3]:


# Download necessary NLTK datasets for NLP tasks

#  'punkt': Used for tokenizing sentences and words.
#  'wordnet': A lexical database for English, useful for word meanings, synonyms, and antonyms.
#  'omw-1.4': Open Multilingual WordNet, which provides multilingual word mapping.
#  'words': A list of English words, useful for spell-checking or filtering non-dictionary words.
nltk.download(['punkt', 'wordnet', 'omw-1.4', 'words'], quiet=True)


# In[7]:


# Apply nest_asyncio to avoid event loop conflicts in Jupyter Notebook
nest_asyncio.apply()


# In[8]:


# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')


# In[9]:


# Initialize LanguageTool for grammar checking
tool = language_tool_python.LanguageTool('en-US')


# In[10]:


# Load the spaCy English language model
nlp = spacy.load('en_core_web_sm')


# In[11]:


# Handle the /start command by sending a welcome message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received command: {update.message.text}")
    """Handle /start command"""
    await update.message.reply_text("""👋 Hello! I'm Qalam, your English assistant bot. I can:\n
📖 Correct grammar errors → Use /correct [sentence]\n
📚 Define words → Use /define [word]\n
🆘 Need help? Type /help
"""
       
    )


# In[12]:


# Handle the /help command by providing usage instructions

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received command: {update.message.text}")
    """Handle /help command"""
    help_text = (
        "ℹ️ **Qalam Bot Help**\n\n"
        "/start - Start conversation\n"
        "/correct <text> - Check grammar\n"
        "/define <word> - Get word definition, examples, and synonyms\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


# In[14]:


# Handle the /correct command to identify and suggest corrections for grammar mistakes

async def correct_grammar(update: Update, context: CallbackContext):
    """Handle the /correct command by correcting grammar and giving feedback."""
    if not context.args:
        await update.message.reply_text("Please provide a sentence: /correct [your sentence]")
        return

    # Get the user's input sentence
    user_sentence = " ".join(context.args)

    # Analyze grammar mistakes
    matches = tool.check(user_sentence)
    corrected_sentence = tool.correct(user_sentence)

    # Construct response message
    response = "📝 **Grammar Check Report:**\n\n"

    if not matches:
        response += "✅ No grammar mistakes found!\n\n"
    else:
        for match in matches:
            incorrect_text = match.context  # Context of the incorrect phrase
            suggestion = match.replacements[0] if match.replacements else "No suggestion available"
            
            response += f"🔸 **Error:** {match.message}\n\n"
            response += f"  ✏️ **Incorrect Phrase:** `{incorrect_text}`\n"
            response += f"  ✅ **Suggested Correction:** `{suggestion}`\n\n"

    # Send the corrected sentence
    response += f"✅ **Final Correction:** `{corrected_sentence}`"

    await update.message.reply_text(response, parse_mode="Markdown")


# In[15]:


# Handle the /define command to provide word definitions,synonyms, POS tagging and examples

async def define_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received command: {update.message.text}")
    """Handle /define command with synonyms and POS tagging"""
    try:
        word = ' '.join(context.args).lower()
        if not word:
            await update.message.reply_text("Please provide a word after /define")
            return

        # Get WordNet synsets
        synsets = wordnet.synsets(word)
        if not synsets:
            await update.message.reply_text(f"❌ No definition found for '{word}'")
            return

        # Use spaCy for POS tagging
        doc = nlp(word)
        pos_tag = doc[0].pos_

        # Start forming the response
        response = f"📚 **{word.capitalize()}**\n\n"
        response += f"🔸 *Part of Speech:* {pos_tag}\n\n"
       
        # Get the first three synsets (different meanings)
        for i, synset in enumerate(synsets[:3], 1):
            # Definition
            definition = synset.definition()
            response += f"**Meaning {i}:** {definition}\n"
           
            # Examples
            examples = synset.examples()[:2]
            if examples:
                response += f"🔹 *Examples:*\n- " + "\n- ".join(examples) + "\n"
           
            # Synonyms handling
            lemmas = [lemma.name().replace('_', ' ') for lemma in synset.lemmas()]
            unique_synonyms = list(set([lem for lem in lemmas if lem != word]))
           
            if unique_synonyms:
                response += f"🔸 *Synonyms:* {', '.join(unique_synonyms)}\n\n"
            else:
                response += "🔸 *No distinct synonyms found*\n\n"
       
        # Send the response
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
       
    except Exception as e:
        logger.error(f"Word definition error: {e}")
        await update.message.reply_text("⚠️ Error fetching word information")


# In[16]:


# Handle text messages that are not commands

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()  # Convert to lowercase for consistency
    
    if "check grammar" in user_message or "correct this" in user_message:
        response = correct_grammar(user_message)  # Call your grammar function
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("I'm not sure, sorry...")


# In[17]:


# Handle errors that occur during the bot's execution

async def error_handler(update, context):
    try:
        if update and update.message:
            print(f"Update {update} caused error: {context.error}")
        else:
            print(f"An error occurred: {context.error}")
    except Exception as e:
        print(f"Error handling the error: {e}")


# In[18]:


# This function handles incoming messages based on whether the bot is mentioned in a group chat or if it's a direct message.

async def process_message(message_type: str, text: str, BOT_USERNAME: str) -> str:
    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, '').strip()
            response = await handle_message(new_text)  # Await handle_response
        else:
            return ''  # Return empty if no bot mention
    else:
        response = await handle_message  (text)  # Await handle_response for normal messages

    return response


# In[19]:


# Set bot's timezone
timezone = pytz.timezone('Asia/Riyadh')
dt = datetime.now(timezone)


# In[20]:


# main function
# This function serves as the entry point for running the bot. 

async def main():
    """Start the bot"""
    try:
        # Initialize the bot
        app = Application.builder().token(TOKEN).build()

        # Command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("correct", correct_grammar))
        app.add_handler(CommandHandler("define", define_word))
        app.add_handler(CommandHandler("help", help_command))
        
        # Message handler
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Error handler
        app.add_error_handler(error_handler)

        # Inform that the bot is running
        print("bot is running..")
        logger.info("Starting Qalam bot...")
        
        # Run the bot
        await app.run_polling(drop_pending_updates=True)
    
    except Exception as e:
        logger.error(f"Error in starting bot: {e}")

# Entry point to run the bot
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(main())  # Works in Jupyter Notebook
        else:
            loop.run_until_complete(main())  # Standard script execution
    except KeyboardInterrupt:
        print("Shutting down the bot...")


# In[ ]:




