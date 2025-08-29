import time
import json
import asyncio
from typing import Dict, Any, Optional
from openai import OpenAI
import os
from .database import DatabaseManager
from .template import EbookTemplate
from .content_saver import content_saver
from .event_notifier import event_notifier

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        self.request_count = 0
        self.request_window_start = time.time()
        self.max_requests_per_minute = 20  # Conservative limit for API calls
        self.current_session_id = None  # Will be set by ContentPipeline
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting to prevent API quota exceeded errors"""
        current_time = time.time()
        
        # Enforce minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        
        # Reset counter if window has passed
        if current_time - self.request_window_start > 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # Check if we're approaching the rate limit
        if self.request_count >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                print(f"Rate limit reached, waiting {sleep_time:.2f} seconds...")
                await asyncio.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def generate_completion(self, prompt: str, max_tokens: int = 2000, request_type: str = "general", model: str = "gpt-4.1") -> str:
        await self._enforce_rate_limit()
        
        request_start_time = time.time()
        
        # Notify LLM request started
        if self.current_session_id:
            await event_notifier.notify_llm_started(
                self.current_session_id, request_type, self.request_count
            )
        
        try:
            print(f"Making LLM request #{self.request_count} ({request_type}) with {model} at {time.strftime('%H:%M:%S')}")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            request_duration = time.time() - request_start_time
            print(f"LLM request #{self.request_count} ({request_type}) completed in {request_duration:.2f}s")
            
            # Notify LLM request completed
            if self.current_session_id:
                await event_notifier.notify_llm_completed(
                    self.current_session_id, request_type, self.request_count, request_duration
                )
            
            return response.choices[0].message.content
        except Exception as e:
            request_duration = time.time() - request_start_time
            print(f"LLM request #{self.request_count} ({request_type}) failed after {request_duration:.2f}s: {str(e)}")
            
            # Notify LLM request error
            if self.current_session_id:
                await event_notifier.notify_llm_error(
                    self.current_session_id, request_type, self.request_count, str(e)
                )
                
            return f"Error generating content: {str(e)}"

class SummarizationAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_template = """
        Summarize this research paper for educational purposes. Extract main concepts and key findings, identify learning objectives for students, create chapter outlines for educational content, preserve technical accuracy and important details, and structure content in a logical learning progression.
        
        Text: {text}
        User Requirements: {user_prompt}
        
        Provide only a structured summary with these sections:
        1. Main Learning Objectives
        2. Key Concepts
        3. Chapter Outline
        4. Important Findings
        
        Do not include any introductory text, preamble, or conclusions. Start directly with the learning objectives.
        """
    
    async def process(self, text: str, user_prompt: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(text=text[:4000], user_prompt=user_prompt or "Create a comprehensive educational resource")
        summary = await self.llm_client.generate_completion(prompt, request_type="document_summarization", model="gpt-3.5-turbo")
        
        processing_time = time.time() - start_time
        
        return {
            'summary': summary,
            'processing_time': processing_time,
            'agent_type': 'summarizer'
        }

class ContentGenerationAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.template_generator = EbookTemplate()
        
        # Updated prompt to work with structured template
        self.analysis_prompt = """
        Analyze the following educational content summary and extract key information:
        - Identify the main topic and create a suitable title
        - List 5 key concepts that should be covered
        - Identify any technical processes or procedures
        - Note any quantitative aspects that might need calculators
        - Suggest practical applications or case studies
        - Determine the content structure based on user requirements
        
        Summary: {summary}
        User Requirements: {user_prompt}
        
        IMPORTANT: Pay special attention to the user requirements for structuring:
        - If user mentions "days", "daily", "day-by-day" -> create daily structure
        - If user mentions "weeks", "weekly" -> create weekly structure  
        - If user mentions "modules", "lessons" -> create modular structure
        - If user mentions "bootcamp", "intensive" -> create intensive daily structure
        - Otherwise use standard chapter structure
        
        Format your response as:
        TITLE: [Main title for the ebook]
        STRUCTURE_TYPE: [daily|weekly|modular|chapters] based on user requirements
        STRUCTURE_COUNT: [number of days/weeks/modules/chapters to create]
        KEY_CONCEPTS: [List 5 key concepts separated by semicolons]
        TECHNICAL_PROCESSES: [List any technical processes]
        QUANTITATIVE_ASPECTS: [List any calculations or measurements needed]
        APPLICATIONS: [List practical applications]
        """
        
        self.content_generation_prompt = """
        Generate detailed educational content for: {section}
        
        Topic: {topic}
        Context: {context}
        User Requirements: {user_prompt}
        
        Write 2-3 paragraphs of educational content with specific examples where relevant. Use clear, educational language and focus on practical understanding. Adapt content complexity based on user requirements.
        
        For technical processes, include step-by-step explanations.
        For calculations, mention key formulas or relationships.
        
        Provide only the educational content without any introductory phrases like "Here is the content" or "This section covers". Start directly with the educational material.
        """
    
    async def generate_ebook(self, summary: str, user_prompt: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # Step 1: Analyze the summary to extract structured information
        analysis_prompt = self.analysis_prompt.format(summary=summary, user_prompt=user_prompt or "Create a comprehensive educational resource")
        analysis_result = await self.llm_client.generate_completion(analysis_prompt, max_tokens=1000, request_type="content_analysis", model="gpt-3.5-turbo")
        
        # Parse the analysis result
        title, structure_type, structure_count, key_concepts = self._parse_analysis(analysis_result)
        
        # Step 2: Generate custom structure based on analysis
        chapters = self._generate_custom_structure(structure_type, structure_count, title)
        
        # Step 3: Generate content for each subsection
        content_data = {}
        for chapter in chapters:
            if 'subsections' in chapter:
                chapter['subsection_content'] = {}
                for subsection in chapter['subsections']:
                    content_prompt = self.content_generation_prompt.format(
                        topic=title,
                        section=f"{chapter['title']} - {subsection}",
                        context=summary[:1500],
                        user_prompt=user_prompt or "Create comprehensive educational content"
                    )
                    
                    # Increase token limit for more comprehensive content, especially for daily/modular content
                    token_limit = 1500 if structure_type in ["daily", "weekly", "modular"] else 800
                    subsection_content = await self.llm_client.generate_completion(content_prompt, max_tokens=token_limit, request_type=f"content_generation_{subsection.lower().replace(' ', '_')}")
                    chapter['subsection_content'][subsection] = subsection_content
        
        # Step 4: Generate the final markdown using the template
        ebook_content = self.template_generator.generate_template(title, chapters, content_data)
        
        processing_time = time.time() - start_time
        
        return {
            'content': ebook_content,
            'processing_time': processing_time,
            'agent_type': 'generator',
            'title': title,
            'key_concepts': key_concepts
        }
    
    def _parse_analysis(self, analysis_text: str) -> tuple:
        """Parse the analysis result to extract title, structure info, and key concepts"""
        title = "Educational Content"
        structure_type = "chapters"
        structure_count = 5
        key_concepts = []
        
        lines = analysis_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('STRUCTURE_TYPE:'):
                structure_type = line.replace('STRUCTURE_TYPE:', '').strip()
            elif line.startswith('STRUCTURE_COUNT:'):
                try:
                    count_text = line.replace('STRUCTURE_COUNT:', '').strip()
                    structure_count = int(''.join(filter(str.isdigit, count_text))) or 5
                except:
                    structure_count = 5
            elif line.startswith('KEY_CONCEPTS:'):
                concepts_text = line.replace('KEY_CONCEPTS:', '').strip()
                key_concepts = [concept.strip() for concept in concepts_text.split(';') if concept.strip()]
        
        return title, structure_type, structure_count, key_concepts
    
    def _generate_custom_structure(self, structure_type: str, structure_count: int, title: str) -> list:
        """Generate custom chapter structure based on analysis"""
        chapters = []
        
        if structure_type == "daily":
            for day in range(1, min(structure_count + 1, 11)):  # Cap at 10 days to prevent excessive content
                chapters.append({
                    "title": f"Day {day}",
                    "description": f"Learning objectives and materials for Day {day}",
                    "subsections": [
                        "Learning Objectives",
                        "Lecture Materials", 
                        "Practice Materials",
                        "Assessment"
                    ]
                })
        elif structure_type == "weekly":
            for week in range(1, min(structure_count + 1, 9)):  # Cap at 8 weeks
                chapters.append({
                    "title": f"Week {week}",
                    "description": f"Week {week} curriculum and activities",
                    "subsections": [
                        "Weekly Overview",
                        "Key Topics",
                        "Activities and Exercises",
                        "Week Assessment"
                    ]
                })
        elif structure_type == "modular":
            for module in range(1, min(structure_count + 1, 9)):  # Cap at 8 modules
                chapters.append({
                    "title": f"Module {module}",
                    "description": f"Module {module} learning content",
                    "subsections": [
                        "Module Overview",
                        "Core Content",
                        "Practical Applications",
                        "Module Assessment"
                    ]
                })
        else:  # Default to chapters
            return self.template_generator.get_default_structure()
        
        return chapters

class AccuracyReviewAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_template = """
        Review this educational content for accuracy against the original source. Compare key facts and concepts, check for misrepresentations or errors, verify technical details and terminology, and rate overall accuracy on a scale of 0-100.
        
        Original Source: {original}
        Generated Content: {generated}
        
        Provide only:
        1. Accuracy Score (0-100)
        2. List of any factual errors found
        3. Suggested corrections
        4. Overall assessment
        
        Do not include introductory text. Start directly with the accuracy score.
        """
    
    async def review(self, original: str, generated: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(
            original=original[:2000], 
            generated=generated[:2000]
        )
        review_result = await self.llm_client.generate_completion(prompt, request_type="accuracy_review", model="gpt-3.5-turbo")
        
        # Extract accuracy score (simplified parsing)
        try:
            lines = review_result.split('\n')
            score_line = [line for line in lines if 'accuracy score' in line.lower() or 'score:' in line.lower()]
            if score_line:
                score_text = score_line[0]
                score = float([word for word in score_text.split() if word.replace('.', '').isdigit()][0])
            else:
                score = 75.0  # Default score
        except:
            score = 75.0
        
        processing_time = time.time() - start_time
        
        return {
            'score': score,
            'corrections': review_result,
            'processing_time': processing_time,
            'agent_type': 'reviewer'
        }

class ResearchEnhancementAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_template = """
        Enhance this educational content with additional valuable resources. Add related concepts and background information, include real-world applications and examples, suggest case studies relevant to the topic, add references to further reading, and include current industry trends if applicable.
        
        Content: {content}
        
        Enhance the content by:
        1. Adding relevant background context
        2. Including practical applications
        3. Suggesting additional resources
        4. Adding current examples or case studies
        
        Provide only the enhanced content without any introductory phrases. Start directly with the enhanced material.
        """
    
    async def enhance(self, content: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(content=content[:2000])
        enhanced_content = await self.llm_client.generate_completion(prompt, max_tokens=2500, request_type="content_enhancement", model="gpt-3.5-turbo")
        
        processing_time = time.time() - start_time
        
        return {
            'enhanced_content': enhanced_content,
            'processing_time': processing_time,
            'agent_type': 'enhancer'
        }

class RevisionAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_template = """
        Revise this educational content based on the provided feedback. Apply the requested changes carefully, maintain content consistency and flow, preserve educational value and accuracy, and keep the same overall structure unless requested otherwise.
        
        Original Content: {content}
        User Feedback: {feedback}
        
        Provide only the revised content that addresses the feedback while maintaining quality. Do not include any introductory phrases. Start directly with the revised material.
        """
    
    async def revise(self, content: str, feedback: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(content=content[:2000], feedback=feedback)
        revised_content = await self.llm_client.generate_completion(prompt, max_tokens=2500, request_type="content_revision", model="gpt-3.5-turbo")
        
        processing_time = time.time() - start_time
        
        return {
            'revised_content': revised_content,
            'processing_time': processing_time,
            'agent_type': 'revisor'
        }

class ContentPipeline:
    def __init__(self):
        self.llm_client = LLMClient()
        self.summarizer = SummarizationAgent(self.llm_client)
        self.generator = ContentGenerationAgent(self.llm_client)
        self.reviewer = AccuracyReviewAgent(self.llm_client)
        self.enhancer = ResearchEnhancementAgent(self.llm_client)
        self.revisor = RevisionAgent(self.llm_client)
        self.db_manager = DatabaseManager()
    
    async def process_document(self, document: str, user_prompt: str, enhance: bool = False, session_id: str = None) -> Dict[str, Any]:
        start_time = time.time()
        results = {}
        
        # Set up session for event notifications
        if session_id:
            self.llm_client.current_session_id = session_id
        
        # Step 1: Summarize
        if session_id:
            await event_notifier.notify_agent_started(session_id, "summarizer")
        
        summary_result = await self.summarizer.process(document, user_prompt)
        results['summary'] = summary_result['summary']
        
        if session_id:
            await event_notifier.notify_agent_completed(session_id, "summarizer", summary_result['processing_time'], "generator")
        
        if session_id:
            await self.db_manager.log_agent_activity(
                session_id, 'summarizer', document[:500], 
                summary_result['summary'][:500], summary_result['processing_time']
            )
            # Save agent log locally
            content_saver.save_agent_log(
                session_id, 'summarizer', document[:1000],
                summary_result['summary'], summary_result['processing_time']
            )
        
        # Step 2: Generate ebook  
        if session_id:
            await event_notifier.notify_agent_started(session_id, "generator")
        
        ebook_result = await self.generator.generate_ebook(summary_result['summary'], user_prompt)
        results['content'] = ebook_result['content']
        
        if session_id:
            await event_notifier.notify_agent_completed(session_id, "generator", ebook_result['processing_time'], "reviewer")
        
        if session_id:
            await self.db_manager.log_agent_activity(
                session_id, 'generator', summary_result['summary'][:500],
                ebook_result['content'][:500], ebook_result['processing_time']
            )
            # Save agent log locally
            content_saver.save_agent_log(
                session_id, 'generator', summary_result['summary'][:1000],
                ebook_result['content'][:2000], ebook_result['processing_time']
            )
            # Save the final ebook content locally
            saved_file = content_saver.save_content(
                session_id, ebook_result['content'], user_prompt,
                content_type="ebook", metadata={
                    'title': ebook_result.get('title', 'Generated Content'),
                    'key_concepts': ebook_result.get('key_concepts', []),
                    'processing_time': ebook_result['processing_time']
                }
            )
            
            # Notify content saved
            await event_notifier.notify_content_saved(
                session_id, "ebook", len(ebook_result['content']), saved_file
            )
        
        # Step 3: Review for accuracy
        accuracy_result = await self.reviewer.review(document, ebook_result['content'])
        results['accuracy_score'] = accuracy_result['score']
        
        if session_id:
            await self.db_manager.log_agent_activity(
                session_id, 'reviewer', f"Score: {accuracy_result['score']}",
                accuracy_result['corrections'][:500], accuracy_result['processing_time']
            )
        
        # Step 4: Apply corrections if needed
        if accuracy_result['score'] < 85:
            revision_result = await self.revisor.revise(
                ebook_result['content'], 
                accuracy_result['corrections']
            )
            results['content'] = revision_result['revised_content']
            
            if session_id:
                await self.db_manager.log_agent_activity(
                    session_id, 'revisor', accuracy_result['corrections'][:500],
                    revision_result['revised_content'][:500], revision_result['processing_time']
                )
        
        # Step 5: Enhance if requested
        if enhance:
            enhancement_result = await self.enhancer.enhance(results['content'])
            results['content'] = enhancement_result['enhanced_content']
            
            if session_id:
                await self.db_manager.log_agent_activity(
                    session_id, 'enhancer', results['content'][:500],
                    enhancement_result['enhanced_content'][:500], enhancement_result['processing_time']
                )
        
        # Notify processing complete
        if session_id:
            total_time = time.time() - start_time
            await event_notifier.notify_processing_complete(
                session_id, results['accuracy_score'], total_time, "content_generated"
            )
        
        return results