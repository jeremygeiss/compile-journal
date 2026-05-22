compile-journal
--- 
- Use journal.sh to create an interstitial journal entry using the bash script. 
- Use compile-journal.py to collect your entries into a single markdown file, whenever you get around to it. It will only collect .md files that follow the specific naming format. 
- Entries are sorted into Journal.md with a date tree structure: Year, Month, Day, Time with corresponding markdown headers.
- After entries are compiled together they are moved an archive folder. Nothing is ever deleted or lost.

It's set up for my personal use and folder structure so you may want to modify to fit your setup. I like neovim, but you could generate your entry with whatever app you want as long as the filename follows the naming convention in compile-journal.py. I recommend setting up aliases in your bashrc to make the process as painless and low friction as possible:


```bash
alias p='python3'
alias j='~/Dropbox/share/code/compile-journal/journal.sh'
alias c-j='p ~/Dropbox/share/code/compile-journal/compile-journal.py'
```
