# Automatic WhatsApp relay system
Written in Python, powered by Selenium. 

## Usage:
- A WhatsApp account acts as a 'hub', all relevant messages, incoming and outgoing, will be through this 'hub'.
- A "Sales list" determines which accounts act as responders (employees in the company), and they will respond to the messages sent by customers through this 'hub' account.
- Everyone in the sales list can see the messages going in and out of the 'hub' account.
- Supports all text formats and small images, videos and files

## Notes:
- Uses a mysql database to store messages.
- WhatsApp has a forwarding limit of 5 accounts, and this slows down the forwarding process.
- Requires a host desktop to use

## Issues:
- During a small window of time per forwarding process, slight mouse movement can disturb the program
- Only partial support for files that require downloading i.e. large images, videos and documents.
- Instructions on how to initialise and use the mySql database coming soon.

## Log:

### v3.2
- Changed selenium class names due to a WhatsApp update
#### 4-Dec:
- Fixed targeting issue when forwarding