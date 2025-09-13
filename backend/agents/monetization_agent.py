import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp
import json
import uuid
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class MonetizationAgent:
    """
    Crossmint integration agent for payments and NFT minting
    Handles Stripe payments and Solana NFT creation for research reports
    """
    
    def __init__(self, crossmint_api_key: str, stripe_api_key: str = None):
        self.crossmint_api_key = crossmint_api_key
        self.stripe_api_key = stripe_api_key
        self.crossmint_base_url = "https://www.crossmint.com/api/2022-06-09"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Pricing configuration
        self.pricing = {
            'basic_report': 0.99,
            'premium_report': 4.99,
            'nft_mint': 9.99,
            'bulk_analysis': 19.99
        }
        
        # NFT collection configuration
        self.nft_collection = {
            'collection_id': 'research-reports-collection',
            'blockchain': 'solana',
            'name': 'AI Research Reports',
            'description': 'Unique AI-generated research synthesis reports'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def process_payment(self, payment_type: str, user_id: str = None, 
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process payment via Crossmint/Stripe integration
        """
        logger.info(f"Processing payment for type: {payment_type}")
        
        try:
            amount = self.pricing.get(payment_type, 0.99)
            
            # Create payment intent
            payment_intent = await self._create_payment_intent(
                amount, payment_type, user_id, metadata
            )
            
            if payment_intent['success']:
                # Process payment (mock implementation)
                payment_result = await self._process_stripe_payment(payment_intent)
                
                return {
                    'success': True,
                    'payment_id': payment_result['payment_id'],
                    'amount': amount,
                    'currency': 'USD',
                    'status': 'completed',
                    'transaction_hash': payment_result.get('transaction_hash'),
                    'receipt_url': payment_result.get('receipt_url'),
                    'metadata': {
                        'payment_type': payment_type,
                        'processed_at': datetime.now().isoformat(),
                        'user_id': user_id
                    }
                }
            else:
                return {
                    'success': False,
                    'error': payment_intent['error'],
                    'payment_type': payment_type
                }
                
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'payment_type': payment_type
            }
    
    async def mint_research_nft(self, report_data: Dict[str, Any], 
                               user_wallet: str = None, 
                               payment_id: str = None) -> Dict[str, Any]:
        """
        Mint research report as NFT on Solana via Crossmint
        """
        logger.info("Minting research report as NFT")
        
        try:
            # Generate unique NFT metadata
            nft_metadata = await self._generate_nft_metadata(report_data)
            
            # Create NFT via Crossmint API
            mint_result = await self._mint_nft_via_crossmint(
                nft_metadata, user_wallet, payment_id
            )
            
            if mint_result['success']:
                return {
                    'success': True,
                    'nft_id': mint_result['nft_id'],
                    'mint_address': mint_result['mint_address'],
                    'blockchain': 'solana',
                    'transaction_hash': mint_result['transaction_hash'],
                    'opensea_url': mint_result.get('opensea_url'),
                    'metadata': nft_metadata,
                    'minted_at': datetime.now().isoformat(),
                    'owner_wallet': user_wallet
                }
            else:
                return {
                    'success': False,
                    'error': mint_result['error']
                }
                
        except Exception as e:
            logger.error(f"NFT minting failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _create_payment_intent(self, amount: float, payment_type: str, 
                                   user_id: str = None, 
                                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create payment intent with Stripe"""
        try:
            # Mock payment intent creation
            payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"
            
            return {
                'success': True,
                'payment_intent_id': payment_intent_id,
                'amount': amount,
                'currency': 'usd',
                'client_secret': f"{payment_intent_id}_secret_{uuid.uuid4().hex[:16]}",
                'status': 'requires_payment_method'
            }
            
        except Exception as e:
            logger.error(f"Payment intent creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _process_stripe_payment(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment via Stripe (mock implementation)"""
        # Mock successful payment processing
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            'payment_id': f"pay_{uuid.uuid4().hex[:24]}",
            'transaction_hash': f"0x{uuid.uuid4().hex}",
            'receipt_url': f"https://dashboard.stripe.com/payments/{uuid.uuid4().hex}",
            'status': 'succeeded'
        }
    
    async def _generate_nft_metadata(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate NFT metadata from research report"""
        
        # Extract key information
        query = report_data.get('query', 'Research Analysis')
        papers_count = len(report_data.get('summaries', []))
        themes_count = len(report_data.get('themes', []))
        gaps_count = len(report_data.get('gaps', []))
        
        # Generate uniqueness hash
        content_hash = hashlib.sha256(
            json.dumps(report_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # Create NFT metadata following OpenSea standards
        metadata = {
            'name': f'AI Research Report: {query}',
            'description': f'Comprehensive AI-generated research synthesis analyzing {papers_count} papers, identifying {themes_count} key themes and {gaps_count} research gaps.',
            'image': await self._generate_nft_image_url(report_data),
            'external_url': f'https://research-assistant.app/report/{content_hash}',
            'attributes': [
                {
                    'trait_type': 'Research Topic',
                    'value': query
                },
                {
                    'trait_type': 'Papers Analyzed',
                    'value': papers_count
                },
                {
                    'trait_type': 'Key Themes',
                    'value': themes_count
                },
                {
                    'trait_type': 'Research Gaps',
                    'value': gaps_count
                },
                {
                    'trait_type': 'Generation Date',
                    'value': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'trait_type': 'Uniqueness Hash',
                    'value': content_hash
                },
                {
                    'trait_type': 'AI Generated',
                    'value': 'True'
                }
            ],
            'properties': {
                'category': 'Research Report',
                'subcategory': 'AI Generated',
                'rarity': self._calculate_rarity_score(report_data),
                'version': '1.0'
            }
        }
        
        return metadata
    
    async def _generate_nft_image_url(self, report_data: Dict[str, Any]) -> str:
        """Generate or retrieve NFT image URL"""
        # In production, generate dynamic image based on report content
        # For now, return a placeholder
        query_hash = hashlib.md5(
            report_data.get('query', 'research').encode()
        ).hexdigest()[:8]
        
        return f"https://api.research-assistant.app/nft-images/{query_hash}.png"
    
    def _calculate_rarity_score(self, report_data: Dict[str, Any]) -> str:
        """Calculate NFT rarity based on report characteristics"""
        papers_count = len(report_data.get('summaries', []))
        themes_count = len(report_data.get('themes', []))
        gaps_count = len(report_data.get('gaps', []))
        
        # Simple rarity calculation
        total_score = papers_count + themes_count * 2 + gaps_count * 3
        
        if total_score >= 50:
            return 'Legendary'
        elif total_score >= 30:
            return 'Epic'
        elif total_score >= 20:
            return 'Rare'
        elif total_score >= 10:
            return 'Uncommon'
        else:
            return 'Common'
    
    async def _mint_nft_via_crossmint(self, metadata: Dict[str, Any], 
                                    user_wallet: str = None, 
                                    payment_id: str = None) -> Dict[str, Any]:
        """Mint NFT via Crossmint API"""
        try:
            headers = {
                'X-API-KEY': self.crossmint_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'metadata': metadata,
                'recipient': user_wallet or 'crossmint:default',
                'compressed': True,  # Use compressed NFTs for lower cost
                'collection': self.nft_collection['collection_id']
            }
            
            # Mock API call (replace with actual Crossmint API)
            await asyncio.sleep(2)  # Simulate minting time
            
            # Mock successful response
            mint_address = f"mint_{uuid.uuid4().hex[:32]}"
            transaction_hash = f"tx_{uuid.uuid4().hex}"
            
            return {
                'success': True,
                'nft_id': mint_address,
                'mint_address': mint_address,
                'transaction_hash': transaction_hash,
                'opensea_url': f"https://opensea.io/assets/solana/{mint_address}",
                'explorer_url': f"https://explorer.solana.com/tx/{transaction_hash}"
            }
            
        except Exception as e:
            logger.error(f"Crossmint NFT minting failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_pricing_info(self) -> Dict[str, Any]:
        """Get current pricing information"""
        return {
            'pricing': self.pricing,
            'currency': 'USD',
            'payment_methods': ['card', 'crypto'],
            'supported_blockchains': ['solana', 'ethereum', 'polygon'],
            'nft_collection': self.nft_collection
        }
    
    async def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify payment status"""
        try:
            # Mock payment verification
            await asyncio.sleep(0.5)
            
            return {
                'success': True,
                'payment_id': payment_id,
                'status': 'completed',
                'verified_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_user_nfts(self, user_wallet: str) -> Dict[str, Any]:
        """Get user's minted NFTs"""
        try:
            # Mock user NFT retrieval
            mock_nfts = [
                {
                    'nft_id': f"nft_{uuid.uuid4().hex[:16]}",
                    'name': 'AI Research Report: Quantum Computing Ethics',
                    'mint_address': f"mint_{uuid.uuid4().hex[:32]}",
                    'minted_at': (datetime.now() - timedelta(days=5)).isoformat(),
                    'opensea_url': f"https://opensea.io/assets/solana/mock_address"
                }
            ]
            
            return {
                'success': True,
                'nfts': mock_nfts,
                'total_count': len(mock_nfts),
                'user_wallet': user_wallet
            }
            
        except Exception as e:
            logger.error(f"Failed to get user NFTs: {e}")
            return {
                'success': False,
                'error': str(e)
            }
