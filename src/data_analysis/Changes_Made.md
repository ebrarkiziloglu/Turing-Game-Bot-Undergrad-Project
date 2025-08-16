I made some changes between the experiments.

# Day 1 

* After the 3rd round, I changed the dynamic time interval determining the bot's messaging frequency from [8, 10] to [3, 10].
* I removed the word 'abi' from the prompt to prevent overuse.

# Day 2
* Before starting this day's experiments, I changed the first time the bot writes a message, since it was writing very late at the beginning of the games. I made the bot write its first message in the first [2, 4] seconds.

* We experienced the timeout error often and the bot never spoke during the 2nd, 5th and 10th rounds.

# Day 3
I introduced the following new typo types to the bot:
* Swap adjacent chars with 0.15
* Repeat letter with 0.12
* Remove space with 0.10
* Add space with 0.08
* Remove letter with 0.08
* Double punctuation with 0.07
* Capitalize random with 0.06

I also added the word 'wbu' to the blocked words list as the bot was overusing it.

# Day 4
* I had received the feedback about the accuse buttons always being in the same order. So, I added randomness there.

I also added the word 'hbu' to the blocked words list as the bot was overusing it.