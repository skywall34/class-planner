import time
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import os
from database import DatabaseManager

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))
    
    async def generate_completion(self, prompt: str, max_tokens: int = 2000) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating content: {str(e)}"

class SummarizationAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_template = """
        Summarize the following research paper for educational purposes:
        - Extract main concepts and key findings
        - Identify learning objectives for students
        - Create chapter outlines suitable for {duration} learning
        - Preserve technical accuracy and important details
        - Structure content in a logical learning progression
        
        Text: {text}
        Duration: {duration}
        
        Please provide a structured summary with:
        1. Main Learning Objectives
        2. Key Concepts
        3. Chapter Outline
        4. Important Findings
        """
    
    async def process(self, text: str, duration: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(text=text[:4000], duration=duration)
        summary = await self.llm_client.generate_completion(prompt)
        
        processing_time = time.time() - start_time
        
        return {
            'summary': summary,
            'processing_time': processing_time,
            'agent_type': 'summarizer'
        }

class ContentGenerationAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_template = """
        Create comprehensive educational ebook content from this summary:
        - Include clear learning objectives for each chapter
        - Add practical examples and case studies
        - Structure content for {duration} learning timeline
        - Format in clean markdown with proper headings
        - Include exercises and review questions
        - Make content engaging and accessible
        
        Summary: {summary}
        Duration: {duration}
        
        Please create a complete ebook with:
        # Title
        ## Chapter 1: Introduction
        ## Chapter 2: Core Concepts
        ## Chapter 3: Advanced Topics
        ## Chapter 4: Applications
        ## Chapter 5: Conclusion and Next Steps
        
        Each chapter should include learning objectives, content, examples, and exercises.
        """
    
    async def generate_ebook(self, summary: str, duration: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(summary=summary, duration=duration)
        ebook_content = await self.llm_client.generate_completion(prompt, max_tokens=3000)
        
        processing_time = time.time() - start_time
        
        return {
            'content': ebook_content,
            'processing_time': processing_time,
            'agent_type': 'generator'
        }

class AccuracyReviewAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_template = """
        Review the generated educational content for accuracy against the original source:
        - Compare key facts and concepts
        - Check for any misrepresentations or errors
        - Verify technical details and terminology
        - Rate overall accuracy on a scale of 0-100
        - Suggest specific corrections if needed
        
        Original Source: {original}
        Generated Content: {generated}
        
        Please provide:
        1. Accuracy Score (0-100)
        2. List of any factual errors found
        3. Suggested corrections
        4. Overall assessment
        """
    
    async def review(self, original: str, generated: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(
            original=original[:2000], 
            generated=generated[:2000]
        )
        review_result = await self.llm_client.generate_completion(prompt)
        
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
        Enhance the educational content with additional valuable resources:
        - Add related concepts and background information
        - Include real-world applications and examples
        - Suggest case studies relevant to the topic
        - Add references to further reading
        - Include current industry trends if applicable
        
        Content: {content}
        
        Please enhance the content by:
        1. Adding relevant background context
        2. Including practical applications
        3. Suggesting additional resources
        4. Adding current examples or case studies
        """
    
    async def enhance(self, content: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(content=content[:2000])
        enhanced_content = await self.llm_client.generate_completion(prompt, max_tokens=2500)
        
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
        Revise the educational content based on the provided feedback:
        - Apply the requested changes carefully
        - Maintain content consistency and flow
        - Preserve educational value and accuracy
        - Keep the same overall structure unless requested otherwise
        
        Original Content: {content}
        User Feedback: {feedback}
        
        Please provide the revised content that addresses the feedback while maintaining quality.
        """
    
    async def revise(self, content: str, feedback: str) -> Dict[str, Any]:
        start_time = time.time()
        
        prompt = self.prompt_template.format(content=content[:2000], feedback=feedback)
        revised_content = await self.llm_client.generate_completion(prompt, max_tokens=2500)
        
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
    
    async def process_document(self, document: str, duration: str, enhance: bool = False, session_id: str = None) -> Dict[str, Any]:
        results = {}
        
        # Step 1: Summarize
        summary_result = await self.summarizer.process(document, duration)
        results['summary'] = summary_result['summary']
        
        if session_id:
            await self.db_manager.log_agent_activity(
                session_id, 'summarizer', document[:500], 
                summary_result['summary'][:500], summary_result['processing_time']
            )
        
        # Step 2: Generate ebook
        ebook_result = await self.generator.generate_ebook(summary_result['summary'], duration)
        results['content'] = ebook_result['content']
        
        if session_id:
            await self.db_manager.log_agent_activity(
                session_id, 'generator', summary_result['summary'][:500],
                ebook_result['content'][:500], ebook_result['processing_time']
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
        
        return results