import paramiko
import subprocess
import telegram
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from bot import bot, dispatcher


def execute_command(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="example.com", username="username", password="password")
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    client.close()
    return output, error

def vps(update, context):
    chat_id = update.effective_chat.id
    bot.send_message(chat_id=chat_id, text='Please enter your VPS username, IP and password separated by spaces')
    
    # Wait for user input
    def wait_for_input(update, context):
        user_input = update.message.text.split(' ')
        if len(user_input) != 3:
            bot.send_message(chat_id=chat_id, text='Invalid input')
            return
        username, ip, password = user_input

        # Connect to VPS
        command = f'ssh {username}@{ip}'
        output, error = execute_command(command)

        # Check for errors
        if error:
            bot.send_message(chat_id=chat_id, text=f'Error connecting to VPS: {error}')
            return

        # Open terminal
        command = 'gnome-terminal'
        execute_command(command)

        # Wait for user input
        bot.send_message(chat_id=chat_id, text='Enter command to run on VPS')

        # Set up handler to wait for user input
        message_handler = MessageHandler(Filters.text & ~Filters.command, run_command)
        context.dispatcher.add_handler(message_handler)

        # Save VPS details in context for use in run_command function
        context.user_data['vps_details'] = {'username': username, 'ip': ip, 'password': password}

    # Set up handler to wait for VPS details input
    vps_input_handler = MessageHandler(Filters.text & ~Filters.command, wait_for_input)
    context.dispatcher.add_handler(vps_input_handler)


def run_command(update, context):
    chat_id = update.effective_chat.id

    # Retrieve VPS details from context
    vps_details = context.user_data.get('vps_details')
    if not vps_details:
        bot.send_message(chat_id=chat_id, text='Error: VPS details not found')
        return

    # Run command on VPS
    command = f'sshpass -p {vps_details["password"]} ssh {vps_details["username"]}@{vps_details["ip"]} {update.message.text}'
    output, error = execute_command(command)

    # Send output to Telegram
    if output:
        bot.send_message(chat_id=chat_id, text=output)
    if error:
        bot.send_message(chat_id=chat_id, text=error)

    # Remove message handler to prevent it from being called again
    context.dispatcher.remove_handler(context.handler_stack[-1])

vps_handler = CommandHandler('vps', vps)
dispatcher.add_handler(vps_handler)
