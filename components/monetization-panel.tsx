"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  CreditCard,
  Wallet,
  Star,
  Download,
  ExternalLink,
  Check,
  Zap,
  Gift,
  TrendingUp,
  Shield,
  Sparkles,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface MonetizationPanelProps {
  reportData: any
  onPayment?: (paymentType: string) => void
  onNFTMint?: (walletAddress: string) => void
}

export default function MonetizationPanel({ reportData, onPayment, onNFTMint }: MonetizationPanelProps) {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const [walletAddress, setWalletAddress] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [paymentSuccess, setPaymentSuccess] = useState(false)
  const [nftMinted, setNftMinted] = useState(false)

  const pricingPlans = [
    {
      id: 'basic',
      name: 'Basic Report',
      price: 0.99,
      description: 'Download your research report',
      features: [
        'PDF Export',
        'Citation List',
        'Basic Analytics',
        'Email Support'
      ],
      icon: <Download className="h-5 w-5" />,
      color: 'bg-blue-500'
    },
    {
      id: 'premium',
      name: 'Premium Report',
      price: 4.99,
      description: 'Enhanced report with audio narration',
      features: [
        'Everything in Basic',
        'Audio Narration',
        'Interactive Charts',
        'Priority Support',
        'Advanced Analytics'
      ],
      icon: <Star className="h-5 w-5" />,
      color: 'bg-purple-500',
      popular: true
    },
    {
      id: 'nft',
      name: 'NFT Collection',
      price: 9.99,
      description: 'Mint your report as a unique NFT',
      features: [
        'Everything in Premium',
        'Solana NFT Mint',
        'Unique Metadata',
        'OpenSea Listing',
        'Ownership Certificate',
        'Resale Rights'
      ],
      icon: <Sparkles className="h-5 w-5" />,
      color: 'bg-gradient-to-r from-yellow-500 to-orange-500'
    }
  ]

  const handlePayment = async (planId: string) => {
    setIsProcessing(true)
    setSelectedPlan(planId)

    try {
      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      setPaymentSuccess(true)
      onPayment?.(planId)
      
      // If NFT plan, proceed to minting
      if (planId === 'nft' && walletAddress) {
        await handleNFTMint()
      }
    } catch (error) {
      console.error('Payment failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleNFTMint = async () => {
    if (!walletAddress) return

    try {
      setIsProcessing(true)
      
      // Simulate NFT minting
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      setNftMinted(true)
      onNFTMint?.(walletAddress)
    } catch (error) {
      console.error('NFT minting failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const calculateRarityScore = () => {
    const papers = reportData?.summaries?.length || 0
    const themes = reportData?.themes?.length || 0
    const gaps = reportData?.gaps?.length || 0
    
    const score = papers + themes * 2 + gaps * 3
    
    if (score >= 50) return { level: 'Legendary', color: 'text-yellow-500' }
    if (score >= 30) return { level: 'Epic', color: 'text-purple-500' }
    if (score >= 20) return { level: 'Rare', color: 'text-blue-500' }
    if (score >= 10) return { level: 'Uncommon', color: 'text-green-500' }
    return { level: 'Common', color: 'text-gray-500' }
  }

  const rarity = calculateRarityScore()

  return (
    <div className="space-y-6">
      {/* Success Messages */}
      <AnimatePresence>
        {paymentSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-green-50 border border-green-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-3">
              <Check className="h-5 w-5 text-green-500" />
              <div>
                <h3 className="font-medium text-green-800">Payment Successful!</h3>
                <p className="text-sm text-green-600">Your report access has been activated.</p>
              </div>
            </div>
          </motion.div>
        )}

        {nftMinted && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-purple-50 border border-purple-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-purple-500" />
              <div>
                <h3 className="font-medium text-purple-800">NFT Minted Successfully!</h3>
                <p className="text-sm text-purple-600">Your research report is now a unique NFT.</p>
                <Button variant="outline" size="sm" className="mt-2 bg-transparent">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View on OpenSea
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Tabs defaultValue="pricing" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="pricing">Pricing</TabsTrigger>
          <TabsTrigger value="nft">NFT Details</TabsTrigger>
          <TabsTrigger value="wallet">Wallet</TabsTrigger>
        </TabsList>

        <TabsContent value="pricing">
          <div className="grid gap-4">
            {pricingPlans.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className={`relative overflow-hidden ${plan.popular ? 'ring-2 ring-purple-500' : ''}`}>
                  {plan.popular && (
                    <div className="absolute top-0 right-0 bg-purple-500 text-white px-3 py-1 text-xs font-medium">
                      Most Popular
                    </div>
                  )}
                  
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg text-white ${plan.color}`}>
                          {plan.icon}
                        </div>
                        <div>
                          <CardTitle className="text-lg">{plan.name}</CardTitle>
                          <CardDescription>{plan.description}</CardDescription>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">${plan.price}</div>
                        <div className="text-sm text-gray-500">USD</div>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      {plan.features.map((feature, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-500" />
                          <span className="text-sm">{feature}</span>
                        </div>
                      ))}
                    </div>

                    {plan.id === 'nft' && (
                      <div className="space-y-3 pt-3 border-t">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Rarity Level:</span>
                          <Badge className={`${rarity.color} bg-transparent border`}>
                            {rarity.level}
                          </Badge>
                        </div>
                        <Input
                          placeholder="Enter Solana wallet address"
                          value={walletAddress}
                          onChange={(e) => setWalletAddress(e.target.value)}
                          className="text-sm"
                        />
                      </div>
                    )}

                    <Button
                      className="w-full"
                      onClick={() => handlePayment(plan.id)}
                      disabled={isProcessing || (plan.id === 'nft' && !walletAddress)}
                    >
                      {isProcessing && selectedPlan === plan.id ? (
                        <div className="flex items-center gap-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                          Processing...
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <CreditCard className="h-4 w-4" />
                          {plan.id === 'nft' ? 'Mint NFT' : 'Purchase'}
                        </div>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="nft">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                NFT Collection Details
              </CardTitle>
              <CardDescription>
                Transform your research report into a unique digital collectible
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* NFT Preview */}
              <div className="bg-gradient-to-br from-purple-100 to-blue-100 rounded-lg p-6">
                <div className="text-center space-y-4">
                  <div className="w-24 h-24 mx-auto bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                    <Sparkles className="h-12 w-12 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold">AI Research Report NFT</h3>
                    <p className="text-sm text-gray-600">Unique digital certificate of your research</p>
                  </div>
                </div>
              </div>

              {/* NFT Attributes */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h4 className="font-medium">Attributes</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Papers Analyzed:</span>
                      <span className="font-medium">{reportData?.summaries?.length || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Key Themes:</span>
                      <span className="font-medium">{reportData?.themes?.length || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Research Gaps:</span>
                      <span className="font-medium">{reportData?.gaps?.length || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Rarity:</span>
                      <Badge className={`${rarity.color} bg-transparent border`}>
                        {rarity.level}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium">Blockchain Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Blockchain:</span>
                      <span className="font-medium">Solana</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Standard:</span>
                      <span className="font-medium">Metaplex</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Compressed:</span>
                      <span className="font-medium">Yes</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Royalties:</span>
                      <span className="font-medium">5%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Benefits */}
              <div className="space-y-3">
                <h4 className="font-medium">NFT Benefits</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Shield className="h-4 w-4 text-green-500" />
                    <span>Ownership Certificate</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <TrendingUp className="h-4 w-4 text-blue-500" />
                    <span>Resale Rights</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Zap className="h-4 w-4 text-purple-500" />
                    <span>Exclusive Access</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Gift className="h-4 w-4 text-orange-500" />
                    <span>Future Airdrops</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="wallet">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="h-5 w-5 text-blue-500" />
                Wallet Connection
              </CardTitle>
              <CardDescription>
                Connect your wallet to purchase and mint NFTs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {
