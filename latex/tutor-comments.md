tutor comments on conception;
This project answers the brief. The marketing department has asked for a tool that they can use for sentiment analysis of new articles. Your conception considers a user interface for customer use as well as metrics to verify system performance. Consider using or comparing other tools than Vader, which, while transparent, has variable performance.  

Please put your code up on GitHub and include the link in your phase 2 submission.

Actions taken in response:
- Added a command-line runner (`cli.py`) and packaging notes to produce a Windows executable for non-technical users.
- Replaced `print()` debugging with structured `logging` and added a `requirements.pinned.txt` for reproducible installs.
- Added `docs/UserGuide.md` and `docs/DeveloperGuide.md` to help marketing users and future developers respectively.
- The implemented code remains modular so alternative or additional models can be compared (as suggested).