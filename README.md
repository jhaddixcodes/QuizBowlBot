# QuizBowlBot

I don't know about you, but I like playing quiz bowl. Unfortunately, with the summer coming around, I'll be home from university and won't have friends to play it with every week! Oh no! So I decided to make a Discord bot that gets questions from the QBReader database and moderates games for me! Now I can play online with my friends every week!* 

*Unfortunately, building a Discord bot does not guarantee friends to play said Discord bot with. Luckily, you can play the bot solo too, it'll just be extremely lonely!

## How to Use The Bot

I have no fucking clue how asynchronous programming works and so the most important part of this project is a cobbled-together mess of functions. I'll refactor it. Eventually. When it becomes a problem. For now, here's how to use the bot in its current form:

* Use /create_game to create a new game session.
* Use /end_game to delete a game session.
* Use /start_game to start the game.
* Use /next_cycle to go to the next tossup/bonus cycle.
* Use /join_game \[team_number] to join a game.
* Use /leave_game to leave a game.
* During a tossup, buzz by entering either 'buzz' or 'b' in the chat.
* During a bonus, direct an answer by entering either 'direct', 'answer', 'd', or 'a' followed by your answer in the chat.
* To get a score check at any time, type 'score check' or 'sc'. There will also be a final score at the end of the packet.
