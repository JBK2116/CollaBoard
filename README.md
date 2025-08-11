This is my first "actual" software project. Came up with the idea during a
family game night, we were discussing new games to try out, but we didn't 
have a convenient way to track everyones thoughts efficiently. Sure, we could have used
pencil and paper, but then that would require searching for that somewhere in the house,
manually writing everyones thoughts, implementing a proper summary system, and ensuring that the paper doesn't get lost afterwards.
I thought that it'd just be easier if we could have a very lightweight app that we could instead use. That can create a
meeting in less than 2 minutes and have everyone connected almost instantenously. Then for the summary, I thought,
why not use AI for this. It doesn't have to do complex calculations or code, just simply summarize information, what it does best.
Hence I decided to make this project.

This is currently the first version. It works fairly well, but NOTE - it is to be used only for recreational purposes.
! Do not use this application for meetings that include sensitive data, and things of that sort.
This is a lightweight project that I learned a lot from. 
There are currently some things to improve in it as im sure you'll see when you look into the codebase.

Tech Stack:
- Frontend -> HTML, CSS, Vanilla Javascript
- Backend -> DJANGO

What it does:
Hosts kahoot styled meetings. 
Meetings consist of questions (no multiple choice) and answers (simple text).
Meetings have a set duration of between 1 minute - 1 hour inclusive. 
Meetings can be terminated manually whenver the host decides, otherwise it will be automatically terminated when the duration is up.
After a meeting is over, the host is taken to a summary page where they can summarize and export the meeting.
The meeting is summarized with the use of the OPENAI API, the current model being chatgpt-4.0 mini.
Export options are strictly pdf and docx.

GENERAL FLOW:
Create account to host a meeting -> Create a meeting and enter appropriate details -> Meeting is launched immediately after creation -> User's Join -> Host begins meeting -> Meeting Ends -> Meeting Is Summarized With AI -> Host chooses their method of exporting the summary.

IMPORTANT:
Live meeting state is currently fragile. Host disconnection mid meeting, terminates the meeting. 
Participant disconnection locks them out of the meeting permenantely. This is something that im working to fix.
Meetings and their summaries are not saved. There is no saved state of a meeting once its been hosted.
Meetings and summaries are automatically deleted after creation and first use.

Thank you for reading.



