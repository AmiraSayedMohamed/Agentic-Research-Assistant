import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CoralOrchestrator:
    """
    Coral Protocol orchestrator for zero-trust agent communication
    Manages the complete research workflow with error handling and recovery
    """
    
    def __init__(self, nebius_api_key: str):
        self.nebius_api_key = nebius_api_key
        self.agents = {}
        self.workflow_state = {}
        
    async def initialize_agents(self):
        """Initialize all agents with proper async context"""
        from .search_agent import SearchAgent
        from .summary_agent import SummaryAgent
        from .synthesizer_agent import SynthesizerAgent
        
        # Initialize agents with async context managers
        self.agents = {
            'search': SearchAgent(),
            'summary': SummaryAgent(self.nebius_api_key),
            'synthesizer': SynthesizerAgent(self.nebius_api_key)
        }
        
        logger.info("Coral orchestrator initialized with all agents")
    
    async def execute_research_workflow(self, query: str, max_papers: int = 10, 
                                      job_id: str = None) -> Dict[str, Any]:
        """
        Execute the complete research workflow through Coral Protocol
        
        Workflow: Search → Summary → Synthesis → Voice → Monetization
        """
        workflow_id = job_id or f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.workflow_state[workflow_id] = {
            'status': 'started',
            'steps': {
                'search': {'status': 'pending', 'start_time': None, 'end_time': None, 'result': None},
                'summary': {'status': 'pending', 'start_time': None, 'end_time': None, 'result': None},
                'synthesis': {'status': 'pending', 'start_time': None, 'end_time': None, 'result': None},
                'voice': {'status': 'pending', 'start_time': None, 'end_time': None, 'result': None},
                'monetization': {'status': 'pending', 'start_time': None, 'end_time': None, 'result': None}
            },
            'query': query,
            'max_papers': max_papers,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        try:
            # Step 1: Search and Retrieval
            await self._execute_step(workflow_id, 'search', self._search_step, query, max_papers)
            
            # Step 2: Summarization
            search_result = self.workflow_state[workflow_id]['steps']['search']['result']
            await self._execute_step(workflow_id, 'summary', self._summary_step, search_result, query)
            
            # Step 3: Synthesis
            summary_result = self.workflow_state[workflow_id]['steps']['summary']['result']
            await self._execute_step(workflow_id, 'synthesis', self._synthesis_step, summary_result, query)
            
            # Step 4: Voice Generation (placeholder for now)
            synthesis_result = self.workflow_state[workflow_id]['steps']['synthesis']['result']
            await self._execute_step(workflow_id, 'voice', self._voice_step, synthesis_result)
            
            # Step 5: Monetization (placeholder for now)
            await self._execute_step(workflow_id, 'monetization', self._monetization_step, workflow_id)
            
            # Mark workflow as completed
            self.workflow_state[workflow_id]['status'] = 'completed'
            self.workflow_state[workflow_id]['updated_at'] = datetime.now()
            
            return self._compile_final_results(workflow_id)
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            self.workflow_state[workflow_id]['status'] = 'error'
            self.workflow_state[workflow_id]['error'] = str(e)
            self.workflow_state[workflow_id]['updated_at'] = datetime.now()
            raise
    
    async def _execute_step(self, workflow_id: str, step_name: str, step_function, *args):
        """Execute a single workflow step with error handling and state tracking"""
        step_state = self.workflow_state[workflow_id]['steps'][step_name]
        
        try:
            step_state['status'] = 'in-progress'
            step_state['start_time'] = datetime.now()
            self.workflow_state[workflow_id]['updated_at'] = datetime.now()
            
            logger.info(f"Starting step {step_name} for workflow {workflow_id}")
            
            # Execute the step function
            result = await step_function(*args)
            
            step_state['status'] = 'completed'
            step_state['end_time'] = datetime.now()
            step_state['result'] = result
            self.workflow_state[workflow_id]['updated_at'] = datetime.now()
            
            logger.info(f"Completed step {step_name} for workflow {workflow_id}")
            
        except Exception as e:
            step_state['status'] = 'error'
            step_state['end_time'] = datetime.now()
            step_state['error'] = str(e)
            self.workflow_state[workflow_id]['updated_at'] = datetime.now()
            
            logger.error(f"Step {step_name} failed for workflow {workflow_id}: {e}")
            raise
    
    async def _search_step(self, query: str, max_papers: int) -> List[Dict[str, Any]]:
        """Execute search agent step"""
        async with self.agents['search'] as search_agent:
            papers = await search_agent.search_papers(query, max_papers)
            
        logger.info(f"Search step completed: found {len(papers)} papers")
        return papers
    
    async def _summary_step(self, papers: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Execute summary agent step"""
        async with self.agents['summary'] as summary_agent:
            summaries = await summary_agent.summarize_papers(papers, query)
            
        logger.info(f"Summary step completed: generated {len(summaries)} summaries")
        return summaries
    
    async def _synthesis_step(self, summaries: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Execute synthesizer agent step"""
        async with self.agents['synthesizer'] as synthesizer_agent:
            report = await synthesizer_agent.synthesize_report(summaries, query)
            
        logger.info("Synthesis step completed: generated comprehensive report")
        return report
    
    async def _voice_step(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute voice generation step (placeholder)"""
        # Placeholder for ElevenLabs integration
        await asyncio.sleep(2)  # Simulate processing time
        
        voice_result = {
            'audio_url': 'https://example.com/audio/research_report.mp3',
            'duration': '12:34',
            'voice': 'Adam',
            'status': 'completed',
            'timestamps': [
                {'section': 'Executive Summary', 'start': '0:00', 'end': '2:15'},
                {'section': 'Key Themes', 'start': '2:15', 'end': '7:30'},
                {'section': 'Gaps & Limitations', 'start': '7:30', 'end': '10:45'},
                {'section': 'Recommendations', 'start': '10:45', 'end': '12:34'}
            ]
        }
        
        logger.info("Voice generation step completed")
        return voice_result
    
    async def _monetization_step(self, workflow_id: str) -> Dict[str, Any]:
        """Execute monetization step (placeholder)"""
        # Placeholder for Crossmint integration
        await asyncio.sleep(1)  # Simulate processing time
        
        monetization_result = {
            'payment_processed': False,
            'nft_minted': False,
            'status': 'available',
            'pricing': {
                'basic_report': 0.99,
                'nft_mint': 4.99
            }
        }
        
        logger.info("Monetization step completed")
        return monetization_result
    
    def _compile_final_results(self, workflow_id: str) -> Dict[str, Any]:
        """Compile final results from all workflow steps"""
        workflow = self.workflow_state[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'status': workflow['status'],
            'query': workflow['query'],
            'papers': workflow['steps']['search']['result'],
            'summaries': workflow['steps']['summary']['result'],
            'synthesis': workflow['steps']['synthesis']['result'],
            'voice': workflow['steps']['voice']['result'],
            'monetization': workflow['steps']['monetization']['result'],
            'metadata': {
                'total_papers': len(workflow['steps']['search']['result']),
                'processing_time': self._calculate_processing_time(workflow),
                'created_at': workflow['created_at'].isoformat(),
                'completed_at': workflow['updated_at'].isoformat()
            }
        }
    
    def _calculate_processing_time(self, workflow: Dict[str, Any]) -> str:
        """Calculate total processing time for the workflow"""
        start_time = workflow['created_at']
        end_time = workflow['updated_at']
        duration = end_time - start_time
        
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        
        return f"{minutes}m {seconds}s"
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        if workflow_id not in self.workflow_state:
            return None
        
        workflow = self.workflow_state[workflow_id]
        
        # Calculate progress percentage
        completed_steps = sum(1 for step in workflow['steps'].values() if step['status'] == 'completed')
        total_steps = len(workflow['steps'])
        progress_percentage = (completed_steps / total_steps) * 100
        
        return {
            'workflow_id': workflow_id,
            'status': workflow['status'],
            'progress_percentage': progress_percentage,
            'current_step': self._get_current_step(workflow),
            'steps': {
                name: {
                    'status': step['status'],
                    'start_time': step['start_time'].isoformat() if step['start_time'] else None,
                    'end_time': step['end_time'].isoformat() if step['end_time'] else None,
                    'error': step.get('error')
                }
                for name, step in workflow['steps'].items()
            },
            'created_at': workflow['created_at'].isoformat(),
            'updated_at': workflow['updated_at'].isoformat()
        }
    
    def _get_current_step(self, workflow: Dict[str, Any]) -> str:
        """Determine the current step being processed"""
        for step_name, step_data in workflow['steps'].items():
            if step_data['status'] == 'in-progress':
                return step_name
            elif step_data['status'] == 'pending':
                return step_name
        return 'completed'
    
    async def cleanup_workflow(self, workflow_id: str):
        """Clean up workflow state and resources"""
        if workflow_id in self.workflow_state:
            del self.workflow_state[workflow_id]
            logger.info(f"Cleaned up workflow {workflow_id}")
