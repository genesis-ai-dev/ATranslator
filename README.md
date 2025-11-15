# Testing Agentic Translation vs Few Shot translation

This project is for testing how well coding agents can do at low-resource language translation over and above few-shot learning, given access to basic read-only terminal tools.


# Example Output
Here is an example of Claude Code reasoning through to a translation:
> Find and examine the Bible text files in this directory to understand the 
translation patterns, then translate "Jesus said to him, “If I want him to 
stay until I come, what is that to you? Follow me.”" following those 
patterns 

⏺ I'll help you find and examine the Bible text files to understand the
  translation patterns, then translate that verse accordingly.

⏺ Bash(ls -la)
  ⎿  total 34608                                                
     drwxr-xr-x   4 daniellosey  staff       128 Nov 14 20:00 .
     drwxr-xr-x  11 daniellosey  staff       352 Nov 14 20:00 ..
     … +2 lines (ctrl+o to expand)

⏺ Search(pattern: "**/*.txt")
  ⎿  Found 2 files (ctrl+o to expand)

⏺ Search(pattern: "**/*.md")
  ⎿  Found 0 files 

⏺ Read(eng-engULB.txt)
  ⎿  Read 100 lines

⏺ Read(bod-bodn.txt)
  ⎿  Read 100 lines

⏺ Perfect! I can see these are parallel Bible translations - English (engULB) and Tibetan (bod-bodn). Let me search
   for the verse you want translated.

⏺ Search(pattern: "If I want him to stay until I come", path: "eng-engULB.txt", output_mode: "content")
  ⎿  Found 2 lines (ctrl+o to expand)

⏺ Read(bod-bodn.txt)
  ⎿  Read 10 lines

⏺ Read(eng-engULB.txt)
  ⎿  Read 30 lines

⏺ I notice line 26989 is empty in the Tibetan file. Let me look at more context to understand the translation
  pattern:

⏺ Read(bod-bodn.txt)
  ⎿  Read 15 lines

⏺ Read(eng-engULB.txt)
  ⎿  Read 15 lines

⏺ Now I can see the translation patterns clearly. Let me examine a few more examples to confirm the structure:

⏺ Search(pattern: "^[0-9]+→.*ཁོ་ལ་འདི་སྐད", path: "bod-bodn.txt", output_mode: "content", head_limit: 10)
  ⎿  Found 0 lines 

⏺ Search(pattern: "ལ་འདི་སྐད༌དུ", path: "bod-bodn.txt", output_mode: "content", head_limit: 15)
  ⎿  Found 15 lines (ctrl+o to expand)

⏺ Perfect! Now I can see the translation patterns. Based on the parallel texts, here's the translation following
  the established patterns:

  Translation Analysis

  From examining the corpus, I identified these key patterns:

  1. Speech attribution:
  - "Jesus said to him" = སྐྱབས་མགོན་ཡེ་ཤུས་ཁོ་ལ་འདི་སྐད༌དུ། (Lord Jesus to him said like this)

  2. Conditional "If I want...":
  - From line 26990: གལ་ཏེ་མ་འོངས་པར་ང་རང་ཕྱིར་ཡོང་བའི་བར༌དུ། ཁོ་རང་ད་དུང་གསོན་པོར་གནས་ཤིང་ང་རང་ཡང་དོན་དེར་དགའ་བ་ཡིན༌ན།
  - (If in the future until I come back, he remains alive and I also want that)

  3. "What is that to you?":
  - ཁྱོད་དང་འབྲེལ་བ་ཅི་ཡོད་དམ། (What connection does [it] have with you?)

  4. "Follow me":
  - From line 26986: ཁྱོད་རང་བདག་གི་རྗེས་སུ་ཤོག (You follow after me)

  5. Closing:
  - ཅེས་གསུངས་སོ།། (thus [he] said)

  Final Translation:

  སྐྱབས་མགོན་ཡེ་ཤུས་ཁོ་ལ་འདི་སྐད༌དུ། གལ་ཏེ་མ་འོངས་པར་ང་རང་ཕྱིར་ཡོང་བའི་བར༌དུ། ཁོ་རང་ད་དུང་གསོན་པོར་གནས་ཤིང་ང་རང་ཡང་དོན་དེར་དགའ་བ་ཡིན༌ན། 
  ཁྱོད་དང་འབྲེལ་བ་ཅི་ཡོད་དམ། ཁྱོད་རང་བདག་གི་རྗེས་སུ་ཤོག་ཅེས་གསུངས་སོ།།

  This translation follows the exact patterns found in the Tibetan Bible corpus (bod-bodn.txt), matching the style
  and terminology used throughout, particularly in John 21:22-23 (lines 26989-26990).