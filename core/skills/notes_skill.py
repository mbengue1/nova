"""
nova notes skill

this skill enables nova to create and manage notes in the apple notes app.
it supports:
- creating new notes
- adding items to existing notes (like shopping lists)
- finding notes by title

the skill uses the appcontrolservice to interact with the notes app via applescript.
"""
import re
from typing import Optional, Dict, Any, List, Tuple

# import the appcontrolservice
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.services.app_control_service import AppControlService

class NotesSkill:
    """skill for managing notes in the apple notes app"""
    
    def __init__(self):
        """initialize the notes skill"""
        self.app_control = AppControlService()
        
        # define patterns for note commands
        self.patterns = {
            'create_note': [
                r'(create|make|start|new)\s+(a\s+)?(new\s+)?(note|notes)',
                r'(create|make|start|new)\s+(a\s+)?(new\s+)?(note|notes)\s+(called|named|titled|with\s+title)',
                r'(create|make|start|new)\s+(a\s+)?(new\s+)?(note|notes)\s+for',
                r'(create|make|start|new)\s+(a\s+)?(new\s+)?(shopping\s+list|grocery\s+list|to-do\s+list|todo\s+list)'
            ],
            'add_to_note': [
                r'add\s+(to|in|into)\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)',
                r'add\s+(.*)\s+to\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)',
                r'(put|place|write|jot\s+down)\s+(.*)\s+(in|into|to)\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)',
                r'update\s+(my\s+)?(note|notes|shopping\s+list|grocery\s+list)'
            ],
            'find_note': [
                r'(find|search\s+for|look\s+for)\s+(my\s+)?(note|notes)',
                r'(find|search\s+for|look\s+for)\s+(.*)\s+(in|from)\s+(my\s+)?(note|notes)',
                r'(show|list|display)\s+(my\s+)?(note|notes|all\s+notes)'
            ]
        }
    
    def handle_query(self, query: str) -> str:
        """
        handle a notes-related query
        
        args:
            query: the user's query text
            
        returns:
            str: the response to the user
        """
        query_lower = query.lower()
        
        # intelligent note creation for specific topics
        topic_patterns = [
            # format: (pattern, title, [suggested items if requested])
            (r'(?:note|list)\s+(?:on|about|for)\s+(?:the\s+)?basketball', "Basketball Notes", 
             ["Practice schedule", "Stretching routine", "Shooting drills", "Conditioning exercises", "Team roster"]),
            (r'(?:note|list)\s+(?:on|about|for)\s+(?:the\s+)?protein\s+(?:items|foods|sources)', "Protein Foods", 
             ["Grilled chicken", "Greek yogurt", "Eggs", "Salmon", "Tofu", "Lentils", "Chickpeas", "Quinoa", "Cottage cheese", "Almonds"]),
            (r'(?:note|list)\s+(?:on|about|for)\s+(?:the\s+)?workout', "Workout Plan", 
             ["Warm-up routine", "Strength training", "Cardio exercises", "Cool-down stretches", "Weekly schedule"]),
            (r'(?:note|list)\s+(?:on|about|for)\s+(?:the\s+)?study\s+(?:plan|schedule)', "Study Schedule", 
             ["Morning review session", "Afternoon deep work", "Evening summary", "Weekend preparation", "Exam dates"]),
            (r'(?:note|list)\s+(?:on|about|for)\s+(?:the\s+)?project\s+(?:ideas|planning)', "Project Planning", 
             ["Goals and objectives", "Timeline", "Resources needed", "Team responsibilities", "Milestones"]),
        ]
        
        # check if query matches any specific topic pattern
        for pattern, title, suggested_items in topic_patterns:
            if re.search(pattern, query_lower):
                content = ""
                
                # extract content if available
                content_match = re.search(r'(?:with|containing|and\s+add)\s+(?:the\s+)?(?:content\s+of\s+)?(.+?)(?:\.|$)', query_lower)
                if content_match:
                    content = content_match.group(1).strip()
                # if the query mentions "for" a topic but doesn't specify content, suggest some items
                elif re.search(r'for\s+(?:a\s+)?(?:list\s+of\s+)?(?:items|things)', query_lower):
                    content = "\n".join([f"• {item}" for item in suggested_items])
                    
                # create the note
                success, message = self.app_control.create_note(title, content)
                
                if success:
                    if content:
                        return f"I've created a new note titled '{title}' with suggested items based on your request."
                    else:
                        return f"I've created a new note titled '{title}' for you."
                else:
                    return f"I had trouble creating your note: {message}"
                    
                # we found a match, so return after processing
                break
                    
        # special case for "show me all my notes" and similar queries
        if re.search(r'show\s+(?:me\s+)?(?:my\s+)?(?:all\s+)?notes', query_lower) or \
           re.search(r'list\s+(?:my\s+)?(?:all\s+)?notes', query_lower) or \
           re.search(r'display\s+(?:my\s+)?(?:all\s+)?notes', query_lower) or \
           query_lower == 'show me all my notes':
            return self._handle_list_all_notes()
            
        # special case for finding notes about a topic
        if re.search(r'find\s+notes\s+about\s+(\w+)', query_lower):
            match = re.search(r'find\s+notes\s+about\s+(\w+)', query_lower)
            if match:
                search_term = match.group(1).strip()
                return self._handle_find_notes_by_term(search_term)
                
        # special case for adding content to a specific note by topic
        add_to_specific_note_pattern = r'(?:add|put|write)\s+(.+?)\s+(?:in|to|into)\s+(?:my\s+)?(?:note|notes)\s+(?:on|about)\s+(.+?)(?:\s|$|\.|,)'
        match = re.search(add_to_specific_note_pattern, query_lower)
        if match:
            content = match.group(1).strip()
            topic = match.group(2).strip()
            # try to find a note with this topic
            success, notes = self.app_control.find_note(topic)
            if success and notes:
                # add content to the first matching note
                note_title = notes[0]
                add_success, add_message = self.app_control.add_to_note(note_title, content)
                if add_success:
                    return f"I've added '{content}' to your note '{note_title}'."
                else:
                    return f"I had trouble updating your note: {add_message}"
            else:
                # create a new note with this topic as title
                title = ' '.join(word.capitalize() for word in topic.split())
                create_success, create_message = self.app_control.create_note(title, content)
                if create_success:
                    return f"I couldn't find a note about {topic}, so I created a new one titled '{title}' with your content."
                else:
                    return f"I had trouble creating your note: {create_message}"
                    
        # special case for adding items to the most recent note
        add_to_recent_pattern = r'(?:add|put|write)\s+(.+?)\s+(?:in|to|into)\s+(?:my\s+)?(?:that|this|the|last|recent)\s+note'
        match = re.search(add_to_recent_pattern, query_lower)
        if match:
            content = match.group(1).strip()
            # get all notes to find the most recent one
            success, notes = self.app_control.list_notes()
            if success and notes:
                # add content to the most recent note (first in the list)
                note_title = notes[0]
                add_success, add_message = self.app_control.add_to_note(note_title, content)
                if add_success:
                    return f"I've added '{content}' to your most recent note '{note_title}'."
                else:
                    return f"I had trouble updating your note: {add_message}"
            else:
                return "I couldn't find any recent notes to add content to."
                
        # special case for adding items to notes app
        add_to_notes_app_pattern = r'(?:add|put|write)\s+(.+?)\s+(?:in|to|into)\s+(?:my\s+)?(?:notes\s+app|apple\s+notes)'
        match = re.search(add_to_notes_app_pattern, query_lower)
        if match:
            content = match.group(1).strip()
            # create a new note with a generic title
            title = "Quick Note"
            create_success, create_message = self.app_control.create_note(title, content)
            if create_success:
                return f"I've created a new note titled '{title}' with your content."
            else:
                return f"I had trouble creating your note: {create_message}"
        
        # smart note creation for general topics
        general_topic_match = re.search(r'(?:create|make|start)\s+(?:a\s+)?(?:new\s+)?(?:note|list)\s+(?:on|about|for)\s+(?:the\s+)?([a-zA-Z0-9\s]+?)(?:\s+and\s+|\s+with\s+|$)', query_lower)
        if general_topic_match:
            topic = general_topic_match.group(1).strip()
            # format title properly
            title = ' '.join(word.capitalize() for word in topic.split())
            
            # check if we should generate content based on the topic
            generate_content = False
            if re.search(r'with\s+(?:some\s+)?(?:items|content|suggestions)', query_lower) or \
               re.search(r'for\s+(?:a\s+)?(?:list\s+of\s+)?(?:items|things)', query_lower):
                generate_content = True
                
            content = ""
            if generate_content:
                # use the llm to generate appropriate content for this topic
                try:
                    from core.brain import NovaBrain
                    brain = NovaBrain()
                    prompt = f"Generate a brief list of 5-7 items for a note about {topic}. Format as bullet points only."
                    content = brain.process_input(prompt)
                    # clean up the response if needed
                    if content and not content.startswith("-"):
                        content = "\n".join([f"• {line.strip()}" for line in content.split("\n") if line.strip()])
                except Exception as e:
                    print(f"Error generating content: {e}")
            
            # create the note
            success, message = self.app_control.create_note(title, content)
            
            if success:
                if content:
                    return f"I've created a new note titled '{title}' with suggested items based on your request."
                else:
                    return f"I've created a new note titled '{title}' for you."
            else:
                return f"I had trouble creating your note: {message}"
        
        # check for create note patterns
        for pattern in self.patterns['create_note']:
            if re.search(pattern, query_lower):
                return self._handle_create_note(query)
        
        # check for add to note patterns
        for pattern in self.patterns['add_to_note']:
            if re.search(pattern, query_lower):
                return self._handle_add_to_note(query)
        
        # check for find note patterns
        for pattern in self.patterns['find_note']:
            if re.search(pattern, query_lower):
                return self._handle_find_note(query)
        
        # if no pattern matches, return a help message
        return "I can help you create notes, add to existing notes, or find notes. Try saying 'Create a new note for grocery shopping' or 'Add milk to my grocery list'."
    
    def _handle_create_note(self, query: str) -> str:
        """
        handle requests to create a new note
        
        args:
            query: the user's query text
            
        returns:
            str: the response to the user
        """
        # extract the note title from the query
        title = self._extract_note_title(query)
        
        if not title:
             # try to extract a topic from the query
            topic_match = re.search(r'(?:on|about|for)\s+(?:the\s+)?([a-zA-Z0-9\s]+)', query, re.IGNORECASE)
            if topic_match:
                topic = topic_match.group(1).strip()
                # capitalize words in the title
                title = ' '.join(word.capitalize() for word in topic.split())
            else:
                # if we couldn't extract a specific title, use a default
                title = "New Note"
        
        # extract any initial content from the query
        content = self._extract_note_content(query)
        
        # create the note
        success, message = self.app_control.create_note(title, content)
        
        if success:
            if content:
                return f"I've created a new note titled '{title}' with the content you specified."
            else:
                return f"I've created a new note titled '{title}' for you."
        else:
            return f"I had trouble creating your note: {message}"
    
    def _handle_add_to_note(self, query: str) -> str:
        """
        handle requests to add content to an existing note
        
        args:
            query: the user's query text
            
        returns:
            str: the response to the user
        """
        # extract the note title from the query
        title = self._extract_note_title(query)
        
        if not title:
            # if we couldn't extract a specific title, ask for clarification
            return "Which note would you like me to add to? Please specify the note title."
        
        # extract the content to add
        content = self._extract_note_content(query)
        
        if not content:
            # if we couldn't extract content, ask for clarification
            return f"What would you like me to add to the note '{title}'?"
        
        # add the content to the note
        success, message = self.app_control.add_to_note(title, content)
        
        if success:
            return f"I've added your content to the note '{title}'."
        else:
            return f"I had trouble updating your note: {message}"
    
    def _handle_list_all_notes(self) -> str:
        """
        handle requests to list all notes
        
        returns:
            str: the response to the user
        """
        # list all notes
        success, notes = self.app_control.list_notes()
        
        if success and notes:
            if len(notes) > 10:
                return f"You have {len(notes)} notes. Here are the most recent ones: {', '.join(notes[:10])}..."
            else:
                return f"Here are your notes: {', '.join(notes)}"
        elif success:
            return "You don't have any notes yet."
        else:
            return "I had trouble accessing your notes."
    
    def _handle_add_to_grocery_list(self, content: str) -> str:
        """
        handle requests to add items to the grocery list
        
        args:
            content: the content to add to the grocery list
            
        returns:
            str: the response to the user
        """
        if not content:
            return "What would you like me to add to your grocery list?"
        
        # add the content to the grocery list
        success, message = self.app_control.add_to_note("Grocery Shopping List", content)
        
        if success:
            return f"I've added '{content}' to your grocery shopping list."
        else:
            return f"I had trouble updating your grocery list: {message}"
    
    def _handle_add_to_todo_list(self, content: str) -> str:
        """
        handle requests to add items to the to-do list
        
        args:
            content: the content to add to the to-do list
            
        returns:
            str: the response to the user
        """
        if not content:
            return "What would you like me to add to your to-do list?"
        
        # add the content to the to-do list
        success, message = self.app_control.add_to_note("To-Do List", content)
        
        if success:
            return f"I've added '{content}' to your to-do list."
        else:
            return f"I had trouble updating your to-do list: {message}"
    
    def _handle_find_notes_by_term(self, search_term: str) -> str:
        """
        handle requests to find notes by a specific search term
        
        args:
            search_term: the term to search for
            
        returns:
            str: the response to the user
        """
        # find notes matching the search term
        success, notes = self.app_control.find_note(search_term)
        
        if success and notes:
            if len(notes) > 10:
                return f"I found {len(notes)} notes matching '{search_term}'. Here are some: {', '.join(notes[:10])}..."
            else:
                return f"I found these notes matching '{search_term}': {', '.join(notes)}"
        elif success:
            return f"I couldn't find any notes matching '{search_term}'."
        else:
            return "I had trouble searching your notes."
    
    def _handle_find_note(self, query: str) -> str:
        """
        handle requests to find notes
        
        args:
            query: the user's query text
            
        returns:
            str: the response to the user
        """
        # for search queries
        search_term = self._extract_search_term(query)
        
        if not search_term:
            # list all notes
            success, notes = self.app_control.list_notes()
            
            if success and notes:
                if len(notes) > 10:
                    return f"You have {len(notes)} notes. Here are the most recent ones: {', '.join(notes[:10])}..."
                else:
                    return f"Here are your notes: {', '.join(notes)}"
            elif success:
                return "You don't have any notes yet."
            else:
                return "I had trouble accessing your notes."
        else:
            # find notes matching the search term
            success, notes = self.app_control.find_note(search_term)
            
            if success and notes:
                if len(notes) > 10:
                    return f"I found {len(notes)} notes matching '{search_term}'. Here are some: {', '.join(notes[:10])}..."
                else:
                    return f"I found these notes matching '{search_term}': {', '.join(notes)}"
            elif success:
                return f"I couldn't find any notes matching '{search_term}'."
            else:
                return "I had trouble searching your notes."
    
    def _extract_note_title(self, query: str) -> Optional[str]:
        """
        extract the note title from the query
        
        args:
            query: the user's query text
            
        returns:
            optional[str]: the extracted title or none if not found
        """
        # common title patterns
        title_patterns = [
            r'(note|list)\s+(called|named|titled)\s+"([^"]+)"',
            r'(note|list)\s+(called|named|titled)\s+([a-zA-Z0-9\s]+)(?:\s+with|$|\s+containing)',
            r'(create|make|new)\s+(a\s+)?(?:new\s+)?(note|list)\s+(?:called|named|titled|for)\s+"([^"]+)"',
            r'(create|make|new)\s+(a\s+)?(?:new\s+)?(note|list)\s+(?:called|named|titled|for)\s+([a-zA-Z0-9\s]+)(?:\s+with|$|\s+containing)',
            r'add\s+(?:.*)\s+to\s+(?:my\s+)?(?:note|list)\s+(?:called|named|titled)?\s+"([^"]+)"',
            r'add\s+(?:.*)\s+to\s+(?:my\s+)?(?:note|list)\s+(?:called|named|titled)?\s+([a-zA-Z0-9\s]+)(?:\s+with|$|\s+containing)',
            r'add\s+(?:.*)\s+to\s+(?:my\s+)?([a-zA-Z0-9\s]+)(?:\s+note|\s+list)',
            r'add\s+to\s+(?:my\s+)?([a-zA-Z0-9\s]+)(?:\s+note|\s+list)',
            # new patterns for more natural language requests
            r'create\s+(?:a\s+)?(?:new\s+)?note\s+(?:on|about|for)\s+(?:the\s+)?([a-zA-Z0-9\s]+?)(?:\s+and\s+|$)',
            r'make\s+(?:a\s+)?(?:new\s+)?note\s+(?:on|about|for)\s+(?:the\s+)?([a-zA-Z0-9\s]+?)(?:\s+and\s+|$)',
            r'start\s+(?:a\s+)?(?:new\s+)?note\s+(?:on|about|for)\s+(?:the\s+)?([a-zA-Z0-9\s]+?)(?:\s+and\s+|$)',
        ]
        
        # special case for shopping/grocery lists
        if re.search(r'(shopping\s+list|grocery\s+list)', query, re.IGNORECASE):
            return "Grocery Shopping List"
            
        # special case for to-do lists
        if re.search(r'(todo|to-do|to\s+do)\s+list', query, re.IGNORECASE):
            return "To-Do List"
        
        # try each pattern
        for pattern in title_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # the title is in the last group
                return match.group(match.lastindex).strip()
        
        # default title for common scenarios
        if re.search(r'show\s+me\s+all\s+my\s+notes', query, re.IGNORECASE) or \
           re.search(r'list\s+my\s+notes', query, re.IGNORECASE) or \
           re.search(r'display\s+my\s+notes', query, re.IGNORECASE):
            return "all"
        
        return None
    
    def _extract_note_content(self, query: str) -> Optional[str]:
        """
        extract the note content from the query
        
        args:
            query: the user's query text
            
        returns:
            optional[str]: the extracted content or none if not found
        """
        # for "create note" queries, look for content after "with" or "containing"
        create_content_patterns = [
            r'(?:with|containing)\s+(?:content|text)?\s+"([^"]+)"',
            r'(?:with|containing)\s+(?:content|text)?\s+(.+)$',
            # extract content from the query for natural language requests
            r'create\s+(?:a\s+)?(?:new\s+)?note\s+(?:on|about|for)\s+(?:the\s+)?[a-zA-Z0-9\s]+\s+(?:with|containing)\s+(.+)$',
            r'make\s+(?:a\s+)?(?:new\s+)?note\s+(?:on|about|for)\s+(?:the\s+)?[a-zA-Z0-9\s]+\s+(?:with|containing)\s+(.+)$',
            # special patterns for "it should contain" or similar phrases
            r'it\s+should\s+contain\s+(.+?)(?:\.|$)',
            r'should\s+contain\s+(.+?)(?:\.|$)',
            r'(?:that|which)\s+(?:has|contains|includes)\s+(.+?)(?:\.|$)',
        ]
        
        # for "add to note" queries, look for content between "add" and "to"
        add_content_patterns = [
            r'add\s+"([^"]+)"\s+to',
            r'add\s+(.+?)\s+to\s+(?:my\s+)?(?:note|list)',
            r'add\s+to\s+(?:my\s+)?(?:note|list)(?:.*?)\s+"([^"]+)"',
            r'add\s+to\s+(?:my\s+)?(?:note|list)(?:.*?)\s+(.+)$',
            # special case for grocery list items
            r'add\s+(.*?)\s+to\s+(?:my\s+)?(?:grocery|shopping)(?:\s+list)?',
        ]
        
        # try create patterns
        for pattern in create_content_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # try add patterns
        for pattern in add_content_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # remove the note title if it's included in the content
                title = self._extract_note_title(query)
                if title and title in content:
                    content = content.replace(title, "").strip()
                return content
        
        return None
    
    def _extract_search_term(self, query: str) -> Optional[str]:
        """
        extract the search term from the query
        
        args:
            query: the user's query text
            
        returns:
            optional[str]: the extracted search term or none if not found
        """
        # search term patterns
        search_patterns = [
            r'(?:find|search\s+for|look\s+for)\s+"([^"]+)"',
            r'(?:find|search\s+for|look\s+for)\s+([a-zA-Z0-9\s]+)(?:\s+in|\s+from|\s+note|\s+notes|$)',
            r'(?:find|search\s+for|look\s+for)\s+(?:notes|note)\s+(?:about|on|containing)\s+"([^"]+)"',
            r'(?:find|search\s+for|look\s+for)\s+(?:notes|note)\s+(?:about|on|containing)\s+([a-zA-Z0-9\s]+)(?:\s+in|\s+from|$)',
            r'find\s+notes\s+about\s+(\w+)',
        ]
        
        # try each pattern
        for pattern in search_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None